#include "MantidAPI/FileProperty.h"
#include "MantidAPI/IMDEventWorkspace.h"
#include "MantidAPI/IMDHistoWorkspace.h"
#include "MantidAPI/IMDWorkspace.h"
#include "MantidAPI/WorkspaceProperty.h"
#include "MantidKernel/ListValidator.h"
#include "MantidVatesAPI/SaveMDWorkspaceToVTK.h"

#include "MantidVatesAPI/Normalization.h"
#include "MantidVatesAPI/SaveMDWorkspaceToVTKImpl.h"

#include "MantidKernel/BoundedValidator.h"
#include "MantidKernel/make_unique.h"

namespace Mantid {
namespace VATES {

DECLARE_ALGORITHM(SaveMDWorkspaceToVTK)

SaveMDWorkspaceToVTK::SaveMDWorkspaceToVTK()
    : saver(Mantid::Kernel::make_unique<SaveMDWorkspaceToVTKImpl>()) {}

SaveMDWorkspaceToVTK::~SaveMDWorkspaceToVTK() {}

const std::string SaveMDWorkspaceToVTK::name() const {
  return "SaveMDWorkspaceToVTK";
}

int SaveMDWorkspaceToVTK::version() const { return 1; }

const std::string SaveMDWorkspaceToVTK::category() const {
  return "MDAlgorithms";
}

const std::string SaveMDWorkspaceToVTK::summary() const {
  std::string summary = "Saves MD workspaces to VTK file types which can be "
                        "loaded by ParaView. MDHisto workspaces are saved as "
                        ".vts files and MDEvent workspaces as .vtu files.";
  return summary;
}

void SaveMDWorkspaceToVTK::init() {
  declareProperty(new Mantid::API::WorkspaceProperty<Mantid::API::IMDWorkspace>(
                      "InputWorkspace", "", Mantid::Kernel::Direction::Input),
                  "MDWorkspace to save/export");

  std::vector<std::string> extensions = {
      SaveMDWorkspaceToVTKImpl::structuredGridExtension,
      SaveMDWorkspaceToVTKImpl::unstructuredGridExtension};
  declareProperty(new Mantid::API::FileProperty(
                      "Filename", "", Mantid::API::FileProperty::Save,
                      extensions, Mantid::Kernel::Direction::Input),
                  "Save location.");

  auto normalizations = saver->getAllowedNormalizationsInStringRepresentation();
  declareProperty(
      "Normalization", "AutoSelect",
      boost::make_shared<Mantid::Kernel::StringListValidator>(normalizations),
      "The visual normalization option. The automatic default will choose a "
      "normalization based on your data type and instrument.");

  auto thresholds = saver->getAllowedThresholdsInStringRepresentation();
  declareProperty(
      "ThresholdRange", "IgnoreZerosThresholdRange",
      boost::make_shared<Mantid::Kernel::StringListValidator>(thresholds),
      "The threshold range. Currently either no threshold or an ignore-zeros "
      "policy can be applied.");

  boost::shared_ptr<Mantid::Kernel::BoundedValidator<int>> mustBePositive(
      new Mantid::Kernel::BoundedValidator<int>());
  mustBePositive->setLower(1);
  declareProperty("RecursionDepth", 5, mustBePositive,
                  "The recursion depth is only required for MDEvent workspaces "
                  "and determines to which level data should be displayed.");
}

void SaveMDWorkspaceToVTK::exec() {
  // Get the input properties
  Mantid::API::IMDWorkspace_sptr inputWS = this->getProperty("InputWorkspace");
  std::string filename = this->getProperty("Filename");

  std::string normalizationInStringRepresentation =
      this->getProperty("Normalization");
  auto normalization = saver->translateStringToVisualNormalization(
      normalizationInStringRepresentation);

  std::string thresholdRangeInStringRepresentation =
      this->getProperty("ThresholdRange");
  auto thresholdRange = saver->translateStringToThresholdRange(
      thresholdRangeInStringRepresentation);

  int recursionDepth = this->getProperty("RecursionDepth");

  // Save workspace into file
  saver->saveMDWorkspace(inputWS, filename, normalization, thresholdRange,
                         recursionDepth);
}

std::map<std::string, std::string> SaveMDWorkspaceToVTK::validateInputs() {
  std::map<std::string, std::string> errorMessage;

  // Check for input workspace type
  Mantid::API::IMDWorkspace_sptr inputWS = this->getProperty("InputWorkspace");
  if (!boost::dynamic_pointer_cast<Mantid::API::IMDHistoWorkspace>(inputWS) &&
      !boost::dynamic_pointer_cast<Mantid::API::IMDEventWorkspace>(inputWS)) {
    errorMessage.emplace("InputWorkspace",
                         "Only MDHisto or MDEvent workspaces can be saved.");
  }

  // Check for the dimensionality
  if (!saver->is3DWorkspace(inputWS)) {
    errorMessage.emplace("InputWorkspace", "The MD workspace must be 3D.");
  }

  // Check for file location
  return errorMessage;
}
}
}