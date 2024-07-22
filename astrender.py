import ast
import pydot
from IPython.display import Image, display


def astrender_simple(tree):
    class ASTRenderer:
        def __init__(self):
            self.graph = pydot.Dot(graph_type='digraph')
            self.node_counter = 1

        def visit(self, node):
            visitor_name = f'visit_{node.__class__.__name__}'
            visitor_method = getattr(self, visitor_name, self.generic_visit)
            return visitor_method(node)

        def node_id(self, node):
            id = getattr('node_id', node, None)
            if id is None:
                node.node_id = self.node_counter
                self.node_counter +=1
            return node.node_id
                
    
        def generic_visit(self, node, label=None, ignore=[], *args, **kwargs):
            label = node.__class__.__name__
            current_node_id = self.node_id(node)

            
            nodeobject = pydot.Node(current_node_id, label=label, shape="box")
            self.graph.add_node(nodeobject)


            for field in node._fields:
                value = getattr(node, field)
                if isinstance(value, ast.AST):
                    self.visit(value)
                elif isinstance(value, list):
                    for node in value:
                        self.visit(node)
                else:
                    pass
                    

            '''    
            for field, value in ast.iter_fields(node):
                if field in ignore:
                    continue
                if isinstance(value, list):
                    sg = pydot.Cluster(graph_name = f"cluster{self.cluster_counter}", label = '', style = 'dotted')
                    self.graph.add_subgraph(sg)
                    self.cluster_counter+=1
                    
                    for item in value:
                        if isinstance(item, ast.AST):
                            child_node_id = self.node_counter
                            child = self.visit(item)  
                            if value[0] is item:  # or (not isinstance(value[0], DS_Call))
                                self.graph.add_edge(pydot.Edge(current_node_id, child_node_id, label=field))
                            sg.add_node(child)
   
                elif isinstance(value, ast.AST):
                    child_node_id = self.node_counter
                    self.visit(value)
                    self.graph.add_edge(pydot.Edge(current_node_id, child_node_id, label=field))
            
            return nodeobject
            '''




        def jupyter_view(self):
            im = Image(self.graph.create_png())
            display(im)
    
  
    visitor = ASTRenderer()
    visitor.visit(tree)
    visitor.jupyter_view()


def astrender(tree):
    class ASTRenderer(ast.NodeVisitor):
        def __init__(self):
            self.graph = pydot.Dot(graph_type='digraph',
                strict=True,
                constraint=True,
                concentrate=True,
                splines="polyline",)
            self.node_counter = 0
            self.cluster_counter = 0

        def visit(self, node, *args, **kwargs):
            visitor_name = f'visit_{node.__class__.__name__}'
            visitor_method = getattr(self, visitor_name, self.generic_visit)
            return visitor_method(node, *args, **kwargs)
    
        def generic_visit(self, node, label=None, ignore=[], *args, **kwargs):
            current_node_id = self.node_counter
            label = label if label else node.__class__.__name__
            nodeobject = pydot.Node(current_node_id, label=label, shape="box")
            self.graph.add_node(nodeobject)
            self.node_counter += 1
    
            if ignore is True:
                return nodeobject
    
            for field, value in ast.iter_fields(node):
                if field in ignore:
                    continue
                if isinstance(value, list):
                    sg = pydot.Cluster(graph_name = f"cluster{self.cluster_counter}", label = '', style = 'dotted')
                    self.graph.add_subgraph(sg)
                    self.cluster_counter+=1
                    
                    for item in value:
                        if isinstance(item, ast.AST):
                            child_node_id = self.node_counter
                            child = self.visit(item)  
                            if value[0] is item:  # or (not isinstance(value[0], DS_Call))
                                self.graph.add_edge(pydot.Edge(current_node_id, child_node_id))
                            sg.add_node(child)
   
                elif isinstance(value, ast.AST):
                    child_node_id = self.node_counter
                    self.visit(value)
                    self.graph.add_edge(pydot.Edge(current_node_id, child_node_id))
            
            return nodeobject

        def jupyter_view(self):
            im = Image(self.graph.create_png())
            display(im)
    
        def visit_Name(self, node, *args, **kwargs):
            return self.generic_visit(node, label = f'Name: {node.id}', ignore = True, *args, **kwargs)
    
        def visit_Constant(self, node, *args, **kwargs):
            return self.generic_visit(node, label = f'Constant: {node.value}', ignore = True, *args, **kwargs)
    
        def visit_BinOp(self, node, *args, **kwargs):
            return self.generic_visit(node, label = f'BinOp: {type(node.op).__name__}', ignore = ['op'], *args, **kwargs)
            
        def visit_Call(self, node, *args, **kwargs):
            if isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                call_name = node.func.id
            else:
                print("ERROR")
            return self.generic_visit(node, label = f'Call: {call_name}', ignore = ['func'], *args, **kwargs)

        def visit_DS_Call(self, node, *args, **kwargs):
            return self.generic_visit(node, label = f'DS_Call: {node.op}\n {node.frame}-->{node.next}', *args, **kwargs)#, ignore = ['func'])

        def visit_arg(self, node, *args, **kwargs):
            return self.generic_visit(node, label = f'arg: {node.arg}', *args, **kwargs)

    if callable(tree):
        tree = inspect.getsource(tree)
    visitor = ASTRenderer()
    visitor.visit(tree)
    visitor.jupyter_view()
    return visitor.graph



  