


### Registers

You can access the 4 special registers by referring to them by name: Signal, Visual, Store, Goto.

These are case sensitive.

```python 
def StoreInNearestMatch(storagesignal):
    closest = 0
    for A, B in LoopSignalMatch(storagesignal):
        closest = SelectNearest(closest, A)
    Store = closest
```

Accessing other registers in this way is not supported.  I recommend using P1-PN and then linking to the component registers.  Alternatively,  use GetFromComponent and SetToComponent.  

### Function Parameters
Desynced Function Parameters are P1, P2, P3, ..., 
P2D will accept aliases for these parameters as part of function definition.

This declaration will alias P1 to Leader, and P2 to OreType:
```python
def MyFunction(Leader, OreType):
    pass
```

#### Rules
1) Parameters are strictly in ascending order.
2) Parameters can be skipped.
