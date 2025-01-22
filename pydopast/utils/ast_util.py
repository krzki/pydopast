import ast

def is_equal(ast1: ast.AST | list[ast.AST], ast2: ast.AST | list[ast.AST]):
    '''
    Compare AST Node based on their _fields value.
    
    The default AST equal tests use all fields in the AST objects
    '''

    if (not ast1) and (not ast2):
        return True
    if not ast1:
        return False
    if not ast2:
        return False
    
    if type(ast1) != type(ast2):
        return False
    
    if isinstance(ast1, ast.AST):
        if len(ast1._fields) != len(ast2._fields):
            return False

        for key in ast1._field_types.keys():
            if key not in ast2._field_types:
                return False
            if not is_equal(getattr(ast1, key), getattr(ast2, key)):
                return False
        return True
    
    if isinstance(ast1, list):
        if len(ast1) != len(ast2):
            return False
        
        for i in range(len(ast1)):
            if not is_equal(ast1[i], ast2[i]):
                return False
        return True

    return ast1 == ast2