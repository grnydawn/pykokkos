import sys, os


class OpMode(object):
    CLEAN       = "0"
    COMPILE     = "1"
    RUN         = "2"
    OPTIMIZE    = "3"


def load_pymod(head, modname):

    if "PYKOKKOS_OPERATION" in os.environ:
        if modname in sys.modules:
            del sys.modules[modname]

        sys.path.insert(0, os.path.abspath(os.path.realpath(head)))
        m = __import__(modname)
        sys.path.pop(0)    

        return m

    else:
        raise Exception("Pykokkos module should be loaded through pykokkos command")



def load_functor(spath):

    head, base = os.path.split(spath)
    mod = None

    if os.path.isfile(spath) and spath.endswith(".py"):
        modname = base[:-3]
        mod = load_pymod(head, modname)

    elif (os.path.isdir(spath) and
            os.path.isfile(os.path.join(spath, "__init__.py"))):
        modname = base[:-1] if base[-1] == os.sep else base
        mod = load_pymod(head, modname)

    return mod
