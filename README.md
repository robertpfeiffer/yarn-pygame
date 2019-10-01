yarn.py, a Python runtime for Yarn dialogue
===========================================

Getting Started 
---------------

At the moment, you can run the console frontend like this.

```bash
PYTHONPATH=$PYTHONPATH:src/ python3 runner.py yarns/yarn.json
```

There are examples for the pygame-based frontends in `examples/`.

If you want to write your own frontend, you should import yarn, and use
`YarnController`.

- `YarnController.message()`: Get the text of the current yarn state
- `YarnController.choices()`: Get the choices available
- `YarnController.transition(choice)`: Advance the state of the dialogue.
  `choice` must be found in the list returned by `YarnController.choices()`

Look at the console.py frontend for inspiration.

To edit yarn files, try https://yarnspinnertool.github.io/YarnEditor/
This web app is based on the old node-webkit Yarn editor, but it runs in
modern browsers (source at https://github.com/YarnSpinnerTool/YarnEditor).

There's also a simple pygame-based editor tool included, but it's not well
documented and you need to to have the emacs daemon running, or either of gvim,
Visual Studio Code, or sublime text as a fallback in order to use it.
If you're using yarn.py to add dialogue to your pygame games, it's a fair bet
you already have Emacs and pygame installed ;)

Run the editor with:
```
python3 editor.py FILENAME.json
```
To edit a node, double click it. This will open your text editor. Deleting the
whole tile and content of a node in your text editor will delete the node.
You can drag nodes around with the left mouse button, and move the viewport by
clicking and dragging the empty space between the nodes.
In order to create a new node, you must link to it from an existing node, and
the middle-click the existing node. Broken links are shown in red under every
node.
If you quit the yarn editor by closing the window, your file will be saved
automatically.

Installation
------------

Copy `src/yarn/` into your `$PYTHONPATH` or into your game. This library is 
meant to be used in games, it's pure Python, just vendor it in! If anybody has
a use case that requires putting this on PyPI, I'll do it, but for now, no need
to make things complicated.
The editor (licensed under the GPLv3) and the example code are not included in
`src/yarn/`.

Yarn.py syntax and semantics
----------------------------

For a *link*, use the standard Yarn syntax `[[your text here|targetNode]]`

To run Python code with *side effects* use `<<run $CODE>>`.
For example, `<<run x=5>>` sets a variable.
Local variables are saved in the YarnController instance, they can then be
referenced in other diaogue nodes and in game code. In game code, you can
query the value of a variable "var" in the `locals` dictionary of your
controller.

To *paste* the value of a Python expression, use `<<print $EXPR>>`.
Text returned by `<<print>>` statements can contain links, but no macros.
This means `<<print "[[link text|targetNode]]">>` will create a link, but
`<<print "<<run x=5>>">>` will not run the `<<run>>` macro. You can also refer
to variables set previously in the same or different nodes, like this:
`<<run name="Dolly">>Hello, <<print name>>`

For *conditionals*, use `<<if $EXPR>> $BRANCH_A <<else>> $BRANCH_B <<endif>>`
Both branches can contain text, `<<macros>>`, links, and conditionals.
Conditionals can be nested as you would expect. Macros in skipped branches will
not be run, so you can use `<<if>>` to control both text substitution and side
effects.

Some convenient variables are automatically set by the Yarn controller. You can
refer to them in your nodes without any further setup. `visited` is a dict of
which nodes have been visited. `visited_before` is a bool indicating whether
the current node has been visited before. `state` is the name of the current
node. `last_state` is the name of the visited last node.

There is also a shorthand syntax based on indentation. It gets compiled into
anonymous nodes. 
```
-> option A
   result A
-> option B
   result B
   -> sub-option B1
      result B1
   -> sub-option B2
      result B2
-> This is just text after the arrow you don't have to write "option"
   The text of the node
   can span over multiple lines
```

The shorthand
```
-> A
   B
   C
   [[foo|bar]]
```
is equivalent to 
```
[[A|OtherNode]]
```
where OtherNode contains
```
B
C
[[foo|bar]]
```

Roadmap
-------
Different frontends will assign further meaning to Yarn output, for 
example to connect text to multiple characters. It might look 
like this:

```
Alice: Hello, Bob!

Bob: Hello, Alice!

Alice(angrily): It's time you returned the money you owe me

/Bob exit stage_left
``` 

Features like this are already present in YarnSpinner, the de-facto "reference
implementation" of Yarn. We will aim for feature parity. But we won't aim for
full source compatibility, because YarnSpinner includes a custom macro language
instead of Python scripting.

License
-------
The editor implemented in the file `editor.py` is released under the terms of 
the GNU General Public License, version 3 or later.

The run-time components in src/yarn are released under the terms of the 
MIT License, to allow use in commercial, closed-source games.
