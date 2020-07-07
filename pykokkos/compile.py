import os, sys

from microapp import App
from pykokkos.util import load_functor, load_pymod, OpMode


class PykokkosCompiler(App):

    _name_ = "compile"
    _version_ = "0.1.0"

    def __init__(self, mgr):
        self.add_argument("sourcefile", help="source file path")

        self.add_argument("-c", "--compiler", help="c++ compiler")
        self.add_argument("-l", "--linker", help="linker")
        self.add_argument("-f", action="append", help="compiler option with one dash")
        self.add_argument("-x", action="append", help="linker option with one dash")
        self.add_argument("--flag", action="append", help="compiler option with two dashes")
        self.add_argument("--xflag", action="append", help="linker option with two dashes")
        self.add_argument("-s", "--staticlib", action="append", help="static libraries")

        #self.add_argument("-I", "--include-dir", action="append",
        #                  help="include directory")
        self.register_forward("functor")

    def perform(self, args):

        os.environ["PYKOKKOS_OPERATION"] = OpMode.COMPILE

        if args.compiler:
            os.environ["PYKOKKOS_COMPILER"] = args.compiler["_"]

        elif "PYKOKKOS_COMPILER" not in os.environ and self.has_config("compiler"):
            os.environ["PYKOKKOS_COMPILER"] = self.get_config("compiler")

        if args.linker:
            os.environ["PYKOKKOS_LINKER"] = args.linker["_"]

        elif "PYKOKKOS_LINKER" not in os.environ:
            if self.has_config("linker"):
                os.environ["PYKOKKOS_LINKER"] = self.get_config("linker")
            else:
                os.environ["PYKOKKOS_LINKER"] = os.environ["PYKOKKOS_COMPILER"]

        flags = []

        if args.f:
            for flag in args.f:
                flags.append("-"+flag["_"])

        if args.flag:

            for flag in args.flag:
                flags.append("--"+flag["_"])

        if flags:
            os.environ["PYKOKKOS_COMPILER_OPTION"] = " ".join(flags)

        elif "PYKOKKOS_COMPILER_OPTION" not in os.environ and self.has_config("compiler_option"):
            os.environ["PYKOKKOS_COMPILER_OPTION"] = self.get_config("compiler_option")

        xflags = []

        if args.x:
            for flag in args.x:
                xflags.append("-"+flag["_"])

        if args.xflag:

            for flag in args.xflag:
                flags.append("--"+flag["_"])

        if xflags:
            os.environ["PYKOKKOS_LINKER_OPTION"] = " ".join(xflags)

        elif "PYKOKKOS_LINKER_OPTION" not in os.environ and self.has_config("linker_option"):
            os.environ["PYKOKKOS_LINKER_OPTION"] = self.get_config("linker_option")

        staticlibs = []

        if args.staticlib:

            for flag in args.staticlib:
                staticlibs.append(flag["_"])

        if staticlibs:
            os.environ["PYKOKKOS_LINKER_STATICLIB"] = " ".join(staticlibs)

        elif "PYKOKKOS_LINKER_STATICLIB" not in os.environ and self.has_config("linker_staticlib"):
            os.environ["PYKOKKOS_LINKER_STATICLIB"] = self.get_config("linker_staticlib")

        spath = args.sourcefile["_"]

        if os.path.exists(spath):
            load_functor(spath)

        else:
            raise Exception("Can not find: %s" % sfile)

        functors = [f.strip() for f in os.environ["PYKOKKOS_FUNCTOR"].split(",") if f]
        self.add_forward(functor=functors)
