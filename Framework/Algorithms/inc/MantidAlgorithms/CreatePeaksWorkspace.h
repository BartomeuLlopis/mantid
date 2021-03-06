#ifndef MANTID_ALGORITHMS_CREATEPEAKSWORKSPACE_H_
#define MANTID_ALGORITHMS_CREATEPEAKSWORKSPACE_H_

#include "MantidKernel/System.h"
#include "MantidAPI/Algorithm.h"

namespace Mantid {
namespace Algorithms {

/** Create an empty PeaksWorkspace.
 *
 * @author Janik Zikovsky
 * @date 2011-04-26 08:49:10.540441
 */
class DLLExport CreatePeaksWorkspace : public API::Algorithm {
public:
  /// Algorithm's name for identification
  const std::string name() const override { return "CreatePeaksWorkspace"; };
  /// Summary of algorithms purpose
  const std::string summary() const override {
    return "Create an empty PeaksWorkspace.";
  }

  /// Algorithm's version for identification
  int version() const override { return 1; };
  /// Algorithm's category for identification
  const std::string category() const override {
    return "Crystal\\Peaks;Utility\\Workspaces";
  }

private:
  /// Initialise the properties
  void init() override;
  /// Run the algorithm
  void exec() override;
};

} // namespace Mantid
} // namespace Algorithms

#endif /* MANTID_ALGORITHMS_CREATEPEAKSWORKSPACE_H_ */
