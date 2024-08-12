
# Python To Desynced How To

  

This utility compiles a *subset* of the Python 3 language into the Desynced behavior programming language.

This documentation assumes familiarity with the game https://store.steampowered.com/app/1450900/Desynced_Autonomous_Colony_Simulator/ 
and the language https://www.python.org/

### Getting Started
Load the webpage and wait 5-10 seconds for the utility to load. Click Examples and pick the first one in the list. This should populate the editor with working code to orient yourself with.


## Variables, Registers, and Inferred Temporaries
Desynced has 3 types of special names:
- A-W refer to local variables
 - P1-PN refer to registers (visible outside the behavior)
 - Special Registers ( Signal, Visible, Store, Goto )

You can explicitly bind to these by using their explicit name correctly capitalized.  Any  named variable that doesn't match an explicit binding will be given a parameter or local variable as appropriate.  Any inferred variables will be given a local variable.

```python
def NamingExample(unnamed_parameter, P4, second_parameter):
	if A < B+3:
		named_local_variable = P4
```
In the above example, 
- unnamed_parameter is bound to P1
- P2 and P3 are ignored
- P4 is used explicitly
- second_parameter is bound to P5
- A and B are used explicitly
- C is used to compute B+3 as an inferred variable
- named_local_variable is bound to D

### Limitations
Desynced currently only supports 22 local variables.  Inferred variables are currently single-use, so they accumulate quickly.  If you encounter this limitation consider rewriting inferred variables as explicit variables.
```python
total = 1+2+3+4+5+6+7+8+9+10 # uses 9 inferred variables
total += 1 ... total += 10   # uses no inferred variables
```

  The compiler can support an arbitrary number, but its emitter logic would need to be updated if this limit is removed.   


## Flow Control

### If and While
``` python
while ConditionalOpName(input_parameters):
	#loop body
if ConditionalOpName(input_parameters):
	# If True
else:
	# If False
```
By default, the top-most flow path is the "True" case.  This aligns with _most_ of the Desynced Ops, but there are several that are flipped.    Adjusting this is on the to do list; for now use modifiers to capture the intended behavior.
#### Modifiers
The `not` operator works as expected: it will invert the conditions for flow.
A specific flow can be tagged as the True flow path by appending it to the op name using double underbars:
```python
if GetSeason__Spring__Summer():
	# Executes if it is Spring or Summer
else:
	# Executes if it is Winter or Fall
```
### Switch Case
Ops that support multiple execution paths are more similar to C's "switch case" syntax than python's syntax options.  This looks a bit ugly; fixing it is on the to do list.
```python
if GetSeason():
	#default case is the first output of the op, in this case Winter.
elif "Spring":
	#do this if Spring
else:
	# All unhandled cases, Summer and Fall
```
### For
For loops are only supported for ops that maintain their own loop frame.  These are typically ops that start with the word "Loop", or more definitively, ops that have a "done" execution path out.
```python
for out1, out2 in LoopOpName(input1, input2):
	# loop body
```
### Inferred Comparisons
All comparison bin ops ( < > <= >= !=   == ) are translated to the CompareNumbers op.  
Other equality comparisons must be used explicitly as function calls.