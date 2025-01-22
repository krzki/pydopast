import enum
import ast

from dataclasses import dataclass
from ..utils import ast_util

class DeltaException(Exception):
    pass

class Target(enum.Enum):
    VARIABLE: 1
    CLASS: 2
    FUNCTION: 3

@dataclass
class LazyDeltaOperation:
    filename: str
    firstlineno: int
    type: Target

class ModuleAttribute:

    def __init__(self) -> None:
        self.body: list[ast.stmt | list[LazyDeltaOperation]] = []
        self.attr_to_id: dict[str, int | list[int | tuple[int, ClassAttribute]]] = dict()
    
    def __eq__(self, value):
        if not isinstance(value, ModuleAttribute):
            return False
        
        if len(self.body) != len(value.body) or len(self.attr_to_id) != len(value.attr_to_id):
            return False
        
        for i in range(len(self.body)):
            if not ast_util.is_equal(self.body[i], value.body[i]):
                return False
        
        return self.attr_to_id == value.attr_to_id

    def __repr__(self):
        return f'ModuleAttribute({repr(self.body)}, {repr(self.attr_to_id)})'

class CoreModuleParser(ast.NodeVisitor):
    def __init__(self):
        self.module_attrs = None
        self.top_level_assign = {
            ast.Assign: self.visit_Assign,
            ast.AnnAssign: self.visit_AnnAssign,
            ast.FunctionDef: self.visit_FunctionDef,
            ast.AsyncFunctionDef: self.visit_AsyncFunctionDef,
            ast.ClassDef: self.visit_ClassDef
        }

    def parse(self, module_ast: ast.Module):
        module_attrs = ModuleAttribute()
        module_attrs.body = module_ast.body
        self.module_attrs = module_attrs

        for idx, node in enumerate(module_ast.body):
            if type(node) in self.top_level_assign:
                self.top_level_assign[type(node)](node, idx=idx)
            else:
                self.visit(node)
        return self.module_attrs

    def visit_Assign(self, node: ast.Assign, idx = -1):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if var_name in self.module_attrs.attr_to_id:
                self.module_attrs.attr_to_id[var_name] = -1
            else:  
                self.module_attrs.attr_to_id[var_name] = idx
        else:
            self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign, idx=-1):
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            if var_name in self.module_attrs.attr_to_id:
                self.module_attrs.attr_to_id[var_name] = -1
            else:
                self.module_attrs.attr_to_id[var_name] = idx
        else:
            self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef, idx=-1):
        var_name = node.name
        if var_name in self.module_attrs.attr_to_id:
            self.module_attrs.attr_to_id[var_name] = -1
        else:
            self.module_attrs.attr_to_id[var_name] = idx

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef, idx = -1):
        var_name = node.name
        if var_name in self.module_attrs.attr_to_id:
            self.module_attrs.attr_to_id[var_name] = -1
        else:  
            self.module_attrs.attr_to_id[var_name] = idx

    def visit_ClassDef(self, node: ast.ClassDef, idx = -1):
        var_name = node.name
        if var_name in self.module_attrs.attr_to_id:
            self.module_attrs.attr_to_id[var_name] = -1
        else:
            class_attr = ClassParser().parse(node)
            self.module_attrs.attr_to_id[var_name] = (idx, class_attr)

    def visit_Delete(self, node: ast.Delete):
        for tgt_node in node.targets:
            if isinstance(tgt_node, ast.Name):
                self.module_attrs.attr_to_id[tgt_node.id] = -1

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            var_name = alias.asname if alias.asname else alias.name
            self.module_attrs.attr_to_id[var_name] = -1

    def visit_ImportFrom(self, node):
        for alias in node.names:
            var_name = alias.asname if alias.asname else alias.name
            self.module_attrs.attr_to_id[var_name] = -1

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.module_attrs.attr_to_id[node.id] = -1

class ClassParser(CoreModuleParser):
    def parse(self, class_ast: ast.ClassDef):
        self.module_attrs = ClassAttribute()
        for idx, node in enumerate(class_ast.body):
            if type(node) in self.top_level_assign:
                self.top_level_assign[type(node)](node, idx=idx)
            else:
                self.visit(node)
        return self.module_attrs

    def visit_ClassDef(self, node: ast.ClassDef, idx=-1):
        pass

class ClassAttribute(ModuleAttribute): pass