import os, sys

from microapp import App
from pykokkos.util import load_functor, OpMode


class PykokkosCleaner(App):

    _name_ = "clean"
    _version_ = "0.1.0"

    def __init__(self, mgr):
        self.add_argument("sourcefile", help="source file path")

    def perform(self, args):

        os.environ["PYKOKKOS_OPERATION"] = OpMode.CLEAN

        spath = args.sourcefile["_"]

        if os.path.exists(spath):
            load_functor(spath)

        else:
            raise Exception("Can not find: %s" % sfile)
