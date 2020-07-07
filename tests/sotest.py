import ctypes

_functor = ctypes.CDLL('/ccs/home/grnydawn/repos/github/pykokkos/tests/hello_hello_functor.so')
LP_c_char = ctypes.POINTER(ctypes.c_char)
LP_LP_c_char = ctypes.POINTER(LP_c_char)
_functor.pykokkos_main.argtypes = (ctypes.c_int, LP_LP_c_char)

def our_function():
    global _functor
    #result = _functor._pykokkos_main_(ctypes.c_int(num_numbers), array_type(*numbers))

    argv = ["192.168.2.170","2600000026"]
    argc = len(argv)

    p = (LP_c_char*len(argv))()
    for i, arg in enumerate(argv):  # not sys.argv, but argv!!!
      enc_arg = arg.encode('utf-8')
      p[i] = ctypes.create_string_buffer(enc_arg)

    na = ctypes.cast(p, LP_LP_c_char)

    import pdb; pdb.set_trace()
    result = _functor.pykokkos_main(argc, na)
    return int(result)

our_function()
