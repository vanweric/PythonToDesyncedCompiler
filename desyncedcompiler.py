import json
import ast
import inspect

def SyntaxErrorFromAST(message, node):
    return SyntaxError(message, (None, node.lineno, node.col_offset, None))

# Section 2: Replacing Binops with Calls
def replace_binops_with_functions(tree):
    class BinOpReplacementVisitor(ast.NodeTransformer):
        # Replace binary operations with function calls
        binop_map = {ast.Add: 'Add',
                     ast.Sub: 'Subtract',
                     ast.Mult:'Multiply',
                     ast.Div: 'Divide',
                     ast.Mod: 'Modulo',
                        }
        def visit_BinOp(self, node):
            if isinstance(node.op, ast.operator) and node.op.__class__ in self.binop_map:
                #self.generic_visit(node)
                new_node = ast.Call(
                    func=ast.Name(id=self.binop_map[type(node.op)], ctx=ast.Load()),
                    args=[self.visit(node.left), self.visit(node.right)],
                    keywords=[],
                    starargs=None,
                    kwargs=None
                )
                new_node=self.visit(new_node)
                ast.copy_location(new_node, node)
                return new_node
            else:
                return node

        def visit_UnaryOp(self, node):
            # Allow negative numbers
            if isinstance(node.op, ast.USub):
                print("usubbing")
                node.operand.value *= -1
                return node.operand
            else:
                return node

        def visit_AugAssign(self, node):
            if isinstance(node.op, ast.operator) and node.op.__class__ in self.binop_map:
                new_node = ast.Assign(
                    targets = [node.target],
                    value = ast.Call(
                        func=ast.Name(id=self.binop_map[type(node.op)], ctx=ast.Load()),
                        args=[node.target, node.value],
                        keywords=[],
                        starargs=None,
                        kwargs=None
                    )
                )
                
                new_node=self.visit(new_node)
                ast.copy_location(new_node, node)
                return new_node
            else:
                return node

        def visit_Compare(self, node):
            compare_map = {
                'Lt':'Smaller',
                'LtE':'Smaller__Equal',
                'Gt':'Larger',
                'GtE':'Larger__Equal',
                'Eq':'Equal',
                'NotEq':'Smaller__Larger',
            }
            compare_type = ast.dump(node.ops[0])[:-2]
            # TODO Make type finding more robust. 
            new_node = ast.Call(
                func = ast.Name(id="CompareNumber__"+compare_map[compare_type], ctx=ast.Load()),
                args = [self.visit(node.left), self.visit(node.comparators[0])],
                keywords = [],
                starargs=None,
                kwargs=None,
            )
            ast.copy_location(new_node, node)
            return new_node

    visitor=BinOpReplacementVisitor()
    return visitor.visit(tree)

# Section 3: Flatten Nested Calls
def flatten_calls(tree):
    class FlatteningTransformer(ast.NodeTransformer):
        def __init__(self):
            super().__init__()
            self.temp_count = 1

        def visit_UnaryOp(self, node):
            if isinstance(node.op, ast.Not):
                operand = node.operand
                operand.func.id = operand.func.id+'__NOT'
                return self.visit(operand)

        def visit_Call(self, node):
            nodelist = []
            for i, arg in enumerate(node.args):
                if isinstance(arg, ast.Call):                
                    temp_var = f'Temp_{self.temp_count}'
                    self.temp_count += 1
                    node.args[i] = ast.Name(id=temp_var, ctx=ast.Load())
                    #list of all calls that have to happen first
                    ncalls = self.visit_Call(arg)
                    ncalls[-1].targets=[ast.Name(id=temp_var, ctx=ast.Store())]
                    nodelist.extend(ncalls)
            assign_wrapper = ast.Assign(targets=[], #to be filled in by parent
                                        value=node,
                                        keywords=[])
            nodelist.append(assign_wrapper)
            
            return nodelist

        def visit_Assign(self, node):
            if isinstance(node.value, (ast.Name, ast.Constant, ast.Tuple)):
                # Special case for a bare Assignment - this is a Copy function, which is 'set_reg' internally
                call = ast.Call(func = ast.Name(id='Copy', ctx='Load'),
                                targets = node.targets,
                                args = [node.value],
                                keywords=[])
                node.value = call
                return node
            if isinstance(node.value, ast.Call):
                ncalls = self.visit(node.value)
                ncalls[-1].targets=node.targets
                return ncalls

        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call):
                ncalls = self.visit(node.value)
                #ncalls[-1] = ast.Expr(value = ncalls[-1].value)
                return ncalls

    transformer = FlatteningTransformer()
    tree = transformer.visit(tree)
    return tree

# Section 4: Translate to DS Calls

class DS_Call(ast.Assign):
    _fields = ('targets', 'args', 'op', 'frame', 'next')

    def __init__(self, targets, args, op, keywords={}):
        self.targets = targets
        self.args = args
        self.next = {}
        self.frame = -1
        self.op = op
        self.keywords = keywords

    def unparse(self, node):
        self.fill()
        self.traverse(node.targets)
        if(len(node.targets)): self.write(' = ')
        self.write(f"DS_Call_{node.op}")
        with self.delimit("(", ")"):
            comma = False
            for e in node.args:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)
        self.write(f" | {node.frame}-->{node.next}")

''' Monkey-Patch in an unparser for DS Calls '''
ast._Unparser.visit_DS_Call = DS_Call.unparse
def convert_to_ds_call(tree):
    
    class DS_Call_Transformer(ast.NodeTransformer):   
        
        def visit_Call(self, node, target=None):
            if target:
                node.targets=[target]
            dscall =DS_Call( targets=[target], args=node.args, op=node.func.id,
                           keywords = getattr(node, 'keywords', {}) )
            ast.copy_location(dscall, node)
            return [dscall]

        def visit_Assign(self, node):
            if isinstance(node.value, (ast.Name, ast.Constant, ast.Tuple)):
                # Special case for a bare Assignment - this is a Copy function, which is 'set_reg' internally
                new_node = DS_Call(targets = node.targets, args = [node.value], op = 'Copy')
                ast.copy_location(new_node, node)
                new_node = self.visit(new_node)
                return new_node
            nodelist = self.visit_Call(node.value)
            nodelist[-1].targets = node.targets
            for n in nodelist:
                self.visit(n)
            return nodelist

        def visit_Expr(self, node):
            nodelist = self.visit_Call(node.value)
            for n in nodelist:
                self.visit(n)
            return nodelist

        def visit_Tuple(self, node):
            if isinstance(node.elts[0], ast.Name):
                return [e for e in node.elts]
            if isinstance(node.elts[0], ast.Constant):
                return ast.Constant( value=[e.value for e in node.elts])
            return node

    return DS_Call_Transformer().visit(tree)

# Section 5: Labeling Pass

def label_frames_vars(tree, debug=False):
    allowed_names = 'ABCDEFGHIJKLMNOQRSTUVW' #don't allow P or past W
    special_names = ['Goto','Store','Visual','Signal', '_']
    
    class ParameterFinder(ast.NodeVisitor):
        def __init__(self, variables={}):
            self.variables = variables

        def visit_arguments(self, node):
            '''
            Named arguments (P1, P2, P3, ...) always use their named slot.
            Unnamed arguments are given the next available slot.
            This may leave gaps.
            '''
            p_ix = 1
            for arg in node.args:
                if arg.arg[0] == "P" and arg.arg[1:].isdigit():
                    new_ix = int(arg.arg[1:])
                    if new_ix > p_ix: 
                        p_ix = new_ix
                    elif new_ix < p_ix:
                        raise SyntaxErrorFromAST(
                            f'A named Parameter ({arg.arg}) with a lower index was given after a higher index ({p_ix})',
                            arg)
                self.variables[arg.arg] = f"P{p_ix}"
                p_ix+=1

    class VariableFinder(ast.NodeVisitor):
        def __init__(self, variables={}):
            self.variables = variables

        def visit_Name(self, node):
            if node.id not in self.variables.values():
                if node.id in allowed_names or node.id in special_names:
                    self.variables.setdefault(node.id,node.id)
                else:
                    self.variables.setdefault(node.id,None)

    
    def remap_temp_variables(mapping):
        '''
        At this point parameters are already renamed
        '''
        existing_keys = list(mapping.keys())
        for key in existing_keys:
            if mapping[key] is None:
                name = next((name for name in allowed_names if name not in mapping.values()), None)
                if name is None:
                    raise SyntaxError("Too many registers used - Desynced supports up to 22 only")
                        
                mapping[key] = name
        return mapping 

    
    class VariableLabeler(ast.NodeTransformer):
        def __init__(self, mapper):
            super().__init__()
            self.mapper = mapper
        
        def visit_Name(self, node):
            if node.id in self.mapper.keys():
                    node.id = self.mapper[node.id]
            return node

        def visit_arg(self, node):
            if node.arg in self.mapper.keys():
                node.arg = self.mapper[node.arg]+'|'+node.arg
            return node
            
    class FrameLabeler(ast.NodeTransformer):  
        def __init__(self):
            super().__init__()
            self.frame_count = 0
            
        def visit_DS_Call(self, node):
            node.frame = self.frame_count
            self.frame_count+=1
            return node

    parameterfinder = ParameterFinder()
    parameterfinder.visit(tree)
    parameters = parameterfinder.variables
    if (debug): 
        print(parameters)
        
    variablefinder = VariableFinder(parameters)
    variablefinder.visit(tree)
    parameters_and_variables = variablefinder.variables
    if (debug): 
        print(parameters_and_variables)
        
    remap = remap_temp_variables(parameters_and_variables)
    flipped_remap = {k:v for k,v in remap.items()}
    if (debug): 
        print(f'{flipped_remap=}')
        
    varlabeler = VariableLabeler(flipped_remap)
    tree = varlabeler.visit(tree)
    
    framelabeler = FrameLabeler()
    tree = framelabeler.visit(tree)
    return tree

# Section 6: Flow Control

def flow_control(tree):
    def flow_list(nodelist, exit):
        '''
        Connects frames in sequence in a list.
        All flow_ functions take an exit and return an entrance
        '''
        first_frame = None
        for item, next_item in zip(nodelist, nodelist[1:] + [None]):
            #lexit = exit if next_item is None else find_first_last_DS_Call([next_item])[0].frame
            
            next_frame_start = None
            current_frame = None
            match next_item:
                case DS_Call():
                    next_frame_start = next_item.frame
                case None:
                    # End of List
                    next_frame_start = exit
                case ast.While():
                    next_frame_start = next_item.test[0].frame
                case ast.For():
                    next_frame_start = next_item.iter[0].frame
                case ast.If():
                    next_frame_start = next_item.test[0].frame
                case _:
                    print(type(item))
                    print("OHNO")

            match item:
                case DS_Call():
                    current_frame = item.frame
                    item.next = {'all': next_frame_start}
                case ast.While():
                    current_frame = flow_While(item, next_frame_start)
                case ast.For():
                    current_frame = flow_For(item, next_frame_start)
                case ast.If():
                    current_frame = flow_If(item, next_frame_start)
                case ast.Pass():
                    return exit

                case ast.FunctionDef():
                    raise SyntaxErrorFromAST("Subroutines and Multiple Function Definitions not supported", item)
                    
                case _:
                    print(type(item))
                    print("OHNO")

            if first_frame is None: first_frame = current_frame

        return first_frame
            
        #view_flow_list(nodelist, "after")
    
    def flow_While(node, exit):
        test_first = flow_list(node.test, exit)
        body_first = flow_list(node.body, test_first)
        node.test[-1].next = {'true': body_first, 'false': exit}
     
        return test_first
        
    def flow_For(node, exit):
        target = node.target
        ''' The unparser needs the for loop to still have a valid target '''
        node.target = ast.Name(id='_', ctx=ast.Store())

        #Special Case - Loop instructions create a stack frame.
        test_first = flow_list(node.iter, exit)
        body_first = flow_list(node.body, -1)

    
        node.iter[-1].next = {'true': body_first, 
                              'done': exit}
        
        if isinstance(target, list):
            node.iter[-1].targets = target
        else:
            node.iter[-1].targets = [target]

        return test_first
    
    def flow_If(node, exit):
        test_first = flow_list(node.test, exit)
        body_first = flow_list(node.body, exit)
        node.test[-1].next = {'true': body_first, 'false': exit}
        
        head = node.orelse  #Guaranteed to be an "If()"
        while(head):
            match head:
                case []:
                    print("Did we ever get here? []")
                    head = None
                                        
                case [ast.If(test=ast.Constant()) as first, *rest]:
                    label = head[0].test.value
                    body_first = flow_list(head[0].body, exit)
                    head = head[0].orelse
                    node.test[-1].next[label] = body_first
                                        
                case [ast.Pass() as first, *rest]:
                    print("passing")
                    head=None
                    pass
                    
                case _:
                    label = 'false'
                    body_first = flow_list(head, exit)
                    head = None
                    node.test[-1].next[label] = body_first
        
        return test_first


            
    # this is a real bad hack and will need to be fixed to support nested function calls.
    if isinstance(tree.body[0], ast.FunctionDef):
        return flow_list(tree.body[0].body, -1)
    return flow_list(tree.body, -1)

# Section 7: Import Desynced Ops

class desynced_ops:
    _instructions = None
    
    def __new__(cls, path=None, jsonfile=None):
        raw_import = None
        if path:
            with open (path, 'r') as jsonfile:
                import json
                raw_import = json.load(jsonfile)["instructions"]
        elif jsonfile:
            raw_import = jsonfile["instructions"]

        if raw_import:
            cls._instructions =  {cls.to_function_name(v['name']):{**v, 'op':k} 
                                  for k,v in raw_import.items() if 'name' in v.keys()}
            print("instructions initialized")

    @classmethod
    def instructions(cls):
        if cls._instructions:
            return cls._instructions
        else:
            print(cls._instructions)
            raise Exception("Instructions not initialized")

    @classmethod
    def to_function_name(self, string):
        # Desynced block names are typically all capitalized.  Standardize on this.
        # Obsolete instructions are marked by being surrounded by asterixes.  Replace with _ so it is a valid python function name
        result =''.join([word.capitalize() for word in string.replace('*','_').replace('(','').replace(')','').split()])
        return result

    
def import_desynced_ops(path = None, jsonfile = None):
    desynced_ops(path, jsonfile)
    return desynced_ops.instructions()

# Section 8: Translate to DSO

def create_dso_from_ast(tree, debug=False):
    ds_ops = desynced_ops.instructions()
    class DSO_from_DSCalls(ast.NodeVisitor):
        def __init__(self, debug=False):
            self.dso={}
            self.debug=debug
            self.parameters={}

        def translate_register_or_value(self, tlist, ix):
            try:
                val = tlist[ix]
            except IndexError:
                return False
            # Values get Handled here.
            #  '_" is special cased to mean not used.
            #  Local variables (A,B,C) are emitted as strings.
            #  Parameters (P1, P2) are emitted as numbers.
            if isinstance(val, ast.Name):
                if val.id == '_':
                    return False
                if val.id[0] == 'P':
                    parameter_ix = int(val.id[1:])
                    self.parameters.setdefault(parameter_ix,True)
                    return parameter_ix
                specialregs= {'Goto':-1,
                              'Store':-2,
                              'Visual':-3,
                              'Signal':-4}
                if val.id in specialregs.keys():
                    return specialregs[val.id]
                return val.id
                
            if isinstance(val, ast.Constant):
                if isinstance(val.value, int):
                    return {"num": val.value}
                if isinstance(val.value, str):
                    #this is where to add translation of constants, e.g. "Metal Ore" to "metalore"
                    return {"id": val.value}

                if isinstance(val.value, list):
                    if isinstance(val.value[0], int) and isinstance(val.value[1], int):
                        return {"coord": {"x": val.value[0], "y": val.value[1]} }
                    if isinstance(val.value[0], str) and isinstance(val.value[1], int):
                        return {"id": val.value[0], "num": val.value[1]}
                    if isinstance(val.value[0], int) and isinstance(val.value[1], str):
                        return {"id": val.value[1], "num": val.value[0]}


        def execs_from_call(self, node, op, parameters, debug=False):
            '''
            Identify all flow out paths

            Match flow paths:
                'all':   All out paths follow this 
                'false': Remaining out paths follow this
                'done':  Loop exit
                'true':  Top-most exec
                'not':   Flip polarity
                str:     Explicit case-free match
                tuple:   Explicit match all within tuple

            Remove Next if it is unused or equal to the next frame
            '''            
            exec_arg = op.get('exec_arg', None)
            op_args = op.get('args', [])

            # info from the op itself
            args = {}
            if exec_arg is None:
                args['next']= 'next'
            elif exec_arg:
                args[exec_arg[1].lower() ]= 'next'
                
                
            if op_args:
                for i, arg in enumerate(op_args):
                    if arg[0] == 'exec':
                        args[arg[1].lower()]= i

            parameters = [p.lower() for p in parameters]

            # info from the flow controller
            flows = {}
            for key, value in node.next.items():
                flows[key.lower()] = value+1 if value >= 0 else value
                        
            processed = {}
            if (debug):
                print('flows\t', flows)
                print('args\t',  args)
                print('params\t', parameters)
                

            #args are one time use
            def bind_and_delete(arg_key, flow_target, reason=""):
                    if (debug): 
                        print(f"Binding {arg_key=} to {flow_target=}\t", reason)
                    processed[args[arg_key]] = flow_target
                    del args[arg_key]
            
            if 'all' in flows:
                all_target = flows['all']
                processed = {value: all_target for key, value in args.items()}
                args = {}
                flows = {}
                
            # flow parameter as a switch target is highest priority
            if 'true' in flows:
                flow_target = flows['true']
                for param in parameters:
                    for arg in list(args.keys()):
                        if param != 'not' and param in arg:
                            bind_and_delete(arg, flow_target, "parameter")
                            if 'true' in flows: del flows['true']
                
            # switch targets are second highest priority
            for key in list(args.keys()):
                if key not in ['all','exit','true','not']:
                    if key in flows:
                        bind_and_delete(key, flows[key], "switch_target")
                        del flows[key]

            if 'true' in flows:
                target_arg = next(iter(args))
                print("True Target Arg is ", target_arg)
                bind_and_delete(target_arg, flows['true'], "true targets")
                del flows['true']

            if 'false' in flows and args:
                for key in list(args.keys()):
                    bind_and_delete(key, flows['false'], "false targets")
                del flows['false']

            ''' "Not" flips processed flows if there are only two outlets'''
            if 'not' in parameters:
                outlets = list({v for v in processed.values()})
                if len(outlets) != 2:
                    raise SyntaxErrorFromAST("NOT statements can only handle exactly two flow outlets", node)
                outlet_remap = {outlets[0]:outlets[1], outlets[1]:outlets[0]}
                processed = {k:outlet_remap[v] for k,v in processed.items()}
            if (debug): 
                print('proc\t', processed)
                print('flows\t', flows)
                print('args\t',  args)

            #remove flows that lead to the next frame, these are implied.
            # Currently bugged with nested loops going backwards one extra frame.
            # Disable for now as it is just space optimization.
            ###processed = {k:v for k,v in processed.items() if v!= node.frame+1}
            
            return processed
            

        def visit_DS_Call(self, node):
            opname, *parameters = node.op.split('__')
            op = ds_ops.get(opname, None)
            if not op:
                raise SyntaxErrorFromAST(f"Unknown Operation: {node.op=}", node)
            res={}
            res['op'] = op['op']

            target_ix=0
            arg_ix=0
            exec_ix=1
            if 'args' in op.keys():
                if self.debug:
                    print(op['args'])
                for i, arg in enumerate(op['args']):
                    if arg[0] == 'out':
                        res[str(i)] = self.translate_register_or_value(node.targets,target_ix)
                        target_ix +=1
                    if arg[0] == 'in':
                        res[str(i)] = self.translate_register_or_value(node.args,arg_ix)
                        arg_ix +=1
            
            if keywords := getattr(node, 'keywords', False):
                for keyword in keywords:
                    argname = keyword.arg
                    value = ast.literal_eval(ast.unparse(keyword.value))
                    res[argname] = value


            res.update(self.execs_from_call(node, op, parameters))
                       
            self.dso[str(node.frame)] = res

        def visit_arg(self, node):
            arg = node.arg
            parsed = arg[1:].split('|', 1)
            parameter_ix = int(parsed[0])
            name = parsed[1] if len(parsed)>1 else True
            self.parameters[parameter_ix]=name
            
        def parameters_block(self):
            ''' Parameter Block is a list of either True (included), False (Ignored) or a String (Name the parameter) '''
            if len(self.parameters):
                print("self.parameters ", self.parameters)
                pnames = [self.parameters.get(i+1, False) for i in range(max(self.parameters.keys()))]
                pnames = [True if p== 'P'+str(i+1) else p for i, p in enumerate(pnames)]
                pblock = [i in self.parameters.keys() for i in range(max(self.parameters.keys()))]
                
                print("pblock ", pblock)
                print("pnames ", pnames)
                self.dso["parameters"] = pblock
                self.dso["pnames"] = pnames
        def name_block(self, tree):
            try:
                name = tree.body[0].name
            except:
                name = "FromPythonCompiler"
            self.dso["name"] = name
            
    walker = DSO_from_DSCalls(debug)
    walker.visit(tree)
    walker.parameters_block()
    walker.name_block(tree)
    dso = walker.dso
    
    return walker.dso


# Section 9: Bas62 Encode

class b62:
    _instance = None
    def __new__(cls, environment=None):
        if not cls._instance:
            if environment == "python":
                cls._instance = b62_mini_racer()
            elif environment == "pyodide":
                cls._instance = b62_pyodide()
            else:
                raise Exception("Unknown environment") 
        return cls._instance

class b62_mini_racer():
    def __init__(self):
        print("Initializing Mini Racer")
        import py_mini_racer
        ctx = py_mini_racer.MiniRacer()
        with open('./src/dsconvert.js', 'r') as file:
            js_code = file.read()
        patch = '''
        
        class TextEncoder {
            encode(str) {
                const codeUnits = new Uint8Array(str.length);
                for (let i = 0; i < str.length; i++) {
                    codeUnits[i] = str.charCodeAt(i);
                }
                return codeUnits;
            }
        }

        class TextDecoder {
            decode(codeUnits) {
                let str = '';
                for (let i = 0; i < codeUnits.length; i++) {
                    str += String.fromCharCode(codeUnits[i]);
                }
                return str;
            }
        }
        
        '''
        ctx.eval((patch+js_code).replace("export function", "function"))
        self._ctx = ctx

    def encode(self, obj, dtype="C"):
        result = self._ctx.call('ObjectToDesyncedString', obj, dtype)
        return result

    def decode(self, dstring):
        result = self._ctx.call('DesyncedStringToObject', dstring)
        return result

class b62_pyodide:
    def __init__(self):
        print("Initializing Mini Racer")
        import dsconvert

    def encode(self, obj, dtype="C"):
        return dsconvert.ObjectToDesyncedString(obj, dtype)

    def decode(self, dstring):
        return dsconvert.DesyncedStringToObject(dstring)

# Section 10: Putting it all together

def python_to_desynced(code, environment=None):
    try: 
        if environment is None:
            import sys
            if "pyodide" in sys.modules:
                environment = "pyodide"
            else:
                environment = "python"
    
        if environment == "python":
            ds_ops = import_desynced_ops(path ="./src/desyncedexport.json")
    
        if callable(code):
            code = inspect.getsource(code)
        tree = ast.parse(code, type_comments=False)
        tree = replace_binops_with_functions(tree)
        tree = flatten_calls(tree)
        tree = convert_to_ds_call(tree)
        tree = label_frames_vars(tree)
        flow_control(tree)
        dso = create_dso_from_ast(tree)
        if environment == "pyodide":
            return json.dumps(dso)
        desyncedstring = b62(environment).encode(dso)
        return desyncedstring
    except SyntaxError as error:
        print(error)
        print(error.__dict__)
        return error
        
def python_to_desynced_pyodide(code):
    try: 
        if callable(code):
            code = inspect.getsource(code)
        tree = ast.parse(code, type_comments=False)
        if not tree.body:
            raise SyntaxError("No Code Found")
        tree = replace_binops_with_functions(tree)
        tree = flatten_calls(tree)
        tree = convert_to_ds_call(tree)
        tree = label_frames_vars(tree)
        flow_control(tree)
        dso = create_dso_from_ast(tree)
        
        return json.dumps([True, dso])
        
    except SyntaxError as error:
        return json.dumps([False, error.msg+'\n Line Number '+str(error.lineno)])
    
    except Exception as error:
        return json.dumps([False, "Uncaught exception!\nThis may be a bug in the compiler.  Please report it via Github\n\n"+str(error)])
        

'''
from astrender import astrender
from asthelpers import unparse


def python_to_desynced_detailed(code):
    if callable(code):
        code = inspect.getsource(code)
    tree = ast.parse(code, type_comments=False)
    print("As parsed:")
    astrender(tree)
    tree = replace_binops_with_functions(tree)
    print("BinOps and AugAssigns mapped to calls:")
    print(unparse(tree))
    tree = flatten_calls(tree)
    print("Calls Flattened:")
    astrender(tree)
    tree = convert_to_ds_call(tree)
    print("Convert to DS Calls")
    astprint(tree)
    tree = label_frames_vars(tree)
    print("Labeling Pass")
    astrender(tree)
    flow_control(tree)
    print("Flow Control")
    astrender(tree)
    dso = create_dso_from_ast(tree)
    print("As DSO")
    print(json.dumps(dso))
    desyncedstring = b62().encode(dso)
    return desyncedstring
'''

"Imported!"