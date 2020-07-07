from __future__ import print_function, unicode_literals

import six, sys, ast, os, io, subprocess, ctypes, inspect, json
from six import StringIO

from pykokkos.rename import Py2CRename
from pykokkos.util import OpMode

_soprefix = """
#include <Kokkos_Core.hpp>

extern "C" {
int pykokkos_main( int argc, char* argv[]%s )
{
    Kokkos::initialize( argc, argv );
    {
"""

_sopostfix = """
    }

    Kokkos::finalize();
    
    return 0;
}
}
"""

def _get_ctypestr(hint):

    if hint == type(1):
        return "int"

    else:
        raise Exception("Type '%s' is not supported." % str(hint))

def math_functor(func):


    # convert python code to c++ code
    opmode = os.environ["PYKOKKOS_OPERATION"]

    dirname = os.path.dirname(func.__globals__["__file__"])
    basename = func.__module__ + "_" + func.__name__
    os.environ["PYKOKKOS_FUNCTOR"] += "," + basename
    cpppath = os.path.join(dirname, "%s.cpp" % basename)
    objpath = os.path.join(dirname, "%s.o" % basename)
    sopath = os.path.join(dirname, "%s.so" % basename)

    if opmode == OpMode.CLEAN:
        if os.path.isfile(cpppath):
            os.remove(cpppath)

        if os.path.isfile(objpath):
            os.remove(objpath)

        if os.path.isfile(sopath):
            os.remove(sopath)

        return func

    argspec = inspect.getfullargspec(func)
    closurevars = inspect.getclosurevars(func)

    if opmode == OpMode.RUN:
        newargs = argspec.args
        #inspect.getdoc(object)
        #inspect.getcomments(object)
        #inspect.getfile(object)
        #inspect.getmodule(object)
        #inspect.getsourcefile(object)
        #inspect.getsourcelines(object)
        #inspect.getsource(object)
        #inspect.signature(callable, *, follow_wrapped=True)
        #class inspect.Signature
        #class inspect.Parameter
        #class inspect.BoundArguments
        #inspect.getclasstree
        #inspect.getfullargspec(func)
        #inspect.getargvalues(frame)
        #inspect.getclosurevars(func)
        #inspect.unwrap(func, *, stop=None)
        #inspect.getattr_static(obj, attr, default=None) 

        #members = inspect.getmembers(func)

        def pykokkos_functor(*newargsi, argv=[]):

            _functor = ctypes.CDLL(sopath)
            LP_c_char = ctypes.POINTER(ctypes.c_char)
            LP_LP_c_char = ctypes.POINTER(LP_c_char)
            _functor.pykokkos_main.argtypes = (ctypes.c_int, LP_LP_c_char)

            argc = len(argv)

            p = (LP_c_char*len(argv))()
            for i, arg in enumerate(argv):  # not sys.argv, but argv!!!
              enc_arg = arg.encode('utf-8')
              p[i] = ctypes.create_string_buffer(enc_arg)

            na = ctypes.cast(p, LP_LP_c_char)

            result = _functor.pykokkos_main(argc, na)
            return int(result)

        return pykokkos_functor

    if opmode == OpMode.COMPILE:
        compiler = os.environ["PYKOKKOS_COMPILER"]
        linker = os.environ["PYKOKKOS_LINKER"]
        compiler_option = os.environ.get("PYKOKKOS_COMPILER_OPTION", "")
        linker_option = os.environ.get("PYKOKKOS_LINKER_OPTION", "")
        linker_staticlib = os.environ.get("PYKOKKOS_LINKER_STATICLIB", "")
        verbosity = int(os.environ.get("PYKOKKOS_VERBOSITY", "1"))

        with open(cpppath, "w") as cppfile:

            # TODO: check argument types not only by name but also through type comparison
            # TODO: write cpp prefix

            args = []

            if argspec.args:
                hints = argspec.annotations
                rethint = hints.pop("return", None)

                for arg in argspec.args:
                    if arg not in hints:
                        raise Exception("'%s' is not hinted with data type." % arg)

                    hint = hints[arg]
                    args.append(_get_ctypestr(hint) + " " + arg)

            argstring = (", " + ", ".join(args)) if args else ""
            cppfile.write(_soprefix % argstring)

            source = inspect.getsource(func)
            tree = ast.parse(source)
            Translator(tree, file=cppfile, indent=2, argspec=argspec, closure=closurevars)

            # TODO: write cpp postfix
            cppfile.write(_sopostfix)

        if not os.path.isfile(cpppath):
            raise Exception("C++ source file for functor is not created.")

        # compile the converted c++ to a shared library
        compilecmd = "%s -c -fPIC -o %s %s %s" % (compiler, objpath,
                                        compiler_option, cpppath)

        process = subprocess.Popen(compilecmd, stdin=subprocess.PIPE, \
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        while True:
            err = process.stderr.readline()
            out = process.stdout.readline()

            if verbosity > 1:
                print(out)

            if verbosity > 0:
                print(err)

            if out == b'' and process.poll() is not None:
                break

        # get return code
        retcode = process.poll()
        if retcode != 0:
            out = compilecmd + "\n" + str(out)
            err = str(err) + "\n".join([str(l) for l in process.stderr.readlines()])
            raise Exception(err + "\n" + out)

        if not os.path.isfile(objpath):
            raise Exception("Object file for functor is not created.")

        # compile the converted c++ to a shared library
        linkcmd = "%s -shared -o %s %s %s %s" % (linker, sopath,
                                        linker_option, objpath, linker_staticlib)

        process = subprocess.Popen(linkcmd, stdin=subprocess.PIPE, \
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        while True:
            err = process.stderr.readline()
            out = process.stdout.readline()

            if verbosity > 1:
                print(out)

            if verbosity > 0:
                print(err)

            if out == b'' and process.poll() is not None:
                break

        # get return code
        retcode = process.poll()
        if retcode != 0:
            out = linkcmd + "\n" + str(out)
            err = str(err) + "\n".join([str(l) for l in process.stderr.readlines()])
            raise Exception(err + "\n" + out)

        if not os.path.isfile(sopath):
            raise Exception("Shared library file for functor is not created.")

        return func

# Large float and imaginary literals get turned into infinities in the AST.
# We unparse those infinities to INFSTR.
INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)

def interleave(inter, f, seq):
    """Call f on each item in seq, calling inter() in between.
    """
    seq = iter(seq)
    try:
        f(next(seq))
    except StopIteration:
        pass
    else:
        for x in seq:
            inter()
            f(x)

class Translator:
    """Python to C translator for PyKokkos functor"""

    def __init__(self, tree, file = sys.stdout, indent = 0, argspec = None, closure = None):
        self.f = file
        self.future_imports = []
        self._indent = indent
        self._py2c = Py2CRename(argspec, closure)

        msg = {"names":{}, "string": {}, "history":[]}
        self.visit(tree, msg)

        print("", file=self.f)
        self.f.flush()

    def fill(self, text = ""):
        "Indent a piece of text, according to the current indentation level"
        self.f.write("\n"+"    "*self._indent + text)

    def write(self, text):
        "Append a piece of text to the current line."
        self.f.write(six.text_type(text))

    def enter(self):
        self._indent += 1

    def leave(self):
        self._indent -= 1

    def visit(self, tree, msg):
        if isinstance(tree, list):
            msg["history"].append("list")

            for t in tree:
                self.visit(t, msg)

            msg["history"].pop()
            return

        clsname = tree.__class__.__name__
        meth = getattr(self, "_"+clsname)
        msg["history"].append(clsname)
        meth(tree, msg)
        msg["history"].pop()


    ############### Unparsing methods ######################
    # There should be one method per concrete grammar type #
    # Constructors should be grouped by sum type. Ideally, #
    # this would follow the order in the grammar, but      #
    # currently doesn't.                                   #
    ########################################################

    def _Module(self, tree, msg):
        for stmt in tree.body:
            self.visit(stmt, msg)
#
#    def _Interactive(self, tree):
#        for stmt in tree.body:
#            self.visit(stmt)
#
#    def _Expression(self, tree):
#        self.visit(tree.body)

    # stmt
    def _Expr(self, tree, msg):
        self.fill()
        self.visit(tree.value, msg)
        self.write(";")

#    def _NamedExpr(self, tree):
#        self.write("(")
#        self.visit(tree.target)
#        self.write(" := ")
#        self.visit(tree.value)
#        self.write(")")
#
#    def _Import(self, t):
#        self.fill("import ")
#        interleave(lambda: self.write(", "), self.visit, t.names)
#
#    def _ImportFrom(self, t):
#        # A from __future__ import may affect unparsing, so record it.
#        if t.module and t.module == '__future__':
#            self.future_imports.extend(n.name for n in t.names)
#
#        self.fill("from ")
#        self.write("." * t.level)
#        if t.module:
#            self.write(t.module)
#        self.write(" import ")
#        interleave(lambda: self.write(", "), self.visit, t.names)
#
#    def _Assign(self, t):
#        self.fill()
#        for target in t.targets:
#            self.visit(target)
#            self.write(" = ")
#        self.visit(t.value)
#
#    def _AugAssign(self, t):
#        self.fill()
#        self.visit(t.target)
#        self.write(" "+self.binop[t.op.__class__.__name__]+"= ")
#        self.visit(t.value)
#
#    def _AnnAssign(self, t):
#        self.fill()
#        if not t.simple and isinstance(t.target, ast.Name):
#            self.write('(')
#        self.visit(t.target)
#        if not t.simple and isinstance(t.target, ast.Name):
#            self.write(')')
#        self.write(": ")
#        self.visit(t.annotation)
#        if t.value:
#            self.write(" = ")
#            self.visit(t.value)
#
#    def _Return(self, t):
#        self.fill("return")
#        if t.value:
#            self.write(" ")
#            self.visit(t.value)
#
#    def _Pass(self, t):
#        self.fill("pass")
#
#    def _Break(self, t):
#        self.fill("break")
#
#    def _Continue(self, t):
#        self.fill("continue")
#
#    def _Delete(self, t):
#        self.fill("del ")
#        interleave(lambda: self.write(", "), self.visit, t.targets)
#
#    def _Assert(self, t):
#        self.fill("assert ")
#        self.visit(t.test)
#        if t.msg:
#            self.write(", ")
#            self.visit(t.msg)
#
#    def _Exec(self, t):
#        self.fill("exec ")
#        self.visit(t.body)
#        if t.globals:
#            self.write(" in ")
#            self.visit(t.globals)
#        if t.locals:
#            self.write(", ")
#            self.visit(t.locals)
#
#    def _Print(self, t):
#        self.fill("print ")
#        do_comma = False
#        if t.dest:
#            self.write(">>")
#            self.visit(t.dest)
#            do_comma = True
#        for e in t.values:
#            if do_comma:self.write(", ")
#            else:do_comma=True
#            self.visit(e)
#        if not t.nl:
#            self.write(",")
#
#    def _Global(self, t):
#        self.fill("global ")
#        interleave(lambda: self.write(", "), self.write, t.names)
#
#    def _Nonlocal(self, t):
#        self.fill("nonlocal ")
#        interleave(lambda: self.write(", "), self.write, t.names)
#
#    def _Await(self, t):
#        self.write("(")
#        self.write("await")
#        if t.value:
#            self.write(" ")
#            self.visit(t.value)
#        self.write(")")
#
#    def _Yield(self, t):
#        self.write("(")
#        self.write("yield")
#        if t.value:
#            self.write(" ")
#            self.visit(t.value)
#        self.write(")")
#
#    def _YieldFrom(self, t):
#        self.write("(")
#        self.write("yield from")
#        if t.value:
#            self.write(" ")
#            self.visit(t.value)
#        self.write(")")
#
#    def _Raise(self, t):
#        self.fill("raise")
#        if six.PY3:
#            if not t.exc:
#                assert not t.cause
#                return
#            self.write(" ")
#            self.visit(t.exc)
#            if t.cause:
#                self.write(" from ")
#                self.visit(t.cause)
#        else:
#            self.write(" ")
#            if t.type:
#                self.visit(t.type)
#            if t.inst:
#                self.write(", ")
#                self.visit(t.inst)
#            if t.tback:
#                self.write(", ")
#                self.visit(t.tback)
#
#    def _Try(self, t):
#        self.fill("try")
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#        for ex in t.handlers:
#            self.visit(ex)
#        if t.orelse:
#            self.fill("else")
#            self.enter()
#            self.visit(t.orelse)
#            self.leave()
#        if t.finalbody:
#            self.fill("finally")
#            self.enter()
#            self.visit(t.finalbody)
#            self.leave()
#
#    def _TryExcept(self, t):
#        self.fill("try")
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#
#        for ex in t.handlers:
#            self.visit(ex)
#        if t.orelse:
#            self.fill("else")
#            self.enter()
#            self.visit(t.orelse)
#            self.leave()
#
#    def _TryFinally(self, t):
#        if len(t.body) == 1 and isinstance(t.body[0], ast.TryExcept):
#            # try-except-finally
#            self.visit(t.body)
#        else:
#            self.fill("try")
#            self.enter()
#            self.visit(t.body)
#            self.leave()
#
#        self.fill("finally")
#        self.enter()
#        self.visit(t.finalbody)
#        self.leave()
#
#    def _ExceptHandler(self, t):
#        self.fill("except")
#        if t.type:
#            self.write(" ")
#            self.visit(t.type)
#        if t.name:
#            self.write(" as ")
#            if six.PY3:
#                self.write(t.name)
#            else:
#                self.visit(t.name)
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#
#    def _ClassDef(self, t):
#        self.write("\n")
#        for deco in t.decorator_list:
#            self.fill("@")
#            self.visit(deco)
#        self.fill("class "+t.name)
#        if six.PY3:
#            self.write("(")
#            comma = False
#            for e in t.bases:
#                if comma: self.write(", ")
#                else: comma = True
#                self.visit(e)
#            for e in t.keywords:
#                if comma: self.write(", ")
#                else: comma = True
#                self.visit(e)
#            if sys.version_info[:2] < (3, 5):
#                if t.starargs:
#                    if comma: self.write(", ")
#                    else: comma = True
#                    self.write("*")
#                    self.visit(t.starargs)
#                if t.kwargs:
#                    if comma: self.write(", ")
#                    else: comma = True
#                    self.write("**")
#                    self.visit(t.kwargs)
#            self.write(")")
#        elif t.bases:
#                self.write("(")
#                for a in t.bases:
#                    self.visit(a)
#                    self.write(", ")
#                self.write(")")
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#
    def _FunctionDef(self, t, msg):
        #self.__FunctionDef_helper(t, "def")
        self.__FunctionDef_helper(t, msg, "")

#    def _AsyncFunctionDef(self, t):
#        self.__FunctionDef_helper(t, "async def")
#
    def __FunctionDef_helper(self, t, msg, fill_suffix):
        self.write("\n")
#        for deco in t.decorator_list:
#            self.fill("@")
#            self.visit(deco)
#        def_str = fill_suffix+" "+t.name + "("
#        self.fill(def_str)
#        self.visit(t.args)
#        self.write(")")
#        if getattr(t, "returns", False):
#            self.write(" -> ")
#            self.visit(t.returns)
        self.enter()
        self.visit(t.body, msg)
        self.leave()

#    def _For(self, t):
#        self.__For_helper("for ", t)
#
#    def _AsyncFor(self, t):
#        self.__For_helper("async for ", t)
#
#    def __For_helper(self, fill, t):
#        self.fill(fill)
#        self.visit(t.target)
#        self.write(" in ")
#        self.visit(t.iter)
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#        if t.orelse:
#            self.fill("else")
#            self.enter()
#            self.visit(t.orelse)
#            self.leave()
#
#    def _If(self, t):
#        self.fill("if ")
#        self.visit(t.test)
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#        # collapse nested ifs into equivalent elifs.
#        while (t.orelse and len(t.orelse) == 1 and
#               isinstance(t.orelse[0], ast.If)):
#            t = t.orelse[0]
#            self.fill("elif ")
#            self.visit(t.test)
#            self.enter()
#            self.visit(t.body)
#            self.leave()
#        # final else
#        if t.orelse:
#            self.fill("else")
#            self.enter()
#            self.visit(t.orelse)
#            self.leave()
#
#    def _While(self, t):
#        self.fill("while ")
#        self.visit(t.test)
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#        if t.orelse:
#            self.fill("else")
#            self.enter()
#            self.visit(t.orelse)
#            self.leave()
#
#    def _generic_With(self, t, async_=False):
#        self.fill("async with " if async_ else "with ")
#        if hasattr(t, 'items'):
#            interleave(lambda: self.write(", "), self.visit, t.items)
#        else:
#            self.visit(t.context_expr)
#            if t.optional_vars:
#                self.write(" as ")
#                self.visit(t.optional_vars)
#        self.enter()
#        self.visit(t.body)
#        self.leave()
#
#    def _With(self, t):
#        self._generic_With(t)
#
#    def _AsyncWith(self, t):
#        self._generic_With(t, async_=True)
#
#    # expr
#    def _Bytes(self, t):
#        self.write(repr(t.s))

    def _Str(self, tree, msg):

        text = repr(tree.s)

        if text[0] == "'" and text[-1] == "'":
            text = json.dumps(text[1:-1])

        self.write(text)

#    def _JoinedStr(self, t):
#        # JoinedStr(expr* values)
#        self.write("f")
#        string = StringIO()
#        self._fstring_JoinedStr(t, string.write)
#        # Deviation from `unparse.py`: Try to find an unused quote.
#        # This change is made to handle _very_ complex f-strings.
#        v = string.getvalue()
#        if '\n' in v or '\r' in v:
#            quote_types = ["'''", '"""']
#        else:
#            quote_types = ["'", '"', '"""', "'''"]
#        for quote_type in quote_types:
#            if quote_type not in v:
#                v = "{quote_type}{v}{quote_type}".format(quote_type=quote_type, v=v)
#                break
#        else:
#            v = repr(v)
#        self.write(v)
#
#    def _FormattedValue(self, t):
#        # FormattedValue(expr value, int? conversion, expr? format_spec)
#        self.write("f")
#        string = StringIO()
#        self._fstring_JoinedStr(t, string.write)
#        self.write(repr(string.getvalue()))
#
#    def _fstring_JoinedStr(self, t, write):
#        for value in t.values:
#            meth = getattr(self, "_fstring_" + type(value).__name__)
#            meth(value, write)
#
#    def _fstring_Str(self, t, write):
#        value = t.s.replace("{", "{{").replace("}", "}}")
#        write(value)
#
#    def _fstring_Constant(self, t, write):
#        assert isinstance(t.value, str)
#        value = t.value.replace("{", "{{").replace("}", "}}")
#        write(value)
#
#    def _fstring_FormattedValue(self, t, write):
#        write("{")
#        expr = StringIO()
#        Translator(t.value, expr)
#        expr = expr.getvalue().rstrip("\n")
#        if expr.startswith("{"):
#            write(" ")  # Separate pair of opening brackets as "{ {"
#        write(expr)
#        if t.conversion != -1:
#            conversion = chr(t.conversion)
#            assert conversion in "sra"
#            write("!{conversion}".format(conversion=conversion))
#        if t.format_spec:
#            write(":")
#            meth = getattr(self, "_fstring_" + type(t.format_spec).__name__)
#            meth(t.format_spec, write)
#        write("}")
#
    def _Name(self, t, msg):

        newname = self._py2c.rename(t.id, msg["history"])
        #msg["names"][newname] = []
        self.write(newname)
#
#    def _NameConstant(self, t):
#        self.write(repr(t.value))
#
#    def _Repr(self, t):
#        self.write("`")
#        self.visit(t.value)
#        self.write("`")
#
#    def _write_constant(self, value):
#        if isinstance(value, (float, complex)):
#            # Substitute overflowing decimal literal for AST infinities.
#            self.write(repr(value).replace("inf", INFSTR))
#        else:
#            self.write(repr(value))
#
#    def _Constant(self, t):
#        value = t.value
#        if isinstance(value, tuple):
#            self.write("(")
#            if len(value) == 1:
#                self._write_constant(value[0])
#                self.write(",")
#            else:
#                interleave(lambda: self.write(", "), self._write_constant, value)
#            self.write(")")
#        elif value is Ellipsis: # instead of `...` for Py2 compatibility
#            self.write("...")
#        else:
#            if t.kind == "u":
#                self.write("u")
#            self._write_constant(t.value)
#
#    def _Num(self, t):
#        repr_n = repr(t.n)
#        if six.PY3:
#            self.write(repr_n.replace("inf", INFSTR))
#        else:
#            # Parenthesize negative numbers, to avoid turning (-1)**2 into -1**2.
#            if repr_n.startswith("-"):
#                self.write("(")
#            if "inf" in repr_n and repr_n.endswith("*j"):
#                repr_n = repr_n.replace("*j", "j")
#            # Substitute overflowing decimal literal for AST infinities.
#            self.write(repr_n.replace("inf", INFSTR))
#            if repr_n.startswith("-"):
#                self.write(")")
#
#    def _List(self, t):
#        self.write("[")
#        interleave(lambda: self.write(", "), self.visit, t.elts)
#        self.write("]")
#
#    def _ListComp(self, t):
#        self.write("[")
#        self.visit(t.elt)
#        for gen in t.generators:
#            self.visit(gen)
#        self.write("]")
#
#    def _GeneratorExp(self, t):
#        self.write("(")
#        self.visit(t.elt)
#        for gen in t.generators:
#            self.visit(gen)
#        self.write(")")
#
#    def _SetComp(self, t):
#        self.write("{")
#        self.visit(t.elt)
#        for gen in t.generators:
#            self.visit(gen)
#        self.write("}")
#
#    def _DictComp(self, t):
#        self.write("{")
#        self.visit(t.key)
#        self.write(": ")
#        self.visit(t.value)
#        for gen in t.generators:
#            self.visit(gen)
#        self.write("}")
#
#    def _comprehension(self, t):
#        if getattr(t, 'is_async', False):
#            self.write(" async for ")
#        else:
#            self.write(" for ")
#        self.visit(t.target)
#        self.write(" in ")
#        self.visit(t.iter)
#        for if_clause in t.ifs:
#            self.write(" if ")
#            self.visit(if_clause)
#
#    def _IfExp(self, t):
#        self.write("(")
#        self.visit(t.body)
#        self.write(" if ")
#        self.visit(t.test)
#        self.write(" else ")
#        self.visit(t.orelse)
#        self.write(")")
#
#    def _Set(self, t):
#        assert(t.elts) # should be at least one element
#        self.write("{")
#        interleave(lambda: self.write(", "), self.visit, t.elts)
#        self.write("}")
#
#    def _Dict(self, t):
#        self.write("{")
#        def write_key_value_pair(k, v):
#            self.visit(k)
#            self.write(": ")
#            self.visit(v)
#
#        def write_item(item):
#            k, v = item
#            if k is None:
#                # for dictionary unpacking operator in dicts {**{'y': 2}}
#                # see PEP 448 for details
#                self.write("**")
#                self.visit(v)
#            else:
#                write_key_value_pair(k, v)
#        interleave(lambda: self.write(", "), write_item, zip(t.keys, t.values))
#        self.write("}")
#
#    def _Tuple(self, t):
#        self.write("(")
#        if len(t.elts) == 1:
#            elt = t.elts[0]
#            self.visit(elt)
#            self.write(",")
#        else:
#            interleave(lambda: self.write(", "), self.visit, t.elts)
#        self.write(")")
#
#    unop = {"Invert":"~", "Not": "not", "UAdd":"+", "USub":"-"}
#    def _UnaryOp(self, t):
#        self.write("(")
#        self.write(self.unop[t.op.__class__.__name__])
#        self.write(" ")
#        if six.PY2 and isinstance(t.op, ast.USub) and isinstance(t.operand, ast.Num):
#            # If we're applying unary minus to a number, parenthesize the number.
#            # This is necessary: -2147483648 is different from -(2147483648) on
#            # a 32-bit machine (the first is an int, the second a long), and
#            # -7j is different from -(7j).  (The first has real part 0.0, the second
#            # has real part -0.0.)
#            self.write("(")
#            self.visit(t.operand)
#            self.write(")")
#        else:
#            self.visit(t.operand)
#        self.write(")")

    binop = { "Add":"+", "Sub":"-", "Mult":"*", "MatMult":"@", "Div":"/", "Mod":"%",
                    "LShift":"<<", "RShift":">>", "BitOr":"|", "BitXor":"^", "BitAnd":"&",
                    "FloorDiv":"//", "Pow": "**"}
    def _BinOp(self, t, msg):
        self.write("(")
        #msg["names"].clear()
        self.visit(t.left, msg)
        self.write(" " + self.binop[t.op.__class__.__name__] + " ")
        #msg["names"].clear()
        self.visit(t.right, msg)
        self.write(")")

#    cmpops = {"Eq":"==", "NotEq":"!=", "Lt":"<", "LtE":"<=", "Gt":">", "GtE":">=",
#                        "Is":"is", "IsNot":"is not", "In":"in", "NotIn":"not in"}
#    def _Compare(self, t):
#        self.write("(")
#        self.visit(t.left)
#        for o, e in zip(t.ops, t.comparators):
#            self.write(" " + self.cmpops[o.__class__.__name__] + " ")
#            self.visit(e)
#        self.write(")")
#
#    boolops = {ast.And: 'and', ast.Or: 'or'}
#    def _BoolOp(self, t):
#        self.write("(")
#        s = " %s " % self.boolops[t.op.__class__]
#        interleave(lambda: self.write(s), self.visit, t.values)
#        self.write(")")
#
#    def _Attribute(self,t):
#        self.visit(t.value)
#        # Special case: 3.__abs__() is a syntax error, so if t.value
#        # is an integer literal then we need to either parenthesize
#        # it or add an extra space to get 3 .__abs__().
#        if isinstance(t.value, getattr(ast, 'Constant', getattr(ast, 'Num', None))) and isinstance(t.value.n, int):
#            self.write(" ")
#        self.write(".")
#        self.write(t.attr)
#
    def _Call(self, t, msg):
        #msg["names"].clear()
        self.visit(t.func, msg)
        self.write("(")
        comma = False
        for e in t.args:
            if comma: self.write(", ")
            else: comma = True
            self.visit(e, msg)
        for e in t.keywords:
            if comma: self.write(", ")
            else: comma = True
            self.visit(e, msg)
        if sys.version_info[:2] < (3, 5):
            if t.starargs:
                if comma: self.write(", ")
                else: comma = True
                self.write("*")
                self.visit(t.starargs, msg)
            if t.kwargs:
                if comma: self.write(", ")
                else: comma = True
                self.write("**")
                self.visit(t.kwargs, msg)
        self.write(")")

#    def _Subscript(self, t):
#        self.visit(t.value)
#        self.write("[")
#        self.visit(t.slice)
#        self.write("]")
#
#    def _Starred(self, t):
#        self.write("*")
#        self.visit(t.value)
#
#    # slice
#    def _Ellipsis(self, t):
#        self.write("...")
#
#    def _Index(self, t):
#        self.visit(t.value)
#
#    def _Slice(self, t):
#        if t.lower:
#            self.visit(t.lower)
#        self.write(":")
#        if t.upper:
#            self.visit(t.upper)
#        if t.step:
#            self.write(":")
#            self.visit(t.step)
#
#    def _ExtSlice(self, t):
#        interleave(lambda: self.write(', '), self.visit, t.dims)
#
#    # argument
#    def _arg(self, t):
#        self.write(t.arg)
#        if t.annotation:
#            self.write(": ")
#            self.visit(t.annotation)
#
#    # others
#    def _arguments(self, t):
#        first = True
#        # normal arguments
#        all_args = getattr(t, 'posonlyargs', []) + t.args
#        defaults = [None] * (len(all_args) - len(t.defaults)) + t.defaults
#        for index, elements in enumerate(zip(all_args, defaults), 1):
#            a, d = elements
#            if first:first = False
#            else: self.write(", ")
#            self.visit(a)
#            if d:
#                self.write("=")
#                self.visit(d)
#            if index == len(getattr(t, 'posonlyargs', ())):
#                self.write(", /")
#
#        # varargs, or bare '*' if no varargs but keyword-only arguments present
#        if t.vararg or getattr(t, "kwonlyargs", False):
#            if first:first = False
#            else: self.write(", ")
#            self.write("*")
#            if t.vararg:
#                if hasattr(t.vararg, 'arg'):
#                    self.write(t.vararg.arg)
#                    if t.vararg.annotation:
#                        self.write(": ")
#                        self.visit(t.vararg.annotation)
#                else:
#                    self.write(t.vararg)
#                    if getattr(t, 'varargannotation', None):
#                        self.write(": ")
#                        self.visit(t.varargannotation)
#
#        # keyword-only arguments
#        if getattr(t, "kwonlyargs", False):
#            for a, d in zip(t.kwonlyargs, t.kw_defaults):
#                if first:first = False
#                else: self.write(", ")
#                self.visit(a),
#                if d:
#                    self.write("=")
#                    self.visit(d)
#
#        # kwargs
#        if t.kwarg:
#            if first:first = False
#            else: self.write(", ")
#            if hasattr(t.kwarg, 'arg'):
#                self.write("**"+t.kwarg.arg)
#                if t.kwarg.annotation:
#                    self.write(": ")
#                    self.visit(t.kwarg.annotation)
#            else:
#                self.write("**"+t.kwarg)
#                if getattr(t, 'kwargannotation', None):
#                    self.write(": ")
#                    self.visit(t.kwargannotation)
#
#    def _keyword(self, t):
#        if t.arg is None:
#            # starting from Python 3.5 this denotes a kwargs part of the invocation
#            self.write("**")
#        else:
#            self.write(t.arg)
#            self.write("=")
#        self.visit(t.value)
#
#    def _Lambda(self, t):
#        self.write("(")
#        self.write("lambda ")
#        self.visit(t.args)
#        self.write(": ")
#        self.visit(t.body)
#        self.write(")")
#
#    def _alias(self, t):
#        self.write(t.name)
#        if t.asname:
#            self.write(" as "+t.asname)
#
#    def _withitem(self, t):
#        self.visit(t.context_expr)
#        if t.optional_vars:
#            self.write(" as ")
#            self.visit(t.optional_vars)


#
#def roundtrip(filename, output=sys.stdout):
#    if six.PY3:
#        with open(filename, "rb") as pyfile:
#            encoding = tokenize.detect_encoding(pyfile.readline)[0]
#        with open(filename, "r", encoding=encoding) as pyfile:
#            source = pyfile.read()
#    else:
#        with open(filename, "r") as pyfile:
#            source = pyfile.read()
#    tree = compile(source, filename, "exec", ast.PyCF_ONLY_AST, dont_inherit=True)
#    Translator(tree, output)
#
#
#
#def testdir(a):
#    try:
#        names = [n for n in os.listdir(a) if n.endswith('.py')]
#    except OSError:
#        print("Directory not readable: %s" % a, file=sys.stderr)
#    else:
#        for n in names:
#            fullname = os.path.join(a, n)
#            if os.path.isfile(fullname):
#                output = StringIO()
#                print('Testing %s' % fullname)
#                try:
#                    roundtrip(fullname, output)
#                except Exception as e:
#                    print('  Failed to compile, exception is %s' % repr(e))
#            elif os.path.isdir(fullname):
#                testdir(fullname)
#
#def main(args):
#    if args[0] == '--testdir':
#        for a in args[1:]:
#            testdir(a)
#    else:
#        for a in args:
#            roundtrip(a)
#
#if __name__=='__main__':
#    main(sys.argv[1:])
