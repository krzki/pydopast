import ast

from pydopast.utils.ast_util import is_equal

BASE_FUN = '''
def fun(a, b=2, *, c=2, d, **kw):
    print(a)
    print(b)
    return c
'''

class TestFunctionAST:
    def test_same_function_source(self):
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(BASE_FUN)

        assert is_equal(tree, tree2)

    def test_fun_args_diff(self):
        differ_args = '''
def fun(a, b=2, *, c=2, d2, **kw2):
    print(a)
    print(b)
    return c
'''
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(differ_args)

        assert not is_equal(tree, tree2)

    def test_fun_decorators_diff(self):
        differ_dec = '''
@abc
def fun(a, b=2, *, c=2, d2, **kw):
    print(a)
    print(b)
    return c
'''
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(differ_dec)

        assert not is_equal(tree, tree2)

    def test_fun_annotation_diff(self):
        differ_annot = '''
def fun(a:int, b=2, *, c=2, d2, **kw) -> int:
    print(a)
    print(b)
    return c
'''
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(differ_annot)

        assert not is_equal(tree, tree2)

    def test_fun_body_diff(self):
        differ_body = '''
def fun(a, b=2, *, c=2, d2, **kw):
    pass
'''
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(differ_body)

        assert not is_equal(tree, tree2)

    def test_async_and_sync_diff(self):
        differ_type = '''
async def fun(a, b=2, *, c=2, d2, **kw):
    print(a)
    print(b)
    return c
'''
        tree = ast.parse(BASE_FUN)
        tree2 = ast.parse(differ_type)

        assert not is_equal(tree, tree2)


class TestAssignEquality:
    def test_assign_same_source(self):
        code = '''
a = 2
b = c = [1, 2]
d, e = c
'''

        tree = ast.parse(code)
        tree2 = ast.parse(code)

        assert is_equal(tree, tree2)

    def test_one_multi_stmt_and_tuple_assign_differ(self):
        one_stmt = 'a = b = 2'
        multi_stmt = 'a = 2; b = 2'
        tuple_stmt = 'a, b = [1,2]'

        tree = ast.parse(one_stmt)
        tree2 = ast.parse(multi_stmt)
        tree3 = ast.parse(tuple_stmt)

        assert not is_equal(tree, tree2)
        assert not is_equal(tree, tree3)
        assert not is_equal(tree2, tree3)

    def test_annot_and_simple_differ(self):
        simple = 'a = 2'
        annot = 'a: int = 2'

        tree = ast.parse(simple)
        tree2 = ast.parse(annot)

        assert not is_equal(tree, tree2)


ASSIGN_FUN_CLASS = '''
a = 2
b = 2
from abc import d

@d
def my_fun() -> int:
    return 3

@my_decorator
class AB:
    def apply(self):
        return self

c = 3
'''

class TestGeneralEquality:
    def test_comments_are_ignored(self):
        no_comment = 'a = 2; b = 2'
        comment = '''
a = 2
# A comment
# Another commen
b = 2
'''
        tree = ast.parse(no_comment)
        tree2 = ast.parse(comment)

        assert is_equal(tree, tree2)

    def test_class_assign_function_same_source(self):
        tree = ast.parse(ASSIGN_FUN_CLASS)
        tree2 = ast.parse(ASSIGN_FUN_CLASS)

        assert is_equal(tree, tree2)

    def test_class_assign_function_different_source(self):
        add_fun_in_the_middle = '''
a = 2
b = 2
from abc import d

@d
def my_fun() -> int:
    return 3

def added_fun():
    pass
    
@my_decorator
class AB:
    def apply(self):
        return self

c = 3
'''
        tree = ast.parse(ASSIGN_FUN_CLASS).body
        tree2 = ast.parse(add_fun_in_the_middle).body

        assert not is_equal(tree, tree2)
