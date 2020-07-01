import sys
import pykokkos


@pykokkos.functor
def hello(i):
    print("Hello %d!" % i)


def main():

    pykokkos.parallel_for(10, hello)

    return 0


if __name__ == "__main__":
    sys.exit(main())
