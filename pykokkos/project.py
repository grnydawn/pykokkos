import os

from microapp import Project
from pykokkos.compiler import PykokkosCompiler


class PyKokkos(Project):
    _name_ = "pykokkos"
    _version_ = "0.1.0"
    _description_ = "Pythonic Kokkos"
    _long_description_ = "Pythonic Kokkos"
    _author_ = "Youngsung Kim"
    _author_email_ = "youngsung.kim.act2@gmail.com"
    _url_ = "https://github.com/grnydawn/pykokkos"
    _builtin_apps_ = [PykokkosCompiler]
    _requires_ = []

    def __init__(self):
        self.add_argument("--compiler", help="c++ compiler")

    def perform(self, args):

        compiler = None

        if self.has_config("compiler"):
            compiler = self.get_config("compiler")

        if args.compiler:
            compiler = args.compiler["_"]

        if compiler:
            self.set_downcast("compiler", compiler)

        else:
            raise Exception("No compiler is defined.")
