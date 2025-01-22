import ast
import inspect
from pydopast.delta_module.delta import DeltaParser

def parse_delta(new_delta):
    parser = DeltaParser()
    src = get_source(new_delta)
    return parser.parse_delta(src)

def parse(code: str):
    if not isinstance(code, str):
        code = get_source(code)
    else:
        code = fix_indent_from_str(code)
        
    return ast.parse(code).body[0]

def parse_class_header(class_decl):
    code = class_decl
    if not isinstance(class_decl, str):
        code = get_source(class_decl)
    else:
        code = fix_indent_from_str(code)

    class_tree: ast.ClassDef = ast.parse(code).body[0]
    class_tree.body = []
    return class_tree

def get_source(delta_object):
    src_lines = inspect.getsourcelines(delta_object)[0]
    src = []

    if len(src_lines) > 0:
        first_char = len(src_lines[0])
        for i in range(len(src_lines[0])):
            if src_lines[0][i] != ' ':
                first_char = i
                break
        for line in src_lines:
            src.append(line[first_char:])
    return ''.join(src)

def fix_indent_from_str(code: str):
    # TODO: Fix case \t\t\t \n \t\t def ....

    code = code.strip('\n')
    indent_len = 0
    for i in range(len(code)):
        if code[i] not in '\n\t ':
            indent_len = i
            break
    code = code.replace('\n' + ' ' * indent_len,'\n')[indent_len:]
    return code
