import pytest

from ..util_test import parse, parse_delta
from pydopast.delta_module import (
    Delta, Add, Remove
)

class TestVariableDeclaration:
    def test_add_remove_variable(self):
        def add_remove_variable(variant: Delta):
            a: int = 2; b = 2
            tup = (1, (2, 3))
            x, (y, z) = tup

            variant.remove('old_var')
            x2 = y2 = x
            variant.remove('tup')
        
        expected = [
            Add(['a'], parse('a: int = 2')),
            Add(['b'], parse('b = 2')),
            Add(['tup'], parse('tup = (1, (2, 3))')),
            Add(['x', 'y', 'z'], parse('x, (y, z) = tup')),
            Remove('old_var'),
            Add(['x2', 'y2'], parse('x2 = y2 = x')),
            Remove('tup')
        ]
        
        assert expected == parse_delta(add_remove_variable)


    def test_decl_import(self):
        def add_import(variant: Delta):
            import avar
            from bvar import fun1, fun2
            import cvar as cmod
            from dvar import a1 as b1, a2
    
        expected = [
            Add(['avar'], parse('import avar')),
            Add(['fun1', 'fun2'], parse('from bvar import fun1, fun2')),
            Add(['cmod'], parse('import cvar as cmod')),
            Add(['b1', 'a2'], parse('from dvar import a1 as b1, a2'))
        ]

        assert expected == parse_delta(add_import)

    def test_import_redefine_the_first_param_fail(self):
        def import_replace_first_param(variant):
            import variant
        def from_import(variant):
            from . import variant
        
        with pytest.raises(Exception):
            parse_delta(import_replace_first_param)

        with pytest.raises(Exception):
            parse_delta(from_import)


class TestExpression:
    def test_constant_fail(self):
        def add_constant(variant: Delta):
            1
        with pytest.raises(Exception):
            parse_delta(add_constant)

    def test_non_delta_remove_call_fail(self):
        def arbitrary_fun_call(variant: Delta):
            variant.modify(afun)
        with pytest.raises(Exception):
            parse_delta(arbitrary_fun_call)

    def test_non_assign_variable_load_fail(self):
        def variable_load(variant: Delta):
            variant
        with pytest.raises(Exception):
            parse_delta(variable_load)

    def test_non_assign_expression_fail(self):
        def add_expr(variant):
            [1, 2] == [2, 3]
        with pytest.raises(Exception):
            parse_delta(add_expr)

    def test_non_assign_named_expr_fail(self):
        def add_named_expr(tmp):
            a = 2; (b := 2)
        with pytest.raises(Exception):
            parse_delta(add_named_expr)