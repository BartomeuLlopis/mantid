#ifndef MANTID_API_WORKSPACEPROPERTY_H_
#define MANTID_API_WORKSPACEPROPERTY_H_

#include "MantidKernel/PropertyWithValue.h"
#include "MantidAPI/IWorkspaceProperty.h"
#include "MantidKernel/Logger.h"

#include <string>

namespace Mantid {
namespace API {
// -------------------------------------------------------------------------
// Forward decaration
// -------------------------------------------------------------------------
class MatrixWorkspace;
class WorkspaceGroup;

/// Enumeration for a mandatory/optional property
struct PropertyMode {
  enum Type { Mandatory, Optional };
};
/// Enumeration for locking behaviour
struct LockMode {
  enum Type { Lock, NoLock };
};

/** A property class for workspaces. Inherits from PropertyWithValue, with the
value being
a pointer to the workspace type given to the WorkspaceProperty constructor. This
kind
of property also holds the name of the workspace (as used by the
AnalysisDataService)
and an indication of whether it is an input or output to an algorithm (or both).

The pointers to the workspaces are fetched from the ADS when the properties are
validated
(i.e. when the PropertyManager::validateProperties() method calls isValid() ).
Pointers to output workspaces are also fetched, if they exist, and can then be
used within
an algorithm. (An example of when this might be useful is if the user wants to
write the
output into the same workspace as is used for input - this avoids creating a new
workspace
and the overwriting the old one at the end.)

@author Russell Taylor, Tessella Support Services plc
@date 10/12/2007

Copyright &copy; 2007-2010 ISIS Rutherford Appleton Laboratory, NScD Oak Ridge
National Laboratory & European Spallation Source

This file is part of Mantid.

Mantid is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

Mantid is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

File change history is stored at: <https://github.com/mantidproject/mantid>.
Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
template <typename TYPE = MatrixWorkspace>
class WorkspaceProperty
    : public Kernel::PropertyWithValue<boost::shared_ptr<TYPE>>,
      public IWorkspaceProperty {
public:
  explicit WorkspaceProperty(
      const std::string &name, const std::string &wsName,
      const unsigned int direction,
      Kernel::IValidator_sptr validator =
          Kernel::IValidator_sptr(new Kernel::NullValidator));

  explicit WorkspaceProperty(
      const std::string &name, const std::string &wsName,
      const unsigned int direction, const PropertyMode::Type optional,
      Kernel::IValidator_sptr validator =
          Kernel::IValidator_sptr(new Kernel::NullValidator));

  explicit WorkspaceProperty(
      const std::string &name, const std::string &wsName,
      const unsigned int direction, const PropertyMode::Type optional,
      const LockMode::Type locking,
      Kernel::IValidator_sptr validator =
          Kernel::IValidator_sptr(new Kernel::NullValidator));

  WorkspaceProperty(const WorkspaceProperty &right);

  WorkspaceProperty &operator=(const WorkspaceProperty &right);

  boost::shared_ptr<TYPE> &
  operator=(const boost::shared_ptr<TYPE> &value) override;

  WorkspaceProperty &operator+=(Kernel::Property const *) override;

  WorkspaceProperty<TYPE> *clone() const override;

  std::string value() const override;

  std::string getDefault() const override;

  std::string setValue(const std::string &value) override;

  std::string
  setDataItem(const boost::shared_ptr<Kernel::DataItem> value) override;

  std::string isValid() const override;

  bool isDefault() const override;

  bool isOptional() const override;
  bool isLocking() const override;

  std::vector<std::string> allowedValues() const override;

  const Kernel::PropertyHistory createHistory() const override;

  bool store() override;

  Workspace_sptr getWorkspace() const override;

  void setIsMasterRank(bool isMasterRank) override;

private:
  std::string isValidGroup(boost::shared_ptr<WorkspaceGroup> wsGroup) const;

  std::string isValidOutputWs() const;

  std::string isOptionalWs() const;

  void clear() override;

  void retrieveWorkspaceFromADS();

  /// The name of the workspace (as used by the AnalysisDataService)
  std::string m_workspaceName;
  /// The name of the workspace that the this this object was created for
  std::string m_initialWSName;
  /// A flag indicating whether the property should be considered optional. Only
  /// matters for input workspaces
  PropertyMode::Type m_optional;
  /** A flag indicating whether the workspace should be read or write-locked
   * when an algorithm begins. Default=true. */
  LockMode::Type m_locking;

  /// for access to logging streams
  static Kernel::Logger g_log;

  bool m_isMasterRank{true};
};

template <typename TYPE>
Kernel::Logger WorkspaceProperty<TYPE>::g_log("WorkspaceProperty");

} // namespace API
} // namespace Mantid

#endif /*MANTID_API_WORKSPACEPROPERTY_H_*/
