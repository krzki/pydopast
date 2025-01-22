import ast
import inspect
import pytest

from pydopast.delta_module import Add, VariableAlreadyExisted
from pydopast.core_module import ModuleAttribute
from pydopast.core_module.parsers import CoreModuleParser

from ..util_test import parse, fix_indent_from_str

class TestAddVariable():
    def test_new_single_variable(self):
        code = 'var1: int = 2'
        add = Add(['var1'], parse(code))
        cm: ModuleAttribute = ModuleAttribute()

        add.apply(cm)

        expected_cm = CoreModuleParser().parse(ast.parse(code))
        assert expected_cm == cm

    def test_new_multiple_variable(self):
        code = 'v1 = v2 = v3 = 3'
        add = Add(['v1', 'v2', 'v3'], parse(code))
        cm = ModuleAttribute()

        add.apply(cm)

        expected_cm = CoreModuleParser().parse(ast.parse(code))

        assert expected_cm == cm

    def test_add_duplicate_variable_fail(self):
        tree = parse('v = 1')
        add = Add(['v'], tree)

        cm = ModuleAttribute()
        cm.attr_to_id['v'] = 0
        cm.body.append(parse('v = 1'))

        with pytest.raises(VariableAlreadyExisted):
            add.apply(cm)

    def test_add_function(self):
        code = '''
            @cache
            def new_fun(a, b, c):
                pass
            '''            
        
        add = Add(['new_fun'], parse(code))
        cm = ModuleAttribute()
        add.apply(cm)

        expected_cm = CoreModuleParser().parse(ast.parse(fix_indent_from_str(code)))
        assert expected_cm == cm

    def test_add_class(self):
        class C: pass
        class NewClass(C):
            def __init__(self): pass
            def m1(self): pass

        code = fix_indent_from_str(inspect.getsource(NewClass))
        add = Add(['NewClass'], parse(code))
        cm = ModuleAttribute()
        add.apply(cm)

        expected_cm = CoreModuleParser().parse(ast.parse(code))
        assert expected_cm == cm