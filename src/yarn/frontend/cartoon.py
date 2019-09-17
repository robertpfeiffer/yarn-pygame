# part of yarn.py, copyright © 2019 Robert Pfeiffer
import pygame, math, re
import yarn.controller

class Characters(object):
    pass

class Dialogue(object):
    def __init__(self, name, path, characters, main_character, speech, thought, n_bubbles, font, **variables):
        self.characters={}
        chars_obj=Characters

        for char_name in characters:
            self.characters[char_name.lower()]=characters[char_name]
            setattr(chars_obj,char_name,characters[char_name])

        nchars=0
        cum_x=0
        min_y=10000
        for char in self.characters:
            char_x = self.characters[char].rect.centerx
            char_y = self.characters[char].rect.top
            cum_x+=char_x
            min_y=min(min_y, char_y)
            nchars+=1
        assert(nchars>0)
        self.avg_x=cum_x/nchars
        self.min_y=min_y - 3
        self.busy=False

        self.controller=yarn.controller.YarnController(path, name, False, dict(chars=chars_obj, **variables))
        self.message=self.controller.message().split("\n")
        self.message_line=0
        self.speech_template=speech
        self.thought_template=thought
        self.font=font
        self.options=self.controller.choices()
        self.selected=0
        self.finished=False
        self.n_bubbles=n_bubbles
        self.bubbles=[]
        self.thought_bubbles=[]
        self.bubbles_g=pygame.sprite.Group()
        self.main_character=main_character

    def deliver_line(self):
        if len(self.message)==0:
            return
        if self.message_line < len(self.message):
            line=self.message[self.message_line]
            
            dialogue_line=r"(\w+)\:(.*)"
            stage_direction=r"\/(\w+) (\w+)\b(.*)$"
            match=re.match(dialogue_line, line)
            match2=re.match(stage_direction, line)
            if match:
                character=self.characters[match[1]]
                content=match[2]
                content=yarn.controller.run_macros(content,
                                                   self.controller, True)
                new_bubble=self.draw_bubble(character, content)
                for other_bubble in self.bubbles:
                    other_bubble.rect.top -= (new_bubble.rect.height + 3)
                self.bubbles.append(new_bubble)
                self.bubbles_g.add(new_bubble)
            elif match2:
                character=self.characters[match2[1]]
                command=match2[2]
                args=match2[3].split()
                #print("Stage Direction", character, command, args)
                self.busy=True
                self.stage_direction=character, command, args
                self.direction_time=0
            else:
                for bubble in self.bubbles_g:
                    bubble.kill()
                    self.bubbles=[]
                #print(line)
            #assert(match or match2)

    def run_stage_direction(self, screen_rect):
        if self.busy:
            character, command, args=self.stage_direction
            #print(">", character, command, args, self.direction_time)

            if command=="clear":
                for bubble in self.bubbles:
                    if bubble.character==character:
                        bubble.kill()
                self.busy=False
            if command=="exit":
                if self.direction_time==0:
                    for bubble in self.bubbles:
                        if bubble.character==character:
                            bubble.kill()
                if args[0]=="stage_right":
                    character.rect.left+=3
                if args[0]=="stage_left":
                    character.rect.right-=3
                if (character.rect.left>screen_rect.right
                    or character.rect.right<screen_rect.left):
                    self.busy=False
                    character.kill()
            elif command=="shake":
                if self.direction_time==0:
                    self.pre_shake_pos=character.rect.left
                elif self.direction_time>45:
                    self.busy=False
                    character.rect.left=self.pre_shake_pos
                    del self.pre_shake_pos
                else:
                    character.rect.left=self.pre_shake_pos+math.sin(self.direction_time/2)*50/self.direction_time
            self.direction_time+=1
            if not self.busy:
                del self.direction_time
                del self.stage_direction
                self.advance()                
            
    def advance(self):
        if self.busy:
            return
        if self.finished:
            for bubble in self.bubbles_g:
                bubble.kill()
            return
        if self.message_line < len(self.message):
            self.message_line+=1
        if self.message_line < len(self.message):
            line=self.message[self.message_line]
            if not line.isspace():
                if len(self.bubbles)>=self.n_bubbles:
                    self.bubbles[0].kill()
                    self.bubbles=self.bubbles[1:]
                self.deliver_line()
        if (self.message_line == len(self.message)
            and self.controller.finished):
            self.finished=True
            for bubble in self.bubbles_g:
                bubble.kill()
            return
        if (self.message_line == len(self.message)
            and self.options):
            if len(self.bubbles)>=self.n_bubbles:
                self.bubbles[0].kill()
                self.bubbles=self.bubbles[1:]
            self.thought_bubbles=self.draw_thought_bubbles()
            for tb in self.thought_bubbles:
                self.bubbles_g.add(tb)
                

    def select_next(self):
        if (self.message_line == len(self.message) and
            self.selected < len(self.options)-1):
            self.selected+=1

    def select_prev(self):
        if (self.message_line == len(self.message) and
            self.selected > 0):
            self.selected-=1

    def prepare_bubble(self, line, template, flipped):
        text = self.font.render(line, 0, (0,0,0))
        bubble_rect= template.calc_target_rect(text.get_rect())
        bubble_rect.topleft=(0,0)
        bubble_surf=pygame.Surface(bubble_rect.size).convert()
        bubble_surf.fill((255, 0, 255, 0))
        bubble_surf.set_colorkey((255, 0, 255))
        
        #print(bubble_rect)
        #print(line)
        content_rect,_=template.blit(bubble_surf, bubble_rect)
        if flipped:
            bubble_surf=pygame.transform.flip(bubble_surf, True, False)
            content_rect.left=bubble_rect.right-content_rect.right
        bubble_surf.blit(text, content_rect.topleft)
        return bubble_surf
            
    def draw_thought_bubble(self, line):
        character=self.main_character
        bubble_surf=self.prepare_bubble(
            line,
            self.thought_template,
            character.rect.centerx < self.avg_x)
        bubble_rect=bubble_surf.get_rect()
        bubble_sprite=pygame.sprite.Sprite()
        bubble_sprite.image=bubble_surf
        bubble_sprite.rect=bubble_rect
        bubble_sprite.text=line
        bubble_sprite.character=character
        if character.rect.centerx < self.avg_x:
            bubble_rect.right=character.rect.left
        else:
            bubble_rect.left=character.rect.right
        bubble_rect.bottom=self.min_y
        return bubble_sprite

    def draw_thought_bubbles(self):
        result=[]
        for option in self.options:
            sprite=self.draw_thought_bubble(option)
            for r in result:
                r.rect.top-= sprite.rect.height+3
            result.append(sprite)
        return result
            
    
    def draw_bubble(self, character, content):
        bubble_surf=self.prepare_bubble(
            content.strip(),
            self.speech_template,
            character.rect.centerx > self.avg_x)
        bubble_rect=bubble_surf.get_rect()
        bubble_sprite=pygame.sprite.Sprite()
        bubble_sprite.image=bubble_surf
        bubble_sprite.rect=bubble_rect
        bubble_sprite.text=content
        bubble_sprite.character=character
        
        if character.rect.centerx < self.avg_x:
            bubble_rect.left=character.rect.right
        else:
            bubble_rect.right=character.rect.left
        bubble_rect.bottom=self.min_y
        return bubble_sprite

    def choose_option(self):
        if self.busy:
            return
        if self.finished:
            return
        if (self.message_line == len(self.message)):
            self.controller.transition(self.options[self.selected])
            self.message=self.controller.message().split("\n")
            #print(self.message)
            self.message_line=0
            self.options=self.controller.choices()
            self.selected=0
            for bubble in self.bubbles_g:
                bubble.kill()
            self.bubbles=[]
            self.thought_bubbles=[]
            self.deliver_line()
            

