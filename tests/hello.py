import sys
import pykokkos


@pykokkos.math_functor
def hello_functor( i:int ) -> None:
    #print("Hello %d!" % i)
    print("Hello")


def pykokkos_main():

    pykokkos.parallel_for(10, hello_functor)

    return 0
