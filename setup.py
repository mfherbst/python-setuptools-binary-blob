#!/usr/bin/env python3

"""Setup for head"""
import os
import sys
import glob
import json
import setuptools

from os.path import join

from setuptools import Extension, find_packages, setup
from setuptools.command.test import test as TestCommand
from setuptools.command.build_ext import build_ext as BuildCommand

# Version of the python bindings and head python package.
__version__ = '0.0.0'


#
# Compile and install core library
#
def trigger_core_build():
    """
    Trigger a build of the core library, if it exists in source form.
    """
    if os.path.isfile("core/build.sh"):
        # I.e. this user has access to core source code
        import subprocess

        subprocess.check_call("./core/build.sh")


#
# Find AdcCore
#
class AdcCore:
    def __init__(self):
        this_dir = os.path.dirname(__file__)
        self.config_path = join(this_dir, "extension", "core",
                                "core_config.json")

    @property
    def is_config_file_present(self):
        """
        Is the config file present on disk
        """
        return os.path.isfile(self.config_path)

    @property
    def config(self):
        if not self.is_config_file_present:
            raise RuntimeError(
                "Did not find core_config.json file in the directory tree." +
                " Did you download or install core properly? See the head " +
                "documentation for help."
            )
        else:
            with open(self.config_path, "r") as fp:
                return json.load(fp)

    def __getattr__(self, key):
        try:
            return self.config[key]
        except KeyError:
            raise AttributeError


#
# Pybind11 BuildExt
#
class GetPyBindInclude:
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11

        return pybind11.get_include(self.user)


# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile

    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.

    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(BuildCommand):
    """A custom build extension for adding compiler-specific options."""
    def build_extensions(self):
        trigger_core_build()

        opts = []
        print(self.compiler.compiler_type)
        if sys.platform == "darwin":
            potential_opts = ['-stdlib=libc++', '-mmacosx-version-min=10.7']
            opts.extend([opt for opt in potential_opts if has_flag(self.compiler, opt)])
        if self.compiler.compiler_type == 'unix':
            opts.append(cpp_flag(self.compiler))
            potential_opts = [
                "-fvisibility=hidden", "-Werror", "-Wall", "-Wextra",
                "-pedantic", "-Wnon-virtual-dtor", "-Woverloaded-virtual",
                "-Wcast-align", "-Wconversion", "-Wsign-conversion",
                "-Wmisleading-indentation", "-Wduplicated-cond",
                "-Wduplicated-branches", "-Wlogical-op",
                "-Wdouble-promotion", "-Wformat=2",
                "-Wno-error=deprecated-declarations",
            ]
            opts.extend([opt for opt in potential_opts
                         if has_flag(self.compiler, opt)])

        for ext in self.extensions:
            ext.extra_compile_args = opts
        BuildCommand.build_extensions(self)


#
# Main setup code
#
if not os.path.isfile("head/__init__.py"):
    raise RuntimeError("Running setup.py is only supported "
                       "from top level of repository as './setup.py "
                       "<command>'")

core = AdcCore()
if not core.is_config_file_present:
    # Trigger a build of core if the source code can be found
    trigger_core_build()
if core.version != __version__:
    # Try to see if a simple core build solves this issue
    trigger_core_build()

    if core.version != __version__:
        raise RuntimeError(
            "Version mismatch between head (== {}) and core (== {})"
            "".format(__version__, core.version)
        )

# Setup RPATH on Linux and MacOS
if sys.platform == "darwin":
    extra_link_args = ["-Wl,-rpath,.", "-Wl,-rpath,@loader_path/head/lib"]
    runtime_library_dirs = []
elif sys.platform == "linux":
    extra_link_args = []
    runtime_library_dirs = ["$ORIGIN", "$ORIGIN/head/lib"]
else:
    raise OSError("Unsupported platform: {}".format(sys.platform))

# Setup build of the libcore extension
ext_modules = [
    Extension(
        'libcore', glob.glob("extension/*.cc"),
        include_dirs=[
            # Path to pybind11 headers
            GetPyBindInclude(),
            GetPyBindInclude(user=True),
            "extension/core/include"
        ],
        libraries=core.libraries,
        library_dirs=["head/lib"],
        extra_link_args=extra_link_args,
        runtime_library_dirs=runtime_library_dirs,
        language='c++',
    ),
]

setup(
    name='head',
    description='A python-based framework for running ADC calculations',
    long_description='',  # TODO
    #
    url='https://github.com/mfherbst/adcc',
    author='adcc developers',
    author_email='adcc+developers@michael-herbst.com',
    maintainer='Michael F. Herbst',
    maintainer_email='info@michael-herbst.com',
    license="LGPL v3",
    #
    version=__version__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v3 (LGPLv3)',
        'Intended Audience :: Science/Research',
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Education",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: Unix',
    ],
    #
    packages=find_packages(exclude=["*.test*", "test"]),
    package_data={'head': ["lib/*.so", "lib/*.dylib"]},
    ext_modules=ext_modules,
    zip_safe=False,
    #
    platforms=["Linux", "Mac OS-X", "Unix"],
    python_requires='>=3.5',
    install_requires=[
        'pybind11 (>= 2.2)',
        'numpy',
        'scipy',
    ],
    tests_require=["pytest", "h5py"],
    #
    cmdclass={'build_ext': BuildExt},
)
