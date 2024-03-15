import ast
import astpretty

class ExcludeValuesWrapper:
    def __init__(self, func, excluded_values):
        self.func = func
        self.excluded_values = set(excluded_values)

    def __call__(self, *args, **kwargs):
        result = self.func(*args, **kwargs)
        return (val for val in result if val not in self.excluded_values)

astpretty._fields = ExcludeValuesWrapper(astpretty._fields, ['keywords','type_comment','type_ignores'])

# simple wrapper of the astprettyprint library
def astprint(tree):
    astpretty.pprint(tree, show_offsets=False)

def unparse(tree):
    class FixLineNumbers(ast.NodeVisitor):
        def __init__(self):
            self.current_line = 1

        def generic_visit(self, node):
            """Called if no explicit visitor function exists for a node."""
            node.lineno = self.current_line
            self.current_line += 1
            super().generic_visit(node)

    fixer = FixLineNumbers()
    fixer.visit(tree)
    return ast.unparse(tree)

