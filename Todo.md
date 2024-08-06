# To Do
If you're interested in contributing to this project, here is a running list of things that could be helpful.

## More Examples


## Documentation

## Flow Control
Add support for 3 or more flow nodes.  The flow control section currently supports this for if statements only, but the ds_call emiter doesn't have support this feature yet.

## Comparison BinOps
Desynced has multiple comparison ops, forcing typing-decisions to be made by the programmer.  Python uses run time type to make this decision.  Not clear what the best path forward here is - probably assume numeric type for binops and rely on explicit functions for non-numerics.

The first part of this would be emitting CompareNumber__GREATER style binops.  The next step would rely on the flow control update above.


## Beautification
This is my first React anything.  Any and all UI improvements are warmly accepted.

### CodeMirror Scrolling
I was unable to convince CodeMirror to occupy all the space available on the screen and maintain it's own scroll bar.  I think this is the lowest hanging fruit.

### Small Screen Support
On smaller screens the compile/copy/clear buttons are difficult to access.






why didn't this open the parameter correclty?

def StoreInNearestMatch(storagesignal):
    closest = 0
    for A, B in LoopSignalMatch(storagesignal):
        closest = SelectNearest(closest, A)
    Store = closest