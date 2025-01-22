import pytest

from ..util_test import parse, parse_delta
from pydopast.delta_module  import (
    Delta, Add, Remove
)

class TestAddBlockFail:
    '''Blocks defined outside a function/method throw an exception'''
    def test_if_block_fail(self):
        def delta_if(variant: Delta):
            if True:
                a = 2
        
        with pytest.raises(Exception):
            parse_delta(delta_if)


    def test_with_block(self):
        def with_block(variant: Delta):
            with open('file', 'r') as f:
                pass

        with pytest.raises(Exception):
            parse_delta(with_block)


    def test_loop_block(self):
        def for_loop(variant: Delta):
            for i in range(20): pass

        def while_loop(variant: Delta):
            i = 2
            while i < 2: pass
        
        with pytest.raises(Exception):
            parse_delta(for_loop)

        with pytest.raises(Exception):
            parse_delta(while_loop)


    def test_try_block(self):
        def try_block(variant: Delta):
            try: may_throw()
            except AnException: pass
            finally: pass
        
        with pytest.raises(Exception):
            parse_delta(try_block)


    def test_match_block(self):
        def match_block(variant: Delta):
            x = 2
            match x:
                case int():
                    a = 2
                case tuple():
                    b = 2
        
        with pytest.raises(Exception):
            parse_delta(match_block)

class TestNonAssignFail:
    '''Expressions defined outside a function/method throw an exception (except Function call from the first argument)'''

    def test_function_call_in_assign_succeed(self):
        def fun_call(variant: Delta):
            def fun1(): pass
            a = fun1()
        
        expected = [
            Add(['fun1'], parse('def fun1(): pass')),
            Add(['a'], parse('a = fun1()'))
        ]
        
        assert expected == parse_delta(fun_call)


    def test_function_call_without_assign_fail(self):
        def fun_call(variant: Delta):
            def fun1(): pass
            fun1()
        
        with pytest.raises(Exception):
            parse_delta(fun_call)


    def test_class_instantation_without_assign_fail(self):
        def class_inst(variant: Delta):
            class C: pass
            C()
        
        with pytest.raises(Exception):
            parse_delta(class_inst)


    def test_named_expression_without_assign_fail(self):
        def named_expr(variant: Delta):
            (x := 2)
        
        with pytest.raises(Exception):
            parse_delta(named_expr)


class TestDeltaParam:
    '''First Param in Delta Operation is used as an indicator during parsing'''
    def test_cannot_redefine_the_first_param(self):
        def redefine_first_param(variant, p2, p3):
            variant = 2
        
        with pytest.raises(Exception):
            parse_delta(redefine_first_param)


    def test_wrapper_must_have_at_least_one_arg(self):
        def no_arg(): pass

        with pytest.raises(Exception):
            parse_delta(no_arg)


    def test_allow_calling_remove_method_first_param(self):
        def calling_remove(variant, p2):
            variant.remove('attr')
        
        assert [Remove('attr')] == parse_delta(calling_remove)


    def test_calling_method_other_than_remove_fail(self):
        def calling_non_remove(variant):
            variant.add('attr')
        
        with pytest.raises(Exception):
            parse_delta(calling_non_remove)