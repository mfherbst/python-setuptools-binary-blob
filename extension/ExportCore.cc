#include <core/core.hh>
#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(libcore, m) { m.def("add", &core::add); }
