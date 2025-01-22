from .operations import (Add, ModifyClass, ModifyFunction, Remove,
                         VariableAlreadyExisted, VariableNotFound, InvalidModificationTarget)

from .delta import Delta, DeltaParser, delta_target

def delta_original(function):
    return function


