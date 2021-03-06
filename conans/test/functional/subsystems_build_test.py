import platform

import pytest
import textwrap


from conans.client.tools.win import unix_path, MSYS2, CYGWIN
from conans.test.assets.sources import gen_function_cpp
from conans.test.functional.utils import check_exe_run
from conans.test.utils.tools import TestClient


@pytest.mark.skipif(platform.system() != "Windows", reason="Tests Windows Subsystems")
class TestSubsystems:

    @pytest.mark.tool_msys2
    def test_msys2_available(self):
        client = TestClient()
        client.run_command('uname')
        assert "MSYS" in client.out

    @pytest.mark.tool_cygwin
    def test_cygwin_available(self):
        client = TestClient()
        client.run_command('uname')
        assert "CYGWIN" in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw32
    def test_mingw32_available(self):
        client = TestClient()
        client.run_command('uname')
        assert "MINGW32_NT" in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw64
    def test_mingw64_available(self):
        client = TestClient()
        client.run_command('uname')
        assert "MINGW64_NT" in client.out

    def test_tool_not_available(self):
        client = TestClient()
        client.run_command('uname', assert_error=True)
        assert "'uname' is not recognized as an internal or external command" in client.out


@pytest.mark.skipif(platform.system() != "Windows", reason="Tests Windows Subsystems")
class TestSubsystemsBuild:
    makefile = textwrap.dedent("""
        .PHONY: all
        all: app

        app: main.o
        	$(CXX) $(CFLAGS) -o app main.o

        main.o: main.cpp
        	$(CXX) $(CFLAGS) -c -o main.o main.cpp
        """)

    def _build(self, client):
        main_cpp = gen_function_cpp(name="main")
        client.save({"Makefile": self.makefile,
                     "main.cpp": main_cpp})
        client.run_command("make")
        client.run_command("app")

    @pytest.mark.tool_msys2
    def test_msys(self):
        """
        native MSYS environment, binaries depend on MSYS runtime (msys-2.0.dll)
        posix-compatible, intended to be run only in MSYS environment (not in pure Windows)
        """
        client = TestClient()
        # pacman -S gcc
        self._build(client)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__MINGW32__" not in client.out
        assert "__MINGW64__" not in client.out
        assert "__MSYS__" in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw64
    def test_mingw64(self):
        """
        64-bit GCC, binaries for generic Windows (no dependency on MSYS runtime)
        """
        client = TestClient()
        # pacman -S mingw-w64-x86_64-gcc
        self._build(client)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__MINGW64__" in client.out
        assert "__CYGWIN__" not in client.out
        assert "__MSYS__" not in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw32
    def test_mingw32(self):
        """
        32-bit GCC, binaries for generic Windows (no dependency on MSYS runtime)
        """
        client = TestClient()
        # pacman -S mingw-w64-i686-gcc
        self._build(client)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86", None)

        assert "__MINGW32__" in client.out
        assert "__CYGWIN__" not in client.out
        assert "__MSYS__" not in client.out

    @pytest.mark.tool_cygwin
    def test_cygwin(self):
        """
        Cygwin environment, binaries depend on Cygwin runtime (cygwin1.dll)
        posix-compatible, intended to be run only in Cygwin environment (not in pure Windows)
        """
        client = TestClient()
        # install "gcc-c++" and "make" packages
        self._build(client)
        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__CYGWIN__" in client.out
        assert "__MINGW32__" not in client.out
        assert "__MINGW64__" not in client.out
        assert "__MSYS__" not in client.out


@pytest.mark.skipif(platform.system() != "Windows", reason="Tests Windows Subsystems")
class TestSubsystemsAutotoolsBuild:
    configure_ac = textwrap.dedent("""
        AC_INIT([Tutorial Program], 1.0)
        AM_INIT_AUTOMAKE([foreign])
        AC_PROG_CXX
        AC_CONFIG_FILES(Makefile)
        AC_OUTPUT
        """)  # newline is important

    makefile_am = textwrap.dedent("""
        bin_PROGRAMS = app
        app_SOURCES = main.cpp
        """)

    def _build(self, client, subsystem):
        main_cpp = gen_function_cpp(name="main")
        client.save({"configure.ac": self.configure_ac,
                     "Makefile.am": self.makefile_am,
                     "main.cpp": main_cpp})

        path = unix_path(client.current_folder, subsystem)
        client.run_command('bash -lc "cd \\"%s\\" && autoreconf -fiv"' % path)
        client.run_command('bash -lc "cd \\"%s\\" && ./configure"' % path)
        client.run_command("make")
        client.run_command("app")

    @pytest.mark.tool_msys2
    def test_msys(self):
        """
        native MSYS environment, binaries depend on MSYS runtime (msys-2.0.dll)
        posix-compatible, intended to be run only in MSYS environment (not in pure Windows)
        """
        client = TestClient()
        # pacman -S gcc
        self._build(client, MSYS2)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__MINGW32__" not in client.out
        assert "__MINGW64__" not in client.out
        assert "__MSYS__" in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw64
    def test_mingw64(self):
        """
        64-bit GCC, binaries for generic Windows (no dependency on MSYS runtime)
        """
        client = TestClient()
        # pacman -S mingw-w64-x86_64-gcc
        self._build(client, MSYS2)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__MINGW64__" in client.out
        assert "__CYGWIN__" not in client.out
        assert "__MSYS__" not in client.out

    @pytest.mark.tool_msys2
    @pytest.mark.tool_mingw32
    def test_mingw32(self):
        """
        32-bit GCC, binaries for generic Windows (no dependency on MSYS runtime)
        """
        client = TestClient()
        # pacman -S mingw-w64-i686-gcc
        self._build(client, MSYS2)

        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86", None)

        assert "__MINGW32__" in client.out
        assert "__CYGWIN__" not in client.out
        assert "__MSYS__" not in client.out

    @pytest.mark.tool_cygwin
    def test_cygwin(self):
        """
        Cygwin environment, binaries depend on Cygwin runtime (cygwin1.dll)
        posix-compatible, intended to be run only in Cygwin environment (not in pure Windows)
        """
        client = TestClient()
        # install "gcc-c++" and "make" packages
        self._build(client, CYGWIN)
        check_exe_run(client.out, "main", "gcc", None, "Debug", "x86_64", None)

        assert "__CYGWIN__" in client.out
        assert "__MINGW32__" not in client.out
        assert "__MINGW64__" not in client.out
        assert "__MSYS__" not in client.out
