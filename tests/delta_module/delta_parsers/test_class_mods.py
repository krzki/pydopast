import pytest

from ..util_test import parse, parse_delta, parse_class_header
from pydopast.delta_module import (
    Delta, Add, ModifyClass,
    ModifyFunction, Remove, DeltaParser
)
'''
TODO: 
    1. Use specific Exception for parser fail
'''

def base_delta(variant: Delta):
    @aclassdec
    class NewClass(Base1, Base2, metaclass=Meta1):
        field1 = 1

        def __init__(self, f2):
            self.f2 = f2

        @staticmethod
        def method0(a):
            return 1

        def method1(self, b):
            return self.f2 + b

expected_base_delta = [
    Add(['NewClass'], parse(
        '''
        @aclassdec
        class NewClass(Base1, Base2, metaclass=Meta1):
            field1 = 1

            def __init__(self, f2):
                self.f2 = f2

            @staticmethod
            def method0(a):
                return 1

            def method1(self, b):
                return self.f2 + b
        '''
    ))
]


class TestClassModifications:
    def test_simple_add(self):
        parser = DeltaParser()
        assert expected_base_delta == parse_delta(base_delta)

    def test_remove_class(self):
        def remove_class(variant: Delta):
            variant.remove('NewClass')

        assert [Remove('NewClass')] == parse_delta(remove_class)

    def test_empty_modify(self):
        def empty_delta(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1): pass

        empty_mod = [
            ModifyClass(
                'NewClass', modifications=[], 
                tree=parse_class_header('class NewClass(Base1, Base2, metaclass=Meta1): pass')
            )
        ]
        assert empty_mod == parse_delta(empty_delta)

    def test_field_add_remove(self):
        def field_mods(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1):
                field2 = 'abc'
                field3 = 'def'
                variant.remove('field1')

        field_ops = [
            ModifyClass(
                'NewClass',
                tree=parse_class_header("class NewClass(Base1, Base2, metaclass=Meta1): pass"),
                modifications=[
                    Add(['field2'], parse("field2 = 'abc'")),
                    Add(['field3'], parse("field3 = 'def'")),
                    Remove('field1')
                ]
            )
        ]
        
        assert field_ops == parse_delta(field_mods)

    def test_method_add_remove(self):
        def add_remove_methods(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1):
                variant.remove('method0')
                
                @adec
                def new_method(self, p1, p2):
                    execute_fun(p1, p2)
                
                def method0():
                    return 20

                variant.remove('method1')

        method_ops = [
            ModifyClass(
                'NewClass',
                tree=parse_class_header('class NewClass(Base1, Base2, metaclass=Meta1): pass'),
                modifications=[
                    Remove('method0'),
                    Add(['new_method'], parse(
                        '''
                        @adec
                        def new_method(self, p1, p2):
                            execute_fun(p1, p2)
                        '''
                    )),
                    Add(['method0'], parse(
                        '''
                        def method0():
                            return 20
                        '''
                    )),
                    Remove('method1')
                ]
            )
        ]

        assert method_ops == parse_delta(add_remove_methods)
    
    def test_modify_method(self):
        def modify_methods(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1):
                @variant.modify
                def __init__(self, f2, f3):
                    original(f2)
                    self.f3 = f3

                @variant.modify
                def method1(self, b):
                    return b

        modify_method_ops = [
            ModifyClass(
                class_name='NewClass',
                tree=parse_class_header('class NewClass(Base1, Base2, metaclass=Meta1): pass'),
                modifications=[
                    ModifyFunction(
                        '__init__',
                        parse('def __init__(self, f2, f3): original(f2); self.f3 = f3')
                    ),
                    ModifyFunction(
                        'method1',
                        parse('def method1(self, b): return b')
                    )
                ]
            )
        ]

        assert modify_method_ops == parse_delta(modify_methods)

    def test_add_inner_class_fail(self):
        def add_new_inner_class(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1):
                class InnerClassNew:
                    pass

        with pytest.raises(Exception):
            parse_delta(add_new_inner_class)

    def test_modify_inner_class_fail(self):
        '''assume the inner class has been defined'''
        def modify_inner_class(variant: Delta):
            @variant.modify
            class NewClass(Base1, Base2, metaclass=Meta1):
                @variant.modify
                class InnerClassNew:
                    pass

        with pytest.raises(Exception):
            parse_delta(modify_inner_class)

    def test_modify_decorator(self):
        def modify_decs(variant: Delta):
            @variant.modify
            @adec
            @adec2
            class NewClass(Base1, Base2, metaclass=Meta1): pass
        
            @variant.modify
            @adec
            class NewClass(Base1, Base2, metaclass=Meta1): pass
        
        expected_mods = [
            ModifyClass(
                'NewClass', modifications=[],
                tree=parse_class_header(
                    '''
                    @adec
                    @adec2
                    class NewClass(Base1, Base2, metaclass=Meta1): pass
                    '''
                )
            ),
            ModifyClass(
                'NewClass', modifications=[],
                tree=parse_class_header(
                    '''
                    @adec
                    class NewClass(Base1, Base2, metaclass=Meta1): pass
                    '''
                )
            )
        ]

        assert expected_mods == parse_delta(modify_decs)


    def test_modify_params(self):
        def modify_params(variant: Delta):
            @variant.modify
            class NewClass(NewBase): pass

            @variant.modify
            class NewClass(Base2): pass

            @variant.modify
            class NewClass(metaclass=Meta2): pass
        
        expected = [
            ModifyClass('NewClass', parse_class_header('class NewClass(NewBase): pass'), []),
            ModifyClass('NewClass', parse_class_header('class NewClass(Base2): pass'), []),
            ModifyClass('NewClass', parse_class_header('class NewClass(metaclass=Meta2): pass'), []),
        ]

        assert expected == parse_delta(modify_params)


    def test_multiple_operations(self):
        def multi_delta(variant: Delta):
            @adec
            class C1(B1, metaclass=Meta1):
                class InnerC: pass
                def __init__(self, p1:str, p2=3) -> None: pass
                def m1(self, p2: int) -> int: return p2
            
            class C2: pass

            @variant.modify
            @adec2
            class C2(C1):
                def __init__(self): pass

            @variant.modify
            @adec
            class C1(B1, metaclass=Meta1):
                @staticmethod
                def m3(p1, p2): pass

                @mdec1
                @mdec2
                def m4(p1: str): pass
            
            variant.remove(C2)

            @variant.modify
            class C1(B1, metaclass=Meta1):
                variant.remove('m3')

                @variant.modify
                @mdec1
                @mdec2
                def m4(p2: int, p3: str): pass

        expected_multiple_delta = [
            Add(['C1'], parse(
                '''
                @adec
                class C1(B1, metaclass=Meta1):
                    class InnerC: pass
                    def __init__(self, p1:str, p2=3) -> None: pass
                    def m1(self, p2: int) -> int: return p2
                '''
            )),
            Add(['C2'], parse('class C2: pass')),
            ModifyClass(
                'C2', 
                modifications=[Add(['__init__'], parse('def __init__(self): pass'))],
                tree=parse_class_header(
                    '''
                    @adec2
                    class C2(C1): pass
                    '''
                )
            ),
            ModifyClass(
                'C1',
                modifications=[
                    Add(['m3'], parse(
                        '''
                        @staticmethod
                        def m3(p1, p2): pass
                        '''
                    )),
                    Add(['m4'], parse(
                        '''
                        @mdec1
                        @mdec2
                        def m4(p1: str): pass
                        '''
                    ))
                ],
                tree=parse_class_header(
                    '''
                    @adec
                    class C1(B1, metaclass=Meta1): pass
                    '''
                )
            ),
            Remove('C2'),
            ModifyClass(
                'C1',
                modifications=[
                    Remove('m3'),
                    ModifyFunction('m4', parse(
                        '''
                        @mdec1
                        @mdec2
                        def m4(p2: int, p3: str): pass
                        '''
                    ))
                ],
                tree=parse_class_header('class C1(B1, metaclass=Meta1): pass')
            )
        ]

        assert expected_multiple_delta == parse_delta(multi_delta)