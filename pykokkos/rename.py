import types

class Py2CRename(object):

    def __init__(self, argspec, closure):

        self._args = argspec.args if argspec else []
        self._varkw = argspec.varkw if argspec else {}
        self._defaults = argspec.defaults if argspec else {}
        self._kwonlyargs = argspec.kwonlyargs if argspec else []
        self._kwonlydefaults = argspec.kwonlydefaults if argspec else {}
        self._annotations = argspec.annotations if argspec else {}

        self._nonlocalvars = closure.nonlocals if closure else {}
        self._globalvars = closure.globals if closure else {}
        self._builtinvars = closure.builtins if closure else {}
        self._unboundvars = closure.unbound if closure else set()

    def compress_history(self, hist):
        return hist[3:-1]

    def rename(self, oldname, history):

        newhist = self.compress_history(history)
        nametype = getattr(self, "_h_" + "_".join(newhist))(oldname)
        return getattr(self, "_n_" + nametype)(oldname)

    ##############################
    #       NAMETYPE             #
    ##############################
    def _h_Expr_Call(self, oldname):

        if oldname in self._builtinvars:
            if type(self._builtinvars[oldname]) == types.BuiltinFunctionType:
                return types.BuiltinFunctionType.__name__

            else:
                raise Exception("Nametype of builtin '%s' is not resolved." % oldname)
        else:
            raise Exception("Nametype of '%s' is not resolved." % oldname)

    ##############################
    #       NEWNAME              #
    ##############################

    def _n_builtin_function_or_method(self, oldname):

        if oldname == "print":
            return "printf"

        else:
            raise Exception("Newname of builtin function '%s' is not generated." % oldname)
