from ..util_test import parse, parse_delta
from pydopast.delta_module import (
    Delta, Add, ModifyFunction, Remove
)

def base_delta(variant: Delta):    
    from functools import cache

    @cache
    def new_fun(p1, p2):
        other_fun(p1)
        fun2(p2)
        return p2

expected_base_delta = [
    Add(['cache'], parse('from functools import cache')),
    Add(['new_fun'], parse('''
            @cache
            def new_fun(p1, p2):
                other_fun(p1)
                fun2(p2)
                return p2
            '''
        )
    )
]


class TestFunctionModification:
    '''All tests (except multiple operations) in this class will add more operations to "base_delta"'''

    def test_add_function(self):
        assert expected_base_delta == parse_delta(base_delta)

    def test_remove_function(self):
        def remove_fun(variant: Delta):
            variant.remove('new_fun')
        assert [Remove('new_fun')] == parse_delta(remove_fun)

    def test_modify_function_body_and_params(self):
        def modify_body_and_params(variant: Delta):
            @variant.modify
            def new_fun(p1, p2, new_param):
                print('modified_fun')
                return original(p1, p2)
            
        modified_body_and_params = [
            ModifyFunction('new_fun',
            parse(
                '''
                def new_fun(p1, p2, new_param):
                    print('modified_fun')
                    return original(p1, p2)
                '''
            ))
        ]

        assert modified_body_and_params == parse_delta(modify_body_and_params)

    def test_add_and_remove_decorators(self):
        def modify_decorators(variant: Delta):
            @variant.modify
            @adec1
            @adec2
            @cache
            def new_fun(p1, p2):
                return original(p1, p2)
            
        modified_decorators = [
            ModifyFunction(
                'new_fun',
                parse(
                    '''
                    @adec1
                    @adec2
                    @cache
                    def new_fun(p1, p2):
                        return original(p1, p2)
                    '''
                )
            )   
        ]

        assert modified_decorators == parse_delta(modify_decorators)

    def test_multiple_operations(self):
        def multiple_operations(variant: Delta):
            def new_fun(a, b: int = 2): pass
            var1: int = 2
            variant.remove('avar')
            variant.remove('afun')
            
            @adec
            def fun2() -> None: pass

            @dec2
            @variant.modify
            @adec2
            async def new_fun(a): pass

            variant.remove('fun2')

        expected_multiple_operations = [
            Add(['new_fun'], parse('def new_fun(a, b: int = 2): pass')),
            Add(['var1'], parse('var1:int = 2')),
            Remove('avar'),
            Remove('afun'),
            Add(['fun2'], parse(
                '''
                @adec
                def fun2() -> None: pass
                '''
            )),
            ModifyFunction('new_fun', parse(
                '''
                @dec2
                @adec2
                async def new_fun(a): pass
                '''
            )),
            Remove('fun2')
        ]

        assert expected_multiple_operations == parse_delta(multiple_operations)