def parallel_for(policy, functor, *args):

    # args conversion to c data types
    #   * numpy ndarray -> to bytes with array shapes
    #   * builtin types: int, float, string

    # generate frame of a c function
    return functor(argv=[], *args)
