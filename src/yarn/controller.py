import re, json, collections

class YarnController(object):
    def __init__(self, path, name, echo=False, init_locals={}, json_content=None):
        """load yarn file from path path.
If echo is True, link text will be added back into the message. For example:
        "You can [[climb the hill|UpperHillside]]" becomes "You can [climb the hill]"
        """
        self.finished=False
        self.name=name
        self.states=dict()
        self.echo=echo
        self.state=None

        if json_content:
            parsed=json_content
        else:
            parsed=json.loads(open(path).read())

        for state in parsed:
            body=state["body"]
            title=state["title"]
            new_state=YarnState(title, body, self)
            self.states[title]=new_state
            new_state.pre_compile()
            for sub_state in new_state.sub_states:
                self.states[sub_state.title]=sub_state

        # passed to eval of user <<statements>>
        self.locals=dict()
        for akey in init_locals:
            self.locals[akey]=init_locals[akey]

        # user can reference these
        self.visited=collections.defaultdict(lambda:False)
        self.visits=collections.defaultdict(lambda:0)

        self.locals["visited"]=self.visited
        self.locals["num_visits"]=self.visits
        self.locals["visited_before"]=False
        self.locals["first_time"]=True
        self.locals["last_state"]=None
        self.locals["link_text"]=""
        self.locals["state"]=None
        self.locals["YarnObj"]=self

        # code in the first state is guaranteed to run!
        self.set_state("Start")

    def eval(self, code):
        return eval(code, {}, self.locals)

    def exec(self, code):
        exec(code, {}, self.locals)

    def __getattr__(self, attr):
        if attr in self.locals:
            return self.locals[attr]
        raise AttributeError("%r object has no attribute %r" %
                             (self.__class__.__name__, attr))

    def set_state(self, title="Start"):
        # set these before expanding the template code
        # so they are available to the user
        self.locals["last_state"]=self.locals["state"]
        self.state=self.states[title]
        self.locals["visited_before"]=self.visited[title]
        self.locals["first_time"]=not self.visited[title]
        self.visited[title]=True
        self.visits[title]+=1
        self.locals["state"]=self.state.title

        self.state.run_parse()
        if len(self.state.choices)==0:
            # could also be set by user
            self.finished=True

    def message(self):
        return self.state.message

    def transition(self, choice):
        if type(choice)==int:
            choice=self.state.choices[choice]
        self.locals["link_text"]=choice
        self.set_state(self.state.transitions[choice])
        return self.message(), self.choices()

    def choices(self):
        return self.state.choices

def code_munge(r, controller):
    line = r[0]
    mod  = r[1]
    args = r[2]
    if mod=="print":
        result = controller.eval(args)
        return str(result)
    if mod=="println":
        result = controller.eval(args)
        return str(result)+"\n"
    if mod=="run":
        result = controller.exec(args)
        return ""
    if mod=="include":
        thestate= controller.states[args]
        return run_macros(thestate.body, controller)
    else:
        return "UNKNOWN MACRO"

def run_macros(code, controller, late_pass=False):
    if late_pass:
        code_rgx = r"<<!(\w+)\b[ ]*(.*?)>>"
    else:
        code_rgx = r"<<(\w+)\b[ ]*(.*?)>>"
    
    result=""
    start_pos=0

    stack=[]
    found_clause=False
    skip_over=False
    for token_match in re.finditer(code_rgx, code):
        if not skip_over:
            result   += code[start_pos:token_match.start()]
        start_pos = token_match.end()

        # don't add a newline for a <<statement>> on its own line
        if (len(result) > 0
            and start_pos < len(code)
            and code[start_pos]=="\n"
            and result[-1]=="\n"):
            start_pos+=1

        # if-then-else aka <<if X>> <<else>> <<endif>> has special logic
        mod  = token_match[1]
        args = token_match[2].strip()
        if mod == "if":
            stack.append((found_clause, skip_over))
            found_clause=False
            if stack[-1][1]:
                skip_over=True
            else:
                found_clause = controller.eval(args)
                skip_over = not found_clause
        elif mod =="else":
            if stack[-1][1]:
                skip_over=True
            elif found_clause:
                skip_over=True
            else:
                skip_over=False
                found_clause=not skip_over
        elif mod =="elif":
            if stack[-1][1]:
                skip_over=True
            elif found_clause:
                skip_over=True
            else:
                found_clause= controller.eval(args)
                skip_over=not found_clause
        elif mod == "endif":
            (found_clause, skip_over)=stack.pop()
        elif mod == "goto":
            if not skip_over:
                controller.set_state(args)
                return
        else:
            # other <<statements>> handled here
            if not skip_over:
                result += code_munge(token_match, controller)

    # don't forget any text after the last statement
    result += code[start_pos:]
    assert(not skip_over)
    assert(len(stack)==0)
    return result

class DummyController(object):
    def eval(self, arg):
        return eval(arg)
    def exec(self, arg):
        return exec(arg)

def get_indent(line):
    line=line.expandtabs()
    indent=0
    for char in line:
        if char.isspace():
            indent+=1
        else:
            return indent
    return -1

def get_indented_block(lines, head):
    head_line=lines[head]
    assert(head+1<len(lines))
    first_line=lines[head+1]
    base_indent=get_indent(head_line)
    block_indent=get_indent(first_line)
    assert(block_indent>base_indent)
    block=[]
    i=head+1
    while i<len(lines):
        line=lines[i]
        indent=get_indent(line)
        if indent>=block_indent:
            block.append(line[block_indent:])
            i+=1
        elif indent==-1:
            block.append("")
            i+=1
        else:
            assert(i>head)
            assert(indent==0)
            break
    return i, block

class YarnState(object):
    def __init__(self, title, body, parent):
        self.title=title
        self.body=body
        self.transitions={}
        self.message=""
        self.choices=[]
        self.controller=parent

    def pre_compile(self):
        self.sub_states=[]
        lines=self.body.split("\n")
        found_choices=False
        compiled=""
        sub_state=None
        i = 0
        while i<len(lines):
            line=lines[i]
            if line.startswith("->"):
                choice_line=lines[i]
                choice_text=choice_line[2:].strip()
                i, block_lines=get_indented_block(lines, i)

                sub_state_code="\n".join(block_lines)
                sub_state_name=self.title+"$sub"+str(i)

                sub_state=YarnState(sub_state_name,
                                  sub_state_code,
                                  self.controller)
                compiled+=f"[[{choice_text}|{sub_state_name}]]\n"
                self.sub_states.append(sub_state)
                sub_state.pre_compile()

                for sub_sub_state in sub_state.sub_states:
                    self.sub_states.append(sub_sub_state)
            else:
                compiled+=line+"\n"
                i+=1

        while len(compiled) > 1 and compiled [-1]=="\n":
            compiled=compiled[:-1]

        self.body=compiled

    def run_parse(self):
        self.transitions={}
        self.message=""
        self.choices=[]

        #two passes expand the template first
        expanded = run_macros(self.body, self.controller)
        if self.controller.state!=self:
            #GOTO detected
            return

        # that means in the second pass we might find a [[link|link]] created
        # by the code inserted by a <<print "[[link|link]]">>
        # This link might be invisible to the yarn editor
        # but <<statements>> generated by code are not expanded again!

        # then search for [[link text|target]] syntax
        #link_rgx = r"\[\[([^\|\[\]]*?)\|([\$\w]+)\]\]"
        link_rgx = r"\[\[(?:(?P<text>(?:(?!\]\]).)+?)\|)?(?P<link>\w+)\]\]"
        last_index=0
        for link in re.finditer(link_rgx, expanded):
            link_text = link["text"] or link["link"]
                
            assert link["link"] in self.controller.states
            self.transitions[link_text]=link["link"]
            self.choices.append(link_text)

            # add previous text to the result
            self.message+=expanded[last_index:link.start()]
            if self.controller.echo:
                self.message+="["+link_text+"]"
            last_index=link.end()

            # skip adding newlines to the message if the link is on
            # a separate line and the text is not echoed
            if (not self.controller.echo
                and last_index < len(expanded)
                and expanded[last_index]=="\n"):
                last_index+=1
                #don't forget any text after the last link
        self.message+=expanded[last_index:]
        if len(self.message)>1:
            if self.message[-1]=="\n":
                self.message=self.message[:-1]
            if self.message[0]=="\n":
                self.message=self.message[1:]


        return self.message, self.choices
