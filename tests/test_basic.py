import os, shutil

from pykokkos import PyKokkos

here = os.path.dirname(os.path.abspath(__file__))


def test_compile(capsys):

    prj = PyKokkos()

    cmd = "--compiler gggg++ compile %s " % os.path.join(here, "hello.py")
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

#    captured = capsys.readouterr()
#    assert captured.err == ""
#    assert "Compiled" in captured.out
#    assert os.path.isfile(jsonfile)
#    os.remove(jsonfile)
