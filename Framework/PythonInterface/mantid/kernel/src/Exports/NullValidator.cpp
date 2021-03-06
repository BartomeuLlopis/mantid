#include "MantidPythonInterface/kernel/GetPointer.h"
#include "MantidKernel/NullValidator.h"

#include <boost/python/class.hpp>
#include <boost/python/register_ptr_to_python.hpp>

using Mantid::Kernel::NullValidator;
using Mantid::Kernel::IValidator;
using namespace boost::python;

GET_POINTER_SPECIALIZATION(NullValidator)

void export_NullValidator() {
  register_ptr_to_python<boost::shared_ptr<NullValidator>>();

  class_<NullValidator, bases<IValidator>, boost::noncopyable>("NullValidator");
}
