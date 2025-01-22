'''
TODO: Consider to perform deepcopy, (parallel/multiprocessing cases)
'''


import ast
import copy

from abc import ABC, abstractmethod
from pydopast.utils import ast_util
from pydopast.core_module import ModuleAttribute, ClassParser

class VariableAlreadyExisted(Exception): pass
class VariableNotFound(Exception): pass
class InvalidModificationTarget(Exception):
    def __init__(self, expected, actual):
        super().__init__(f'Invalid delta modification target: "{actual}" is not a "{expected}"')

class Operation(ABC):
    @abstractmethod
    def apply(self, core_module):
        raise NotImplementedError

class Add(Operation):
    def __init__(self, names: list[str], tree: ast.stmt):
        self.names = names
        self.tree = tree

    def apply(self, core_module: ModuleAttribute):
        body_entry = len(core_module.body) if len(self.names) == 1 else -1
        
        if body_entry != -1 and isinstance(self.tree, ast.ClassDef):
            body_entry = (body_entry, ClassParser().parse(self.tree))

        for name in self.names:
            if name in core_module.attr_to_id:
                raise VariableAlreadyExisted(f'Variable "{name}" has been defined in the core module')
            core_module.attr_to_id[name] = body_entry
        
        core_module.body.append(self.tree)            

    def __eq__(self, value):
        if not value:
            return False
        
        if not isinstance(value, Add):
            return False

        return (self.names == value.names) and ast_util.is_equal(self.tree, value.tree)

    def __repr__(self):
        return f'Add({self.names}, {ast.dump(self.tree)})'

class ModifyFunction(Operation):
    def __init__(self, function_name: str, tree: ast.FunctionDef | ast.AsyncFunctionDef):
        self.fun_name = function_name
        self.tree = tree

        self.need_original = False
        checker = OriginalSearch()
        for node in tree.body:
            if checker.need_original(node):
                self.need_original = True
                break                

    def apply(self, core_module: ModuleAttribute):
        if self.fun_name not in core_module.attr_to_id:
            raise VariableNotFound(f'No variable named "{self.fun_name}" in the core module')

        fun_id = core_module.attr_to_id[self.fun_name]
        original_tree = core_module.body[fun_id]
        if not (isinstance(original_tree, ast.FunctionDef) or (isinstance(original_tree, ast.AsyncFunctionDef))):
            raise InvalidModificationTarget('Function', self.fun_name)

        if not self.need_original:
            core_module.body[fun_id] = self.tree
        else:
            #TODO: Make copy original function lazy
            original_fun = self.__clone_function_header(original_tree)
            original_fun.body = [
                original_tree,
                self.__fun_arg_def_to_call(original_tree.args)
            ]
            
            old_body = self.tree.body
            self.tree.body = None
            new_tree= copy.deepcopy(self.tree)
            
            new_body = [original_fun]
            for body in old_body:
                new_body.append(body)

            new_tree.body = new_body
            self.tree.body = old_body
            core_module.body[fun_id] = new_tree

        return core_module

    def __clone_function_header(self, function: ast.FunctionDef | ast.AsyncFunctionDef):
        if isinstance(function, ast.FunctionDef):
            return ast.FunctionDef(
                name='original', args=function.args, 
                returns=function.returns, type_params=function.type_params,
                type_comment=function.type_comment
            )
        else:
            return ast.AsyncFunctionDef(
                name='original', args=function.args, 
                returns=function.returns, type_params=function.type_params,
                type_comment=function.type_comment
            )
    
    def __fun_arg_def_to_call(self, arguments: ast.arguments):
        args = []
        for arg in arguments.args:
            args.append(ast.Name(arg.arg, ctx=ast.Load()))
        if arguments.vararg:
            args.append(
                ast.Starred(
                    value=ast.Name(arguments.vararg.arg, ctx=ast.Load()),
                    ctx=ast.Load()
                )
            )
        keywords = []
        for kw in arguments.kwonlyargs:
            keywords.append(
                ast.keyword(
                    arg=kw.arg, value=ast.Name(id=kw.arg, ctx=ast.Load())
                )
            )
        if arguments.kwarg:
            keywords.append(
                ast.keyword(value=ast.Name(id=arguments.kwarg.arg, ctx=ast.Load()))
            )

        return ast.Call(
            func=ast.Name(id=self.fun_name, ctx=ast.Load()),
            args=args, keywords=keywords
        )

    def __eq__(self, value):
        if not value:
            return False
        
        if not isinstance(value, ModifyFunction):
            return False

        return (self.fun_name == value.fun_name) and ast_util.is_equal(self.tree, value.tree)
    
    def __repr__(self):
        return f'ModifyFunction({self.fun_name}, {ast.dump(self.tree)})'

class ModifyClass(Operation):
    def __init__(self, class_name: str, tree: ast.ClassDef, modifications: list[Operation]):
        '''tree has empty "body" attribute'''

        self.class_name = class_name
        self.mods = modifications
        self.tree = tree

    def apply(self, core_module):
        return core_module

    def __eq__(self, value):
        if not value:
            return False
        
        if not isinstance(value, ModifyClass):
            return False

        return self.class_name == value.class_name \
                and self.mods == value.mods \
                and ast_util.is_equal(self.tree, value.tree)

    def __repr__(self):
        return f'ModifyClass({self.class_name}, {self.mods}, {ast.dump(self.tree)})'

class Remove(Operation):
    def __init__(self, name: str):
        self.name = name

    def apply(self, core_module: ModuleAttribute):
        if self.name not in core_module.attr_to_id:
            raise VariableNotFound(f'No variable "{self.name}" in the core module')
        
        body_id = core_module.attr_to_id[self.name]
        core_module.body[body_id] = None
        del core_module.attr_to_id[self.name]
        return core_module

    def __eq__(self, value):
        if not value:
            return False
        
        if not isinstance(value, Remove):
            return False
    
        return self.name == value.name

    def __repr__(self):
        return f'Remove({self.name})'
    

class OriginalSearch(ast.NodeVisitor):
    def need_original(self, node):
        self.orignal_name = 'original'
        return self.visit(node) == True

    def visit_Name(self, node):
        if node.id == self.orignal_name:
            if isinstance(node.ctx, ast.Store):
                return False
            else:
                return True
        return False

    def visit_FunctionDef(self, node):
        if node.name == self.orignal_name:
            return False

    def visit_AsyncFunctionDef(self, node):
        if node.name == self.orignal_name:
            return False

    def visit_ClassDef(self, node):
        if node.name == self.orignal_name:
            return False

    def visit_Import(self, node):
        for name in node.names:
            var_name = name.asname if name.asname else name.name
            if var_name == self.orignal_name:
                return False
    
    def visit_ImportFrom(self, node):
        for name in node.names:
            var_name = name.asname if name.asname else name.name
            if var_name == self.orignal_name:
                return False