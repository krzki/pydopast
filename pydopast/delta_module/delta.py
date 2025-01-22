import ast

from typing import Any
from types import ModuleType

from .operations import Operation, Add, ModifyClass, ModifyFunction, Remove

def delta_target(target: ModuleType | str):
    return lambda fun: fun

class Delta:
    def modify(self, function_or_class) -> None:
        raise NotImplementedError

    def remove(self, attribute: Any) -> None:
        raise NotImplementedError

ALLOWED_NODES = [
    ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom,
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Expr, ast.Pass
]

class DeltaParser(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.name_collector = NameCollector()

    def parse_delta(self, function_src: str) -> list[Operation]:
        tree: ast.FunctionDef = ast.parse(function_src).body[0]
        if len(tree.args.args) == 0:
            raise Exception('Delta wrapper must have at least one argument')
        
        self.res = []
        self.variant = tree.args.args[0].arg

        for node in tree.body:
            if type(node) not in ALLOWED_NODES:
                raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')
            self.visit(node)
        return self.res

    def visit_ClassDef(self, node):
        is_modify = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name) and dec.value.id == self.variant:
                is_modify = True
                break
        
        if not is_modify:
            new_op = Add([node.name], node)
        else:
            new_dec = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name) and dec.value.id == self.variant:
                    continue
                new_dec.append(dec)

            class_parser = ClassDeltaParser()
            class_modifications = class_parser.parse_class(node, self.variant)
            node.decorator_list = new_dec
            node.body = []
            new_op = ModifyClass(node.name, node, class_modifications)
        self.res.append(new_op)

    def visit_Assign(self, node):
        names = self.name_collector.collect(node.targets, self.variant)
        self.res.append(Add(names, node))

    def visit_AnnAssign(self, node):
        if not isinstance(node.target, ast.Name):
            raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')
        if node.target.id == self.variant:
            raise Exception(f'Cannot redefine the first parameter ("{self.variant}")')
        
        self.res.append(Add([node.target.id], node))

    def visit_Expr(self, node):
        is_remove = False
        remove_attr = ''
        if isinstance(node.value, ast.Call):
            fun = node.value.func
            if isinstance(fun, ast.Attribute)\
                and (isinstance(fun.value, ast.Name) and fun.value.id == self.variant)\
                and fun.attr == 'remove':

                args = node.value.args
                if len(args) == 1:
                    if isinstance(args[0], ast.Name):
                        is_remove = True
                        remove_attr = args[0].id
                    elif isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                        is_remove = True
                        remove_attr = args[0].value
        
        if not is_remove:
            raise Exception('Only calling to delta.remove expression is allowed')
        self.res.append(Remove(remove_attr))

    def visit_Import(self, node):
        self.process_import(node)
    
    def visit_ImportFrom(self, node):
        self.process_import(node)
    
    def process_import(self, node: ast.Import | ast.ImportFrom):
        names = []
        for name in node.names:
            attr_name = name.asname if name.asname else name.name
            if attr_name == self.variant:
                raise Exception(f'Cannot redefine the first parameter ("{self.variant}")')
            names.append(attr_name)
        
        self.res.append(Add(names, node))

    def visit_FunctionDef(self, node):
        self._modify_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._modify_function(node)
    
    def _modify_function(self, node: ast.AsyncFunctionDef | ast.FunctionDef):
        is_modify = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name) and dec.value.id == self.variant:
                is_modify = True
                break
        
        if not is_modify:
            new_op = Add([node.name], node)
        else:
            new_dec = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name) and dec.value.id == self.variant:
                    continue
                new_dec.append(dec)
            node.decorator_list = new_dec
            new_op = ModifyFunction(node.name, node)
        self.res.append(new_op)


class NameCollector(ast.NodeVisitor):
    def collect(self, target: list | ast.Tuple, variant):
        self.names = []
        self.variant = variant
        if isinstance(target, list):
            for item in target:
                if isinstance(item, ast.AST):
                    self.visit(item)
        elif isinstance(target, ast.AST):
            self.visit(target)
        return self.names

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Store):
            raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')
        
        if node.id == self.variant:
            raise Exception(f'Cannot redefine the first parameter ("{self.variant}")')
        self.names.append(node.id)

    def visit_Attribute(self, node):
        raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')

    def visit_Subscript(self, node):
        raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')
    
class ClassDeltaParser(DeltaParser):
    def parse_delta(self, function_src):
        return []
    
    def parse_class(self, class_ast: ast.ClassDef, variant_name: str) -> list[Operation]: 
        self.res = []
        self.variant = variant_name

        for node in class_ast.body:
            if type(node) not in ALLOWED_NODES:
                raise Exception('Top-level delta must be assignments, declarations, or delta.remove calls')
            self.visit(node)
        return self.res
    
    def visit_ClassDef(self, node):
        raise Exception('Cannot add and/or modify inner classes')