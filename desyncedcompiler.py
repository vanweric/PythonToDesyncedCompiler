import json
import ast, inspect

#Section: Helper Functions

# astpretty is much better looking, install it!
try:
    import astpretty

    # simple wrapper of the astprettyprint library
    def astprint(tree):
        astrender(tree)
        astpretty.pprint(tree, show_offsets=False)
        
except ModuleNotFoundError:
    import pprint
    def ast_to_dict(node):
        if isinstance(node, ast.AST):
            node_dict = {'type': type(node).__name__}
            for field, value in ast.iter_fields(node):
                node_dict[field] = ast_to_dict(value)
            return node_dict
        elif isinstance(node, list):
            return [ast_to_dict(item) for item in node]
        else:
            return node

    def astprint(tree):
        pprint.pprint(ast_to_dict(tree))


# Section 1: Import Desynced Ops
def import_desynced_ops(path):
    def to_function_name(string):
        # Desynced block names are typically all capitalized.  Standardize on this.
        # Obsolete instructions are marked by being surrounded by asterixes.  Replace with _ so it is a valid python function name
        result =''.join([word.capitalize() for word in string.replace('*','_').replace('(','').replace(')','').split()])
        return result
        
    with open (path, 'r') as jsonfile:
        raw_import = json.load(jsonfile)
    instructions = {to_function_name(v['name']):{**v, 'op':k} for k,v in raw_import.items() if 'name' in v.keys()}
    return instructions
    
ds_ops = import_desynced_ops("./instructions.json")
# Section: Section2

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



class DS_Call(ast.Assign):
    _fields = ('targets', 'args', 'op', 'frame', 'next')

    def __init__(self, targets, args, op):
        self.targets = targets
        self.args = args
        self.next = {}
        self.frame = -1
        self.op = op

def transform_nested_calls(tree):
    class FlatteningTransformer(ast.NodeTransformer):  
        def __init__(self):
            super().__init__()
            self.temp_count = 1
            
        def visit_Call(self, node, target=None):
            if target:
                node.targets=[target]
            
            nodelist = [DS_Call( targets=[target], args=node.args, op=node.func.id)]
            for i, arg in enumerate(node.args):
                
                if isinstance(arg, ast.Call):
                    temp_var = f'Temp_{self.temp_count}'
                    self.temp_count += 1                    
                    nodelist.insert(0, self.visit_Call(arg, ast.Name(id=temp_var, ctx=ast.Store())))
                    node.args[i] = ast.Name(id=temp_var, ctx=ast.Load())
                    
            # Return a list containing the original call node and the new call node
            def flatten(lst):
                return [item for sublist in lst for item in (flatten(sublist) if isinstance(sublist, list) else [sublist])]
            nodelist = flatten(nodelist)
            for node in nodelist:
                self.visit(node)
            return nodelist

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

    return FlatteningTransformer().visit(tree)

def label_frames(tree):
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
        node.target = None
        #print('For:')
        #astprint(node)
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
    

def create_dso_from_ast(tree):

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

        def visit_DS_Call(self, node):
            op = ds_ops[node.op]
            if self.debug:
                print('\n\n')
                print(op)
                astprint(node)
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
                        res[str(i)]=list(node.next.values())[exec_ix]+1
                        exec_ix+=1
                        
            self.dso[str(node.frame)] = res
            if self.debug:
                print(res)

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
            
    walker = DSO_from_DSCalls()
    walker.visit(tree)
    walker.parameters_block()
    walker.name_block(tree)
    dso = walker.dso
    
    return walker.dso

from py_mini_racer import py_mini_racer

def object_to_desynced_string(obj, dtype="C"):
    # Create a PyMiniRacer instance
    ctx = py_mini_racer.MiniRacer()
    
    # Load the JavaScript file
    with open('dsconvert.js', 'r') as file:
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
    '''
    # Evaluate the JavaScript code
    ctx.eval(patch+js_code)
    
    # Call the JavaScript function
    result = ctx.call('ObjectToDesyncedString', obj,dtype)

    return result
    
def python_to_desynced(code):
    if callable(code):
        code = inspect.getsource(code)
    tree = ast.parse(code, type_comments=False)

    tree = replace_binops_with_functions(tree)
    tree = transform_nested_calls(tree)
    tree = label_frames(tree)
    flow_control(tree)
    dso = create_dso_from_ast(tree)
    desyncedstring = object_to_desynced_string(dso)
    return desyncedstring









