# Python To Desynced Compiler

I've been playing [Desynced](https://www.desyncedgame.com/), a base building video game that features programmable behaviors for units.  I found that writing my code out in a python-style pseudocode first really helped me write the Desynced code.  I decided to try to compile my pseudocode into something Desynced could actually execute, and here is the result.

# How to Use
## Online
The Online Version is [here](https://vanweric.github.io/PythonToDesyncedCompiler/)

This binder link will open a Jupyter environment with everything ready to go:  
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/vanweric/PythonToDesyncedCompiler/master?labpath=PythonToDesynced.ipynb)

## Offline
Clone this repository (or just grab PythonToDesynced.ipynb).  You'll need Jupyter installed at a minimum.  I also recommend ASTPretty.

## Running the Notebook
The notebook is designed to build the compilation process up step by step.  
Each cell depends on the ones before it, so  Run ---> Run All might be a good place to start.

Each step has descriptive text, the actual compilation code for that step, and then a test cell.  Edit the python code at each step to see how it flows through the logic.

If you're new to Jupyter, [this tutorial](https://github.com/jupyter/notebook/blob/main/docs/source/examples/Notebook/Notebook%20Basics.ipynb) might help.  Otherwise, "ctrl-enter" to run a cell is all you really need to know.

# External Dependencies

## instructions.lua
All of the game's opcodes are in a file called "instructions.lua".  The information from this file is what lets the compiler know what functions are available, and to match them up at compilation time.  

## base62 + serialize
The compiler emits a JSON string.  In order to import it to the game it needs to be serialized and base62 encoded.  I haven't ported this functionality yet, but it is available online from the devs here:
https://stagegames.github.io/DesyncedJavaScriptUtils/
