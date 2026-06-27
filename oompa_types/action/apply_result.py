import aenum
from oompa_types.objects.named import Named


class ApplyResult:
    class Status(aenum.AutoNumberEnum):
        UNDEFINED = ()
        NO_OP = ()
        SUCCESS = ()
        NOT_APPLICABLE = ()
        NOT_RELEVANT = ()
        ERROR = ()

    status: Status

    def __init__(self, status: Status = Status.UNDEFINED):
        self.status = status
        self._messages: list[str] = None
        self._added: list[Named] = None
        self._removed: list[Named] = None

    def __str__(self):
        return f"{self.status} added:{self.added} removed:{self.removed}"

    def reset(self):
        """Resets this result object. Returns itself to allow chaining."""
        self.status = ApplyResult.Status.UNDEFINED
        if self._messages:
            self._messages.clear()
        if self._added:
            self._added.clear()
        if self._removed:
            self._removed.clear()
        return self

    @property
    def message(self):
        return self._messages

    @message.setter
    def message(self, message: str):
        if self._messages is None:
            self._messages = []
        self._messages.append(message)

    @property
    def added(self):
        return self._added

    @added.setter
    def added(self, *objs: Named):
        if self._added is None:
            self._added = []
        self._added.extend(objs)

    @property
    def removed(self):
        return self._removed

    @removed.setter
    def removed(self, *objs: Named):
        if self._removed is None:
            self._removed = set()
        self._removed.update(objs)
