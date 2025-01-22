import ast

from pydopast.core_module import ModuleAttribute, CoreModuleParser, ClassAttribute


def parse(code: str) -> ModuleAttribute:
    parser = CoreModuleParser()
    return parser.parse(ast.parse(code))

def is_contain(maps: dict, key: str):
    return key in maps

class TestModuleParser:

    def test_record_all_declarations(self):
        code = """
def fun1(a):
    print(1)
    print(2)
    return 1
def fun2():
    pass
var1 = 3
"""
        module_attribute: ModuleAttribute = parse(code)
        
        assert module_attribute.attr_to_id['fun1'] == 0
        assert module_attribute.attr_to_id['fun2'] == 1
        assert module_attribute.attr_to_id['var1'] == 2

    def test_redifinition_cannot_be_modified(self):
        code = """
def fun1(a):
    pass
fun1 = 2
a = 2
"""

        module_attribute: ModuleAttribute = parse(code)
        
        assert module_attribute.attr_to_id['fun1'] == -1
        assert module_attribute.attr_to_id['a'] == 2


class TestVariableAssignment:
    def test_assignment(self):
        code = "a = 1; b=2"

        module_attribute: ModuleAttribute = parse(code)

        assert is_contain(module_attribute.attr_to_id, 'a')
        assert is_contain(module_attribute.attr_to_id, 'b')
        
        body = module_attribute.body
        a_id = module_attribute.attr_to_id['a']
        b_id = module_attribute.attr_to_id['b']

        assert isinstance(body[a_id], ast.Assign)
        assert isinstance(body[b_id], ast.Assign)

    def test_multiple_assignment_cannot_be_modified(self):
        """hide multiple assignment attribute (set it to -1)"""
        code = """a = b = 1"""
        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1

    def test_unpacking_cannot_be_modified(self):
        """hide unpacking attribute id (set it to -1)"""
        code = "a, (b, c) = [1,(2, 3)]"

        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == -1

    def test_unpacking_and_multiple_assignment_redefination_cannot_be_modified(self):
        code = """
a = 1
b = 2
a, *c = [1,4]
b = d = 3
a = 3
b = 4
"""
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == -1
        assert module_attribute.attr_to_id['d'] == -1

    def test_annotated_assignment(self):
        code = "a: int; b: int = 2"
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == 0
        assert module_attribute.attr_to_id['b'] == 1

    def test_dot_and_subscript_annotation_can_be_modified(self):
        code = "a = {'b':1}; c=[1, 2]; a.b = 2; c[1] = 4; d = 5"
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == 0
        assert module_attribute.attr_to_id['c'] == 1
        assert module_attribute.attr_to_id['d'] == 4

    def test_delete_statement_cannot_be_modified(self):
        code = "a = 1; b = 2; c = 3; del a, b"
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == 2


class TestAssignmentInsideNewBlocks:
    """All variables which are defined/redefined inside a block CANNOT be modified
    Blocks include If, For, While, Try, With, and Match."""
    
    def test_if_block(self):
        code = """
a = 2
var1 = 3
if a == 2:
    b = 3
    c = 4
    var1 = 5
else:
    e = 6
"""
        module_attribute: ModuleAttribute = parse(code)
        
        assert module_attribute.attr_to_id['a'] == 0
        assert module_attribute.attr_to_id['var1'] == -1
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == -1
        assert module_attribute.attr_to_id['e'] == -1

    def test_nested_if(self):
        code = """
a = 2
if a == 2:
    if False:
        b = 2
    else:
        a = 3
"""
        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1

    def test_for_block(self):
        code = """
for i in range(20):
    a = i + 1
"""
        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['i'] == -1
        assert module_attribute.attr_to_id['a'] == -1

    def test_while_block(self):
        code = """
i = 0
while i < 20:
    a = a_function()
    if a % 2 == 2:
        b = 3
"""

        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['i'] == 0
        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1

    def test_try_except_final_block(self):
        code = """
a = 2
try:
    b = a
    b / 0
except DivisionByZero:
    c = 3
else:
    d = 4
finally:
    e = 5
"""

        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['a'] == 0
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == -1
        assert module_attribute.attr_to_id['d'] == -1
        assert module_attribute.attr_to_id['e'] == -1

    def test_with_statement_ignore_as_variable(self):
        code = """
with open('my_file', 'r') as f:
    process_file()
    a = 2
    b = 3
"""
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['a'] == -1
        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['f'] == -1

    def test_match_block(self):
        code = """
match a:
    case str():
        b = 2
    case tuple():
        c = 3
"""
        module_attribute: ModuleAttribute = parse(code)

        assert module_attribute.attr_to_id['b'] == -1
        assert module_attribute.attr_to_id['c'] == -1


class TestFunctionDeclaration:
    def test_function_declaration(self):
        code = """
def a():
    print(3)
async def c():
    print(5)
"""
        module_attribute: ModuleAttribute = parse(code)
        assert is_contain(module_attribute.attr_to_id, 'a')
        assert is_contain(module_attribute.attr_to_id, 'c')

        body = module_attribute.body
        a_id = module_attribute.attr_to_id['a']
        c_id = module_attribute.attr_to_id['c']
        
        assert isinstance(body[a_id], ast.FunctionDef)
        assert isinstance(body[c_id], ast.AsyncFunctionDef)

    def test_ignore_any_declaration_inside_function(self):
        code = """
def a(b):
    c = 3
    def inner():
        print(3)
    return 5
"""
        module_attribute: ModuleAttribute = parse(code)

        assert is_contain(module_attribute.attr_to_id, 'a')
        assert not is_contain(module_attribute.attr_to_id, 'b')
        assert not is_contain(module_attribute.attr_to_id, 'c')
        assert not is_contain(module_attribute.attr_to_id, 'inner')


class TestClassDeclaration:
    def test_class_declaration(self):
        code = """
class MyClass:
    a = 2
    def __init__(self):
        self.abc = 2
    d = 3
"""
        module_attribute: ModuleAttribute = parse(code)

        # module attribute check
        assert is_contain(module_attribute.attr_to_id, 'MyClass')

        class_id = module_attribute.attr_to_id['MyClass'][0]
        assert isinstance(module_attribute.body[class_id], ast.ClassDef)
        
        assert not is_contain(module_attribute.attr_to_id, 'a')
        assert not is_contain(module_attribute.attr_to_id, '__init__')
        assert not is_contain(module_attribute.attr_to_id, 'd')

        # class attribute check
        class_attribute: ClassAttribute = module_attribute.attr_to_id['MyClass'][1]
        assert class_attribute != None

        assert is_contain(class_attribute.attr_to_id, 'a')
        assert is_contain(class_attribute.attr_to_id, '__init__')
        assert is_contain(class_attribute.attr_to_id, 'd')

    def test_ignore_variable_self_attribut(self):
        """self.variable are ignored"""
        code = """
class A:
    def __init__(self):
        self.a = 2
    def b():
        self.c = 3
"""
        module_attribute: ModuleAttribute = parse(code)
        assert not is_contain(module_attribute.attr_to_id, 'a')
        assert not is_contain(module_attribute.attr_to_id, 'c')
        
        class_attribute: ClassAttribute = module_attribute.attr_to_id['A'][1]
        assert class_attribute != None
        
        assert is_contain(class_attribute.attr_to_id, '__init__')
        assert is_contain(class_attribute.attr_to_id, 'b')

        assert not is_contain(class_attribute.attr_to_id, 'a')
        assert not is_contain(class_attribute.attr_to_id, 'c')


class TestDeclFromImportStmt:
    def test_import_add_declaration(self):
        code = """
import abc
import mod2 as mod2_alias

class A:
    import mod3
    
def fun1():
    import mod4
"""

        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['abc'] == -1
        assert module_attribute.attr_to_id['mod2_alias'] == -1

        assert not is_contain(module_attribute.attr_to_id, 'mod2')
        assert not is_contain(module_attribute.attr_to_id, 'mod3')
        assert not is_contain(module_attribute.attr_to_id, 'mod4')

    def test_from_import(self):
        code = """
from abc import fun1, fun2
from .. import fun3 as alias1
"""

        module_attribute: ModuleAttribute = parse(code)
        assert module_attribute.attr_to_id['fun1'] == -1
        assert module_attribute.attr_to_id['fun2'] == -1
        assert module_attribute.attr_to_id['alias1'] == -1

        assert not is_contain(module_attribute.attr_to_id, 'abc')
        assert not is_contain(module_attribute.attr_to_id, 'fun3')