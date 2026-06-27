from oompa_types.domain.valued import Valued


class AbstractValued[VALUE_T](Valued[VALUE_T]):
    def __init__(
        self,
        value: VALUE_T | None = None,
        default: VALUE_T | None = None,
        value_type: VALUE_T = None,
    ):
        self._value = value
        self._default: VALUE_T = default
        if value_type is not None:
            self._value_type = value_type
        else:
            self._value_type: VALUE_T = type(value)

    @property
    def value(self) -> VALUE_T:
        return self._value

    @value.setter
    def value(self, new_value: VALUE_T):
        self._value = new_value

    @property
    def default(self) -> VALUE_T:
        return self._default

    @property
    def value_type(self) -> VALUE_T:
        return self._value_type
