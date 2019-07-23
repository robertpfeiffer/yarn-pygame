yarn.py, a Python interpreter for Yarn dialogue
===============================================

Running 
-------

At the moment, you can run the example frontend like this.

```bash
python3 console.py example_yarns/wiz.json
```

If you want to write your own frontend, you should import yarn, and use
`YarnController`.

- `YarnController.message()`: Get the text of the current yarn state
- `YarnController.choices()`: Get the choices available
- `YarnController.transition(choice)`: Advance the state of the dialogue.
  `choice` must be found in the list returned by `YarnController.choices()`

Look at the console.py frontend for inspiration.

Yarn.py syntax and semantics
----------------------------

For a *link*, use the standard Yarn syntax `[[your text here|targetNode]]`

To run Python code with *side effects* use `<<run $CODE>>`.
For example, `<<run x=5>>` sets a variable.
Local variables are saved in the YarnController instance, they can then be 
referenced in other diaogue nodes and in game code. In game code, you can query 
the value of a variable "var" in the `locals` dictionary of your controller.

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

Some convenient variables are automatically set by the Yarn controller. You can refer to them in your nodes without any further setup. `visited` is a dict of which nodes have been visited. `visited_before` is a bool indicating whether the current node has been visited before. `state` is the name of the current node. `ast_state` is the name of the last node.

Different frontends will assign further meaning to Yarn nodes text, for 
example to connect text to multiple characters. In the future, it might look 
like this:

```
Alice: Hello, Bob!

Bob: Hello, Alice!

Alice(angrily): It's time you returned the money you owe me

Bob: *exit stage left*
```
