import os

from microapp import Project
from pykokkos.compile import PykokkosCompiler
from pykokkos.clean import PykokkosCleaner
from pykokkos.run import PykokkosRunner


class PyKokkos(Project):
    _name_ = "pykokkos"
    _version_ = "0.1.0"
    _description_ = "Pythonic Kokkos"
    _long_description_ = "Pythonic Kokkos"
    _author_ = "Youngsung Kim"
    _author_email_ = "youngsung.kim.act2@gmail.com"
    _url_ = "https://github.com/grnydawn/pykokkos"
    _builtin_apps_ = [PykokkosCompiler, PykokkosCleaner, PykokkosRunner]
    _requires_ = []

#    def __init__(self):
#        self.add_argument("--compiler", help="c++ compiler")
#        self.add_argument("-f", "--flag", action="append",
#                          help="compiler option")
#
#        self.add_argument("-I", "--include-dir", action="append",
#                          help="include directory")
#        self.add_argument("-L", "--library-dir", action="append",
#                          help="library directory")
#
    def perform(self, args):

        os.environ["PYKOKKOS_FUNCTOR"] = ""

#        compiler = None
#
#        if self.has_config("compiler"):
#            compiler = self.get_config("compiler")
#
#        if args.compiler:
#            compiler = args.compiler["_"]
#
#        if compiler:
#            os.environ["PYKOKKOS_COMPILER"] = compiler
#
#        flags = []
#
#        if self.has_config("compiler_option"):
#            flags = [self.get_config("compiler_option")]
#
#        if args.flag:
#            for flag in args.flag:
#                flags.append(flag["_"])
#
#        if flags:
#            os.environ["PYKOKKOS_COMPILER_OPTION"] = " ".join(flags)
#
#        incpath = []
#
#        if self.has_config("include_path"):
#            incpath = [self.get_config("include_path")]
#
#        if args.include_dir:
#            for path in args.include_dir:
#                incpath.append(path["_"])
#
#        if incpath:
#            os.environ["PYKOKKOS_INCLUDE_PATH"] = ":".join(incpath)
#   
#        libpath = []
#
#        if self.has_config("library_path"):
#            libpath = [self.get_config("library_path")]
#
#        if args.library_dir:
#            for path in args.library_dir:
#                libpath.append(path["_"])
#
#        if libpath:
#            os.environ["PYKOKKOS_LIBRARY_PATH"] = ":".join(libpath)
