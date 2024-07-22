import json
import ast
import inspect




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
                    args=[node.left, node.right],
                    keywords=[],
                    starargs=None,
                    kwargs=None
                )
                new_node=self.visit(new_node)
                return new_node
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
                return new_node
            else:
                return node

    visitor=BinOpReplacementVisitor()
    return visitor.visit(tree)

# Section 3: Flatten Nested Calls
def flatten_calls(tree):
    class FlatteningTransformer(ast.NodeTransformer):
        def __init__(self):
            super().__init__()
            self.temp_count = 1

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

    def __init__(self, targets, args, op):
        self.targets = targets
        self.args = args
        self.next = {}
        self.frame = -1
        self.op = op

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
            return [DS_Call( targets=[target], args=node.args, op=node.func.id)]

        def visit_Assign(self, node):
            if isinstance(node.value, (ast.Name, ast.Constant, ast.Tuple)):
                # Special case for a bare Assignment - this is a Copy function, which is 'set_reg' internally
                new_node = DS_Call(targets = node.targets, args = [node.value], op = 'Copy')
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

def label_frames_vars(tree):
    def create_variable_remap(input_list):
        highest_letter = 'A'
        highest_temp_number = 0
    
        for item in input_list:
            if item.startswith('Temp_'):
                temp_number = int(item.split('_')[1])
                highest_temp_number = max(highest_temp_number, temp_number)
            elif item.isalpha():
                highest_letter = max(highest_letter, item)

        mapping = {i:i for i in input_list}
        for i in range(1, highest_temp_number + 1):
            temp_key = f'Temp_{i}'
            temp_value = chr(ord(highest_letter) + i)
            mapping[temp_key] = temp_value
    
        return mapping

    class VariableFinder(ast.NodeVisitor):
        def __init__(self):
            self.variables = {}

        def visit_Name(self, node):
            self.variables[node.id]=None

    class VariableLabeler(ast.NodeTransformer):
        def __init__(self, mapper):
            super().__init__()
            self.mapper = mapper
        
        def visit_Name(self, node):
            if node.id in self.mapper.keys():
                node.id = self.mapper[node.id]
            return node
            
    class FrameLabeler(ast.NodeTransformer):  
        def __init__(self):
            super().__init__()
            self.frame_count = 0
            
        def visit_DS_Call(self, node):
            node.frame = self.frame_count
            self.frame_count+=1
            return node

            
    finder = VariableFinder()
    finder.visit(tree)
    vars = finder.variables.keys()
    remap = create_variable_remap(vars)
    varlabeler = VariableLabeler(remap)
    tree = varlabeler.visit(tree)
    framelabeler = FrameLabeler()
    tree = framelabeler.visit(tree)
    return tree

# Section 6: Flow Control

def flow_control(tree):

    def find_first_last_DS_Call(list):
        class DSFinder(ast.NodeVisitor):
            def __init__(self):
                self.last=None
                self.first= None
    
            def visit_DS_Call(self, node):
    
                self.last = node
                if self.first is None:
                    self.first = node
    
        finder = DSFinder()
        for tree in list:
            finder.visit(tree)
        return finder.first, finder.last
    
    def flow_list(nodelist, exit=-1):
        #myexit = find_first_last_DS_Call(nodelist)
        for item, next_item in zip(nodelist, nodelist[1:] + [None]):
            lexit = exit if next_item is None else find_first_last_DS_Call([next_item])[0].frame
            if isinstance(item, DS_Call):
                item.next = {'next': lexit}
            if isinstance(item, ast.While):
                flow_While(item, lexit)
            if isinstance(item, ast.If):
                flow_If(item, lexit)
            if isinstance(item, ast.For):
                flow_For(item, lexit)
    
    def flow_While(node, exit=-1):
        flow_list(node.test)
        flow_list(node.body)
        body_first, body_last = find_first_last_DS_Call(node.body)
        test_first, test_last = find_first_last_DS_Call(node.test)
    
        test_last.next = {'next': body_first.frame, 'exit': exit}
        body_last.next = {'next': test_first.frame,}
    
    def flow_If(node, exit=-1):
        flow_list(node.test)
        flow_list(node.body)
        flow_list(node.orelse)
        body_first, body_last = find_first_last_DS_Call(node.body)
        test_first, test_last = find_first_last_DS_Call(node.test)
        orelse_first, orelse_last = find_first_last_DS_Call(node.orelse)
    
        test_last.next = {'next': exit if body_first is None else body_first.frame,
                          'else': exit if orelse_first is None else orelse_first.frame}
        if body_last:
            body_last.next = {'next': exit}
        if orelse_last:
            orelse_last.next = {'next':exit}
    
    
    def flow_For(node, exit=-1):
        target = node.target
        ''' The unparser needs the for loop to still have a valid target '''
        node.target = ast.Name(id='_', ctx=ast.Store())

        flow_list(node.body)
        flow_list(node.iter)
        body_first, body_last = find_first_last_DS_Call(node.body)
        iter_first, iter_last = find_first_last_DS_Call(node.iter)
    
        iter_last.next = {'next': body_first.frame, 
                          'exit': exit}
        body_last.next= {'next': False}
        if isinstance(target, list):
            iter_last.targets = target
        else:
            iter_last.targets = [target]
            
    # this is a real bad hack and will need to be fixed to support nested function calls.
    if isinstance(tree.body[0], ast.FunctionDef):
        return flow_list(tree.body[0].body)
    return flow_list(tree.body)

# Section 7: Import Desynced Ops

_instructions = None
def import_desynced_ops(path = None, jsonfile = None):
    global _instructions

    if not _instructions:
        def to_function_name(string):
            # Desynced block names are typically all capitalized.  Standardize on this.
            # Obsolete instructions are marked by being surrounded by asterixes.  Replace with _ so it is a valid python function name
            result =''.join([word.capitalize() for word in string.replace('*','_').replace('(','').replace(')','').split()])
            return result
        if path:
            with open (path, 'r') as jsonfile:
                raw_import = json.load(jsonfile)["instructions"]
        elif jsonfile:
            raw_import = jsonfile["instructions"]
        _instructions = {to_function_name(v['name']):{**v, 'op':k} for k,v in raw_import.items() if 'name' in v.keys()}
    return _instructions

# Section 8: Translate to DSO

def create_dso_from_ast(tree, debug=False):
    ds_ops = import_desynced_ops()
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
                    self.parameters[parameter_ix]=True
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

        def translate_exec(self, next, exec_ix):
            # This is just scaffolding at the moment
            # Needs a ton of work...
            try:
                return list(next.values())[exec_ix]+1
            except IndexError:
                return False

        def visit_DS_Call(self, node):
            op = ds_ops[node.op]
            res={}
            res['op'] = op['op']
            if node.next['next'] != node.frame+1:
                res['next'] = node.next['next']
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
                    if arg[0] == 'exec':
                        res[str(i)]= self.translate_exec(node.next, exec_ix)
                        exec_ix+=1
                        
            self.dso[str(node.frame)] = res

        def parameters_block(self):
            if len(self.parameters):
                pblock = [self.parameters.get(i+1, False) for i in range(max(self.parameters.keys()))]
                self.dso["parameters"] = pblock

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
    def __new__(cls, environment):
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
    print("Code:\n", code)
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