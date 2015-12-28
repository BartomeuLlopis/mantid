#include "MantidGeometry/Crystal/PointGroup.h"
#include "MantidKernel/System.h"

#include <set>
#include <boost/make_shared.hpp>
#include <boost/algorithm/string.hpp>

#include "MantidGeometry/Crystal/PointGroupFactory.h"
#include "MantidGeometry/Crystal/SymmetryOperationFactory.h"
#include "MantidGeometry/Crystal/SymmetryElementFactory.h"

namespace Mantid {
namespace Geometry {
using Kernel::V3D;
using Kernel::IntMatrix;

/**
 * Returns all equivalent reflections for the supplied hkl.
 *
 * This method returns a vector containing all equivalent hkls for the supplied
 * one. It depends on the internal state of the pointgroup object (e.g. which
 * symmetry operations and therefore, which transformation matrices are
 * present). This internal state is unique for each concrete point group and
 * is set in the constructor.
 *
 * The returned vector always contains a set of unique hkls, so for special hkls
 * like (100), it has fewer entries than for a general hkl. See also
 * PointGroup::getEquivalentSet.
 *
 * @param hkl :: Arbitrary hkl
 * @return :: std::vector containing all equivalent hkls.
 */
std::vector<V3D> PointGroup::getEquivalents(const V3D &hkl) const {
  return getEquivalentSet(hkl);
}

/**
 * Returns the same V3D for all equivalent hkls.
 *
 * This method is closely related to PointGroup::getEquivalents. It returns the
 * same V3D for all hkls of one "family". For example in a cubic point group
 * it will return (100) for (001), (010), (0-10), etc.
 *
 * It can be used to generate a set of symmetry independent hkls, useful for
 * example in powder diffraction.
 *
 * @param hkl :: Arbitrary hkl
 * @return :: hkl specific to a family of index-triplets
 */
V3D PointGroup::getReflectionFamily(const Kernel::V3D &hkl) const {
  return *getEquivalentSet(hkl).begin();
}

/// Protected constructor - can not be used directly.
PointGroup::PointGroup(const std::string &symbolHM, const Group &group,
                       const std::string &description)
    : Group(group), m_symbolHM(symbolHM),
      m_name(symbolHM + " (" + description + ")") {
  m_crystalSystem = getCrystalSystemFromGroup();
  m_latticeSystem = getLatticeSystemFromCrystalSystemAndGroup(m_crystalSystem);
}

PointGroup::PointGroup(const PointGroup &other)
    : Group(other), m_symbolHM(other.m_symbolHM), m_name(other.m_name),
      m_crystalSystem(other.m_crystalSystem),
      m_latticeSystem(other.m_latticeSystem) {}

PointGroup &PointGroup::operator=(const PointGroup &other) {
  Group::operator=(other);

  m_symbolHM = other.m_symbolHM;
  m_name = other.m_name;
  m_crystalSystem = other.m_crystalSystem;
  m_latticeSystem = other.m_latticeSystem;

  return *this;
}

/// Hermann-Mauguin symbol
std::string PointGroup::getSymbol() const { return m_symbolHM; }

bool PointGroup::isEquivalent(const Kernel::V3D &hkl,
                              const Kernel::V3D &hkl2) const {
  std::vector<V3D> hklEquivalents = getEquivalentSet(hkl);

  return (std::find(hklEquivalents.begin(), hklEquivalents.end(), hkl2) !=
          hklEquivalents.end());
}

/**
 * Generates a set of hkls
 *
 * This method applies all transformation matrices to the supplied hkl and puts
 * it into a set, which is returned in the end. Using a set ensures that each
 * hkl occurs once and only once. This set is the set of equivalent hkls,
 * specific to a concrete point group.
 *
 * The symmetry operations need to be set prior to calling this method by a call
 * to PointGroup::setTransformationMatrices.
 *
 * @param hkl :: Arbitrary hkl
 * @return :: set of hkls.
 */
std::vector<V3D> PointGroup::getEquivalentSet(const Kernel::V3D &hkl) const {
  std::vector<V3D> equivalents;
  equivalents.reserve(m_allOperations.size());

  for (auto op = m_allOperations.begin(); op != m_allOperations.end(); ++op) {
    equivalents.push_back((*op).transformHKL(hkl));
  }

  std::sort(equivalents.begin(), equivalents.end(), std::greater<V3D>());

  equivalents.erase(std::unique(equivalents.begin(), equivalents.end()),
                    equivalents.end());

  return equivalents;
}

/**
 * Returns the CrystalSystem determined from symmetry elements
 *
 * This method determines the crystal system of the point group. It makes
 * use of the fact that each crystal system has a characteristic set of
 * symmetry elements. The requirement for the cubic system is for example
 * that four 3-fold axes are present, whereas one 3-fold axis indicates
 * that the group belongs to the trigonal system.
 *
 * @return Crystal system that the point group belongs to.
 */
PointGroup::CrystalSystem PointGroup::getCrystalSystemFromGroup() const {
  std::map<std::string, std::set<V3D>> symbolMap;

  for (auto op = m_allOperations.begin(); op != m_allOperations.end(); ++op) {
    SymmetryElementWithAxis_sptr element =
        boost::dynamic_pointer_cast<SymmetryElementWithAxis>(
            SymmetryElementFactory::Instance().createSymElement(*op));

    if (element) {
      std::string symbol = element->hmSymbol();
      V3D axis = element->getAxis();

      symbolMap[symbol].insert(axis);
    }
  }

  if (symbolMap["3"].size() == 4) {
    return CrystalSystem::Cubic;
  }

  if (symbolMap["6"].size() == 1 || symbolMap["-6"].size() == 1) {
    return CrystalSystem::Hexagonal;
  }

  if (symbolMap["3"].size() == 1) {
    return CrystalSystem::Trigonal;
  }

  if (symbolMap["4"].size() == 1 || symbolMap["-4"].size() == 1) {
    return CrystalSystem::Tetragonal;
  }

  if (symbolMap["2"].size() == 3 ||
      (symbolMap["2"].size() == 1 && symbolMap["m"].size() == 2)) {
    return CrystalSystem::Orthorhombic;
  }

  if (symbolMap["2"].size() == 1 || symbolMap["m"].size() == 1) {
    return CrystalSystem::Monoclinic;
  }

  return CrystalSystem::Triclinic;
}

/**
 * Returns the LatticeSystem of the point group, using the crystal system
 *
 * This function uses the crystal system argument and the coordinate system
 * stored in Group to determine the lattice system. For all crystal systems
 * except trigonal there is a 1:1 correspondence, but for trigonal groups
 * the lattice system can be either rhombohedral or hexagonal.
 *
 * @param crystalSystem :: CrystalSystem of the point group.
 * @return LatticeSystem the point group belongs to.
 */
PointGroup::LatticeSystem PointGroup::getLatticeSystemFromCrystalSystemAndGroup(
    const CrystalSystem &crystalSystem) const {
  switch (crystalSystem) {
  case CrystalSystem::Cubic:
    return LatticeSystem::Cubic;
  case CrystalSystem::Hexagonal:
    return LatticeSystem::Hexagonal;
  case CrystalSystem::Tetragonal:
    return LatticeSystem::Tetragonal;
  case CrystalSystem::Orthorhombic:
    return LatticeSystem::Orthorhombic;
  case CrystalSystem::Monoclinic:
    return LatticeSystem::Monoclinic;
  case CrystalSystem::Triclinic:
    return LatticeSystem::Triclinic;
  default: {
    if (getCoordinateSystem() == Group::Hexagonal) {
      return LatticeSystem::Hexagonal;
    }

    return LatticeSystem::Rhombohedral;
  }
  }
}

/** @return a vector with all possible PointGroup objects */
std::vector<PointGroup_sptr> getAllPointGroups() {
  std::vector<std::string> allSymbols =
      PointGroupFactory::Instance().getAllPointGroupSymbols();

  std::vector<PointGroup_sptr> out;
  for (auto it = allSymbols.begin(); it != allSymbols.end(); ++it) {
    out.push_back(PointGroupFactory::Instance().createPointGroup(*it));
  }

  return out;
}

/// Returns a multimap with crystal system as key and point groups as values.
PointGroupCrystalSystemMap getPointGroupsByCrystalSystem() {
  PointGroupCrystalSystemMap map;

  std::vector<PointGroup_sptr> pointGroups = getAllPointGroups();
  for (size_t i = 0; i < pointGroups.size(); ++i) {
    map.insert(std::make_pair(pointGroups[i]->crystalSystem(), pointGroups[i]));
  }

  return map;
}

/// Return a human-readable string for the given crystal system
std::string
getCrystalSystemAsString(const PointGroup::CrystalSystem &crystalSystem) {
  switch (crystalSystem) {
  case PointGroup::CrystalSystem::Cubic:
    return "Cubic";
  case PointGroup::CrystalSystem::Tetragonal:
    return "Tetragonal";
  case PointGroup::CrystalSystem::Hexagonal:
    return "Hexagonal";
  case PointGroup::CrystalSystem::Trigonal:
    return "Trigonal";
  case PointGroup::CrystalSystem::Orthorhombic:
    return "Orthorhombic";
  case PointGroup::CrystalSystem::Monoclinic:
    return "Monoclinic";
  default:
    return "Triclinic";
  }
}

/// Returns the crystal system enum that corresponds to the supplied string or
/// throws an invalid_argument exception.
PointGroup::CrystalSystem
getCrystalSystemFromString(const std::string &crystalSystem) {
  std::string crystalSystemLC = boost::algorithm::to_lower_copy(crystalSystem);

  if (crystalSystemLC == "cubic") {
    return PointGroup::CrystalSystem::Cubic;
  } else if (crystalSystemLC == "tetragonal") {
    return PointGroup::CrystalSystem::Tetragonal;
  } else if (crystalSystemLC == "hexagonal") {
    return PointGroup::CrystalSystem::Hexagonal;
  } else if (crystalSystemLC == "trigonal") {
    return PointGroup::CrystalSystem::Trigonal;
  } else if (crystalSystemLC == "orthorhombic") {
    return PointGroup::CrystalSystem::Orthorhombic;
  } else if (crystalSystemLC == "monoclinic") {
    return PointGroup::CrystalSystem::Monoclinic;
  } else if (crystalSystemLC == "triclinic") {
    return PointGroup::CrystalSystem::Triclinic;
  } else {
    throw std::invalid_argument("Not a valid crystal system: '" +
                                crystalSystem + "'.");
  }
}

/// Returns the supplied LatticeSystem as a string.
std::string
getLatticeSystemAsString(const PointGroup::LatticeSystem &latticeSystem) {
  switch (latticeSystem) {
  case PointGroup::LatticeSystem::Cubic:
    return "Cubic";
  case PointGroup::LatticeSystem::Tetragonal:
    return "Tetragonal";
  case PointGroup::LatticeSystem::Hexagonal:
    return "Hexagonal";
  case PointGroup::LatticeSystem::Rhombohedral:
    return "Rhombohedral";
  case PointGroup::LatticeSystem::Orthorhombic:
    return "Orthorhombic";
  case PointGroup::LatticeSystem::Monoclinic:
    return "Monoclinic";
  default:
    return "Triclinic";
  }
}

/// Returns the lattice system enum that corresponds to the supplied string or
/// throws an invalid_argument exception.PointGroup::LatticeSystem
PointGroup::LatticeSystem
getLatticeSystemFromString(const std::string &latticeSystem) {
  std::string latticeSystemLC = boost::algorithm::to_lower_copy(latticeSystem);

  if (latticeSystemLC == "cubic") {
    return PointGroup::LatticeSystem::Cubic;
  } else if (latticeSystemLC == "tetragonal") {
    return PointGroup::LatticeSystem::Tetragonal;
  } else if (latticeSystemLC == "hexagonal") {
    return PointGroup::LatticeSystem::Hexagonal;
  } else if (latticeSystemLC == "rhombohedral") {
    return PointGroup::LatticeSystem::Rhombohedral;
  } else if (latticeSystemLC == "orthorhombic") {
    return PointGroup::LatticeSystem::Orthorhombic;
  } else if (latticeSystemLC == "monoclinic") {
    return PointGroup::LatticeSystem::Monoclinic;
  } else if (latticeSystemLC == "triclinic") {
    return PointGroup::LatticeSystem::Triclinic;
  } else {
    throw std::invalid_argument("Not a valid lattice system: '" +
                                latticeSystem + "'.");
  }
}

bool CrystalSystemComparator::
operator()(const PointGroup::CrystalSystem &lhs,
           const PointGroup::CrystalSystem &rhs) const {
  return static_cast<int>(lhs) < static_cast<int>(rhs);
}

} // namespace Mantid
} // namespace Geometry
