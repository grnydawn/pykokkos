import os, sys

from microapp import App

def _load_pymod(head, modname):

    sys.path.insert(0, os.path.abspath(os.path.realpath(head)))
    m = __import__(modname)
    sys.path.pop(0)    
    return m


class PykokkosCompiler(App):

    _name_ = "compile"
    _version_ = "0.1.0"

    def __init__(self, mgr):
        self.add_argument("sourcefile", help="source file path")

    def perform(self, args):

        spath = args.sourcefile["_"]

        if os.path.exists(spath):
            head, base = os.path.split(spath)
            mod = None

            if os.path.isfile(spath) and spath.endswith(".py"):
                modname = base[:-3]
                mod = _load_pymod(head, modname)

            elif (os.path.isdir(spath) and
                    os.path.isfile(os.path.join(spath, "__init__.py"))):
                modname = base[:-1] if base[-1] == os.sep else base
                mod = _load_pymod(head, modname)

        else:
            raise Exception("Can not find: %s" % sfile)

        import pdb; pdb.set_trace()

