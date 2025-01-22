import pytest

from pydopast.delta_module import Remove, VariableNotFound
from pydopast.core_module import ModuleAttribute

from ..util_test import parse

class TestRemove:
    def test_remove_attribute(self):
        cm = ModuleAttribute()
        cm.attr_to_id['a'] = 0
        cm.body.append(parse('a = 2'))

        mod = Remove('a')

        old_id = cm.attr_to_id['a']
        mod.apply(cm)

        assert cm.body[old_id] == None
        assert 'a' not in cm.attr_to_id

    def test_remove_not_existed_variable(self):
        cm = ModuleAttribute()
        cm.attr_to_id['a'] = 0
        cm.body.append(parse('a = 2'))

        mod = Remove('b')

        with pytest.raises(VariableNotFound):
            mod.apply(cm)