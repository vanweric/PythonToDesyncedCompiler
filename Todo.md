# To Do

If you're interested in contributing to this project, here is a running list of things that could be helpful.

## User Onboarding Experience:

### More Examples

To add an example, add it to the examples folder as a .py and link to it in app.js.
Help in eliminating the "link to it in app.js" step would be appreciated.

### Documentation

Documentation will eventually be held in Info.md

## Beautification

This is my first React anything. First Web anything really since the heyday of MySpace and the Blink tag. Any and all UI improvements are warmly accepted.

### CodeMirror Scrolling

I had difficulty convincing CodeMirror to occupy all of it's space and maintain it's own scrollbar. The current workaround is functional but not pretty.

### Small Screen Support

On smaller screens the compile/copy/clear buttons are difficult to access.

### Refine Autocomplete

Autocomplete suggests a lot of functions that are relevant to python but not to desynced python.
Removing the dunder completes would be a good start.

## Functionality

### For x in Range():

This type of loop currently isn't supported.
I see two potential paths:

1. Add a LoopRange op to Desynced
2. Add a special case to the compiler that translates for x in range(start, stop, stride): to x= start, while x < stop: body x+=stride

### Constant Folding / Constant Propagation

Constant folding is identifying expressions that can be evaluated at compile time and replacing them with that expression. Unclear whether the folder in ast_opt.c can be used here.
This would likely just be a NodeTransformer that happens very early.

Several of my scripts have a variable at the top that acts as a constant but is compiled as a variable. It would be nice to eliminate all the extra ops that requires.
There isn't a good syntax structure for python to mark a constant.

### Enumerated Inputs

Some functions have inputs on a drop down menu, such as MoveUnit (Synchronously / Asynchronously).

### Match Syntax for Switch Case

Right now switch is implemented with if/elif chains. Match is relatively new syntax, but would be cleaner here.
Match was introduced in CPython 3.10, and Pyodide version 0.20

### Walrus Operator

If and while loops currently don't support output variables. Adding support for the walrus operator would enable this.

### Inverted Conditionals

The Desynced ops don't have consistent ordering of their conditionals - about 10% have flipped logic. It would be useful to identify these and special case them.

### Variable Coloring / Re-use

Variables that are inferred are single use only. Desynced only supports 22 variables, and lots of inferred variables can eat through this quickly.

Determine lifetime for these and allow overlapping useage.

### Blueprints

Place Construction can be given a blueprint via keyword bp={dict describing blueprint}.
This requires the user to be very familiar with the inner workings of the game, or to be able to reverse engineer blueprints using their disassembler.
Unclear what the right path forward is, suggestions welcome.

### Micropip or Wheels

The majority of the loading time and loading size is that the compiler is loaded as a text file and then compiled every time the page is loaded. This would be dramatically improved by prepackaging.

### Better Unit Testing

I let my first batch of unit tests rot during a big refactor, so the coverage is pretty sparse right now. Adding coverage would be a great way to get to know the system.
