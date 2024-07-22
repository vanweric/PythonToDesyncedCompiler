# To Do

### Flow Control
No syntactic support for 3 or more flow nodes.

### Comparison BinOps
Desynced has multiple comparison ops, forcing typing-decisions to be made by the programmer.  Python uses run time type to make this decision.  Not clear what the best path forward here is - probably assume numeric type for binops and rely on explicit functions for non-numerics.

### Empty Loop Bodies
Compiler currently can't handle loops with no entries in the body.  However, neither can the Desynced.
Emit a No-Op in this case.