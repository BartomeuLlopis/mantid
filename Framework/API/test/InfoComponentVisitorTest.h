#ifndef MANTID_API_INFOCOMPONENTVISITORTEST_H_
#define MANTID_API_INFOCOMPONENTVISITORTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidKernel/V3D.h"
#include "MantidGeometry/IComponent.h"
#include "MantidAPI/InfoComponentVisitor.h"
#include "MantidGeometry/Instrument/ParameterMap.h"
#include "MantidBeamline/ComponentInfo.h"
#include "MantidTestHelpers/ComponentCreationHelper.h"
#include <set>

using Mantid::API::InfoComponentVisitor;
using Mantid::Kernel::V3D;
using namespace ComponentCreationHelper;

class InfoComponentVisitorTest : public CxxTest::TestSuite {
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static InfoComponentVisitorTest *createSuite() {
    return new InfoComponentVisitorTest();
  }
  static void destroySuite(InfoComponentVisitorTest *suite) { delete suite; }

  void test_visitor_basic_sanity_check() {

    // Create a very basic instrument to visit
    auto visitee = createMinimalInstrument(V3D(0, 0, 0) /*source pos*/,
                                           V3D(10, 0, 0) /*sample pos*/
                                           ,
                                           V3D(11, 0, 0) /*detector position*/);

    Mantid::Geometry::ParameterMap pmap;

    // Create the visitor.
    InfoComponentVisitor visitor(1, [](const Mantid::detid_t) { return 0; },
                                 pmap);

    // Visit everything
    visitee->registerContents(visitor);

    TSM_ASSERT_EQUALS("Should have registered 4 components", visitor.size(), 4);
  }

  void test_visitor_detector_indexes_check() {

    // Create a very basic instrument to visit
    auto visitee = createMinimalInstrument(V3D(0, 0, 0) /*source pos*/,
                                           V3D(10, 0, 0) /*sample pos*/
                                           ,
                                           V3D(11, 0, 0) /*detector position*/);

    Mantid::Geometry::ParameterMap pmap;
    // Create the visitor.
    const size_t detectorIndex = 0;
    InfoComponentVisitor visitor(
        1, [&](const Mantid::detid_t) { return detectorIndex; }, pmap);

    // Visit everything
    visitee->registerContents(visitor);

    auto componentInfo = visitor.makeComponentInfo();

    /*
     * Now lets check the cached contents of our visitor to check
     * it did the job correctly.
    */

    TSM_ASSERT_EQUALS("Single detector should have index of 0",
                      componentInfo->detectorIndices(detectorIndex),
                      std::vector<size_t>{detectorIndex});

    TS_ASSERT_EQUALS(componentInfo->detectorIndices(1), std::vector<size_t>{});
    TS_ASSERT_EQUALS(componentInfo->detectorIndices(2), std::vector<size_t>{});
    // Last thing registered is always the Instrument  which is an Assembly
    // containing all detectors
    TS_ASSERT_EQUALS(componentInfo->detectorIndices(3),
                     std::vector<size_t>{detectorIndex});
  }

  void test_visitor_component_check() {
    // Create a very basic instrument to visit
    auto visitee = createMinimalInstrument(V3D(0, 0, 0) /*source pos*/,
                                           V3D(10, 0, 0) /*sample pos*/
                                           ,
                                           V3D(11, 0, 0) /*detector position*/);

    Mantid::Geometry::ParameterMap pmap;
    // Create the visitor.
    InfoComponentVisitor visitor(1, [](const Mantid::detid_t) { return 0; },
                                 pmap);

    // Visit everything
    visitee->registerContents(visitor);

    std::set<Mantid::Geometry::ComponentID> componentIds(
        visitor.componentIds().begin(), visitor.componentIds().end());
    TSM_ASSERT_EQUALS("Expect 4 component Ids", componentIds.size(), 4);

    TSM_ASSERT_EQUALS("Should contain the instrument id", 1,
                      componentIds.count(visitee->getComponentID()));
    TSM_ASSERT_EQUALS(
        "Should contain the sample id", 1,
        componentIds.count(visitee->getComponentByName("some-surface-holder")
                               ->getComponentID()));
    TSM_ASSERT_EQUALS("Should contain the source id", 1,
                      componentIds.count(visitee->getComponentByName("source")
                                             ->getComponentID()));
    TSM_ASSERT_EQUALS(
        "Should contain the detector id", 1,
        componentIds.count(
            visitee->getComponentByName("point-detector")->getComponentID()));
  }
};

#endif /* MANTID_API_INFOCOMPONENTVISITORTEST_H_ */
