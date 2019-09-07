import sys
import os
from multiprocessing import cpu_count
from conans import ConanFile, tools

class BotanConan(ConanFile):
    name = "Botan"
    version = "2.10.0"
    license = "BSD-2-Clause"
    url = "https://github.com/SteffenL/conan-botan"
    description = "Botan is a C++ cryptography library for Modern C++"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"

    source_dir = "botan"

    def source(self):
        git = tools.Git(folder=self.source_dir)
        git.clone("https://github.com/randombit/botan.git", self.version)

    def build(self):
        with tools.chdir(self.source_dir):
            sys.path.append(os.curdir)
            self._botan_configure()
            self._build()

    def package(self):
        self.copy("license.txt", dst="licenses", src=self.source_dir)
        self.copy("*.h", dst="include", src=os.path.join(self.source_dir, "build/include"))
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so*", dst="lib", keep_path=False)
        self.copy("*.dylib*", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = self._get_libs()

        if self.options.shared:
            self.cpp_info.defines += ["BOTAN_DLL=1"]
        else:
            self.cpp_info.defines += ["BOTAN_DLL="]

    def _build(self):
        if self.settings.compiler == "Visual Studio":
            vcvars = tools.vcvars_command(self.settings)
            build_cmd = "%s && nmake" % vcvars
        else:
            build_cmd = "make -j{cpu_count}".format(cpu_count=cpu_count())
        self.run(build_cmd)

    def _botan_configure(self):
        import configure
        cmd = [os.path.join(os.curdir, "configure.py")] + self._get_configure_params()
        configure.main(cmd)

    def _get_libs(self):
        libs = []
        if self.settings.compiler == "Visual Studio":
            libs += ["botan", "user32", "ws2_32"]
        else:
            libs += ["botan-2", "dl", "rt"]
            if not self.options.shared:
                libs += ["pthread"]
        return libs

    def _get_cc(self):
        if self.settings.compiler == "Visual Studio":
            return "msvc"
        if self.settings.compiler == "gcc":
            return "mingw" if self.settings.os == "Windows" else "gcc"
        if self.settings.compiler in ("apple-clang", "clang"):
            return "clang"
        raise ValueError("Unsupported compiler")

    def _get_cpu(self):
        return {
            "x86": "x86_32",
            "x86_64": "x86_64"
        }[str(self.settings.arch)]

    def _get_os(self):
        return {
            "Windows": "windows",
            "Linux": "linux"
        }[str(self.settings.os)]

    def _get_gcc_abi_flags(self):
        flags = []
        if self.settings.compiler.libcxx == "libstdc++":
            flags += ["-D_GLIBCXX_USE_CXX11_ABI=0"]
        elif self.settings.compiler.libcxx == "libstdc++11":
            flags += ["-D_GLIBCXX_USE_CXX11_ABI=1"]
        return " ".join(flags)

    def _get_gcc_version(self):
        version = str(self.settings.compiler.version).split(".")
        version = version if len(version) >= 2 else version + ["0"]
        version = ".".join(version)
        return version

    def _get_configure_params(self):
        params = ["=".join(x) for x in [
            ("--os", self._get_os()),
            ("--cc", self._get_cc()),
            ("--cpu", self._get_cpu())
        ]]
        if self.settings.compiler == "gcc":
            params += ["=".join(x) for x in [
                ("--cc-abi-flags", self._get_gcc_abi_flags()),
                ("--cc-min-version", self._get_gcc_version())
            ]]
        elif self.settings.compiler == "Visual Studio":
            params += ["=".join(x) for x in [
                ("--msvc-runtime", str(self.settings.compiler.runtime))
            ]]
        if self.settings.build_type == "Debug":
            params += ["--debug-mode"]
        if self.options.shared:
            params += ["--enable-shared-library", "--disable-static-library"]
        else:
            params += ["--enable-static-library", "--disable-shared-library"]
        return params
