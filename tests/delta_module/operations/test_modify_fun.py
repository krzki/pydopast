import ast
import inspect
import pytest

from pydopast.delta_module import VariableNotFound, ModifyFunction, InvalidModificationTarget
from pydopast.core_module import ModuleAttribute
from pydopast.core_module.parsers import CoreModuleParser

from ..util_test import parse, fix_indent_from_str

class TestModifyFunction:
    def test_modify_function_no_original(self):
        code = '''
            a = 2
            def f(): pass
            def m(): pass
            b = 2
        '''
        code = fix_indent_from_str(code)

        expected_cm = CoreModuleParser().parse(ast.parse(code))
        
        f_id = expected_cm.attr_to_id['f']
        expected_cm.body[f_id] = parse('def f(p1, p2): print(p1); return p1 + p2')

        cm = CoreModuleParser().parse(ast.parse(code))
        mod = ModifyFunction('f', parse('def f(p1, p2): print(p1); return p1 + p2'))
        mod.apply(cm)

        assert expected_cm == cm


    def test_modify_non_function_variable_fail(self):
        code = 'a = 2'

        cm = CoreModuleParser().parse(ast.parse(code))
        mod = ModifyFunction('a', parse('def a(): pass'))

        with pytest.raises(InvalidModificationTarget):
            mod.apply(cm)


    def test_modify_not_existed_function(self):
        cm = ModuleAttribute()
        mod = ModifyFunction('a', parse('def a(): pass'))

        with pytest.raises(VariableNotFound):
            mod.apply(cm)


    def test_modify_params(self):
        code = 'def fun(): pass'
        cm = CoreModuleParser().parse(ast.parse(code))
        
        mod_code = '''def fun(p1: int, p2: str = 'a') -> int: print(p1, p2); return p1 + 1'''
        mod = ModifyFunction('fun', parse(mod_code))
        expected_cm = CoreModuleParser().parse(ast.parse(mod_code))
        mod.apply(cm)

        assert expected_cm == cm
    

    def test_modify_decorators(self):
        code = 'def fun(): pass'
        cm = CoreModuleParser().parse(ast.parse(code))
        
        mod_code = '''
            @adec1
            @adec2
            def fun(p1: int, p2: str = 'a') -> int:
                print(p1, p2)
                return p1 + 1
            '''
        mod_code = fix_indent_from_str(mod_code)
        mod = ModifyFunction('fun', parse(mod_code))
        expected_cm = CoreModuleParser().parse(ast.parse(fix_indent_from_str(mod_code)))
        mod.apply(cm)

        assert expected_cm == cm


    def test_modify_with_original(self):
        code = '''
        @adec
        @cache
        def fun(p1, p2):
            a = 2
            a += heavy_fun(p1)
            return a + p2 
        '''
        code = fix_indent_from_str(code)

        mod_code = '''
        @delta.modify
        def fun(p1, p2):
            b = p1 + p2
            prev_val = original(b, 2 * b)
            return prev_val + p2
        '''
        mod_code = fix_indent_from_str(mod_code)

        cm = CoreModuleParser().parse(ast.parse(code))
        mod = ModifyFunction('fun', parse(mod_code))

        expected_cm = CoreModuleParser().parse(ast.parse(fix_indent_from_str(
            '''
            def fun(p1, p2):
                def original(p1, p2):
                    @adec
                    @cache
                    def fun(p1, p2):
                        a = 2
                        a += heavy_fun(p1)
                        return a + p2
                    
                b = p1 + p2
                prev_val = original(b, 2 * b)
                return prev_val + p2
            '''
        )))
        
        mod.apply(cm)
        assert expected_cm == cm