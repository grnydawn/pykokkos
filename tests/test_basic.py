import os, shutil

from pykokkos import PyKokkos

here = os.path.dirname(os.path.abspath(__file__))
srcfile = os.path.join(here, "hello.py")
cppfile = os.path.join(here, "hello.cpp")
objfile = os.path.join(here, "hello.o")
sofile = os.path.join(here, "hello.so")

kokkos_path = "/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/xl-16.1.1-5/kokkos-3.0.00-5uh3tul7pohep6k3jouxqyb5atitwhzh"
kokkos_include_dir = kokkos_path + "/include"
kokkos_library_dir = kokkos_path + "/lib64"

def test_clean(capsys):

    prj = PyKokkos()

    cmd = "clean %s" % srcfile
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert not os.path.isfile(cppfile)
    assert not os.path.isfile(objfile)
    assert not os.path.isfile(sofile)

def test_compile(capsys):

    prj = PyKokkos()

    #cmd = "compile %s -c g++ -I %s -L %s -f 'fopenmp' -f 'std=c++11'" % (
    cmd = "compile %s -c xlC -f 'I %s' -x 'fopenmp' -f 'fopenmp' -f 'std=c++11' -s '%s'" % (
            srcfile, kokkos_include_dir, kokkos_library_dir+"/libkokkoscore.a")
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    #assert "Hello World!" in captured.out

    functor = fwds["functor"][0]

    assert os.path.isfile(os.path.join(here, functor + ".cpp"))
    assert os.path.isfile(os.path.join(here, functor + ".o"))
    assert os.path.isfile(os.path.join(here, functor + ".so"))


def test_run(capsys):

    prj = PyKokkos()

    cmd = "run %s" % srcfile
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Hello" in captured.out
