"""main entry for pykokkos command-line interface"""


def main():
    from pykokkos import PyKokkos
    ret, _ = PyKokkos().run_command()
    return ret


if __name__ == "__main__":
    main()
