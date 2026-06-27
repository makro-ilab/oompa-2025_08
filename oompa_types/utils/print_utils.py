ARGS_START = "("
ARGS_END = ")"
BINDINGS_START = "<"
BINDINGS_END = ">"
IMPLIED_BINDINGS_START = "<<"
IMPLIED_BINDINGS_END = ">>"
VALUE_TYPE_START = "{"
VALUE_TYPE_END = "}"
PATH_START = "|"
PATH_END = "|"


def collect_args(args):
    if args is None or len(args) == 0:
        return ARGS_START + ARGS_END
    return ARGS_START + ",".join(map(str, args)) + ARGS_END


def collect_bindings(bindings):
    if bindings is None or len(bindings) == 0:
        return BINDINGS_START + BINDINGS_END
    return BINDINGS_START + ",".join(map(str, bindings)) + BINDINGS_END
