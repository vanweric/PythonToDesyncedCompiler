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

try:
    import astpretty
    def astprint(tree, show_attributes=False):
        if isinstance(tree, list):
            for node in tree:
                astprint(node, show_attributes)
        elif isinstance(tree, ast.AST):
            astpretty.pprint(tree, show_offsets=show_attributes)
        else:
            print(tree)

except ModuleNotFoundError:
    def astprint(tree, show_attributes=False):
        if isinstance(tree, list):
            for node in tree:
                astprint(node, show_attributes)
        elif isinstance(tree, ast.AST):
            print(ast.dump(tree, indent=4, annotate_fields=True, include_attributes=show_attributes))
        else:
            print(tree)

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

def flat_ast_iter_fields(node):
    for field_name, field in ast.iter_fields(node):
        if isinstance(field, list):
            for item in field:
                yield (field_name, item)
        else:
            yield (field_name, field)