#ifndef MANTID_ALGORITHMS_LINEPROFILETEST_H_
#define MANTID_ALGORITHMS_LINEPROFILETEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidAlgorithms/LineProfile.h"

#include "MantidAlgorithms/CompareWorkspaces.h"
#include "MantidAPI/Axis.h"
#include "MantidAPI/MatrixWorkspace.h"
#include "MantidTestHelpers/WorkspaceCreationHelper.h"

using Mantid::Algorithms::CompareWorkspaces;
using Mantid::Algorithms::LineProfile;
using namespace Mantid::API;
using namespace Mantid::DataObjects;
using namespace Mantid::HistogramData;
using namespace Mantid::Kernel;
using namespace WorkspaceCreationHelper;

class LineProfileTest : public CxxTest::TestSuite {
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static LineProfileTest *createSuite() { return new LineProfileTest(); }
  static void destroySuite( LineProfileTest *suite ) { delete suite; }


  void test_Init()
  {
    LineProfile alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
  }

  void test_profile_of_single_horizontal_spectrum()
  {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);
    const auto inputXMode = inputWS->histogram(0).xMode();

    const int start = 2;
    const int end = nBins - 2;
    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", static_cast<double>(nHist) / 2))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 0.49))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", static_cast<double>(end)))
    TS_ASSERT_THROWS_NOTHING(alg.execute())
    TS_ASSERT(alg.isExecuted())

    Workspace2D_sptr outputWS = alg.getProperty("OutputWorkspace");
    TS_ASSERT(outputWS);
    TS_ASSERT_EQUALS(outputWS->getNumberHistograms(), 1)
    const auto hist = outputWS->histogram(0);
    TS_ASSERT_EQUALS(hist.xMode(), inputXMode)
    for (size_t i = 0; i < hist.x().size(); ++i) {
      TS_ASSERT_EQUALS(hist.x()[i], i + start)
    }
    for (const auto y : hist.y()) {
      TS_ASSERT_EQUALS(y, inputWS->y(0)[0])
    }
    for (const auto e : hist.e()) {
      TS_ASSERT_EQUALS(e, inputWS->e(0)[0])
    }
    const auto vertAxis = outputWS->getAxis(1);
    TS_ASSERT_EQUALS(vertAxis->getValue(0), static_cast<double>(nHist) / 2 - 0.5)
    TS_ASSERT_EQUALS(vertAxis->getValue(1), static_cast<double>(nHist) / 2 + 0.5)
  }

  void test_horizontal_profile_linewidth_outside_workspace()
  {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);
    const auto inputXMode = inputWS->histogram(0).xMode();

    const int start = 2;
    const int end = nBins - 2;
    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", 1.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 3.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", static_cast<double>(end)))
    TS_ASSERT_THROWS_NOTHING(alg.execute())
    TS_ASSERT(alg.isExecuted())

    Workspace2D_sptr outputWS = alg.getProperty("OutputWorkspace");
    TS_ASSERT(outputWS);
    TS_ASSERT_EQUALS(outputWS->getNumberHistograms(), 1)
    const auto hist = outputWS->histogram(0);
    TS_ASSERT_EQUALS(hist.xMode(), inputXMode)
    for (size_t i = 0; i < hist.x().size(); ++i) {
      TS_ASSERT_EQUALS(hist.x()[i], i + start)
    }
    for (const auto y : hist.y()) {
      TS_ASSERT_EQUALS(y, inputWS->y(0)[0])
    }
    for (const auto e : hist.e()) {
      TS_ASSERT_EQUALS(e, std::sqrt(4 * inputWS->e(0)[0] * inputWS->e(0)[0]) / 4)
    }
    const auto vertAxis = outputWS->getAxis(1);
    TS_ASSERT_EQUALS(vertAxis->getValue(0), 1.0)
    TS_ASSERT_EQUALS(vertAxis->getValue(1), 5.0)
  }

  void test_vertical_profile() {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);

    const int start = 2;
    const int end = nHist - 2;
    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Vertical"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", static_cast<double>(nBins) / 2))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 3.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", static_cast<double>(end)))
    TS_ASSERT_THROWS_NOTHING(alg.execute())
    TS_ASSERT(alg.isExecuted())

    Workspace2D_sptr outputWS = alg.getProperty("OutputWorkspace");
    TS_ASSERT(outputWS);
    TS_ASSERT_EQUALS(outputWS->getNumberHistograms(), 1)
    const auto hist = outputWS->histogram(0);
    TS_ASSERT_EQUALS(hist.xMode(), Histogram::XMode::Points)
    for (size_t i = 0; i < hist.x().size(); ++i) {
      TS_ASSERT_EQUALS(hist.x()[i], i + start)
    }
    for (const auto y : hist.y()) {
      TS_ASSERT_EQUALS(y, inputWS->y(0)[0])
    }
    for (const auto e : hist.e()) {
      TS_ASSERT_EQUALS(e, std::sqrt(7 * inputWS->e(0)[0] * inputWS->e(0)[0]) / 7)
    }
    const auto vertAxis = outputWS->getAxis(1);
    TS_ASSERT_EQUALS(vertAxis->getValue(0), static_cast<double>(nBins) / 2 - 3.5)
    TS_ASSERT_EQUALS(vertAxis->getValue(1), static_cast<double>(nBins) / 2 + 3.5)
  }

  void test_vertical_profile_over_entire_workspace() {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);

    const int start = -1;
    const int end = nHist + 1;
    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Vertical"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", static_cast<double>(nBins) / 2))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 3.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", static_cast<double>(end)))
    TS_ASSERT_THROWS_NOTHING(alg.execute())
    TS_ASSERT(alg.isExecuted())

    Workspace2D_sptr outputWS = alg.getProperty("OutputWorkspace");
    TS_ASSERT(outputWS);
    TS_ASSERT_EQUALS(outputWS->getNumberHistograms(), 1)
    const auto hist = outputWS->histogram(0);
    TS_ASSERT_EQUALS(hist.xMode(), Histogram::XMode::Points)
    for (size_t i = 0; i < hist.x().size(); ++i) {
      TS_ASSERT_EQUALS(hist.x()[i], i + 1)
    }
    for (const auto y : hist.y()) {
      TS_ASSERT_EQUALS(y, inputWS->y(0)[0])
    }
    for (const auto e : hist.e()) {
      TS_ASSERT_EQUALS(e, std::sqrt(7 * inputWS->e(0)[0] * inputWS->e(0)[0]) / 7)
    }
    const auto vertAxis = outputWS->getAxis(1);
    TS_ASSERT_EQUALS(vertAxis->getValue(0), static_cast<double>(nBins) / 2 - 3.5)
    TS_ASSERT_EQUALS(vertAxis->getValue(1), static_cast<double>(nBins) / 2 + 3.5)
  }

  void test_length() {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);

    const int start = 2;
    const int end = nBins - 2;
    LineProfile algWithEnd;
    // Don't put output in ADS by default
    algWithEnd.setChild(true);
    algWithEnd.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(algWithEnd.initialize())
    TS_ASSERT(algWithEnd.isInitialized())
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("Centre", static_cast<double>(nHist) / 2))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("HalfWidth", 0.49))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.setProperty("End", static_cast<double>(end)))
    TS_ASSERT_THROWS_NOTHING(algWithEnd.execute())
    TS_ASSERT(algWithEnd.isExecuted())

    Workspace2D_sptr outputEndWS = algWithEnd.getProperty("OutputWorkspace");

    LineProfile algWithLength;
    // Don't put output in ADS by default
    algWithLength.setChild(true);
    algWithLength.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(algWithLength.initialize())
    TS_ASSERT(algWithLength.isInitialized())
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("Centre", static_cast<double>(nHist) / 2))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("HalfWidth", 0.49))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("Start", static_cast<double>(start)))
    TS_ASSERT_THROWS_NOTHING(algWithLength.setProperty("Length", static_cast<double>(end - start)))
    TS_ASSERT_THROWS_NOTHING(algWithLength.execute())
    TS_ASSERT(algWithLength.isExecuted())

    Workspace2D_sptr outputLengthWS = algWithLength.getProperty("OutputWorkspace");
    TS_ASSERT_DIFFERS(outputEndWS.get(), outputLengthWS.get())
    CompareWorkspaces comparison;
    comparison.initialize();
    comparison.setProperty("Workspace1", outputEndWS);
    comparison.setProperty("Workspace2", outputLengthWS);
    comparison.setProperty("CheckAllData", true);
    comparison.execute();
    const bool outputsEqual = comparison.getProperty("Result");
    TS_ASSERT(outputsEqual)
  }

  void test_failure_when_profile_outside_workspace() {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);

    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", -10.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 1.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", 2.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", 9.0))
    TS_ASSERT_THROWS_ANYTHING(alg.execute())
    TS_ASSERT(!alg.isExecuted())
  }

  void test_ignore_special_values() {
    const size_t nHist = 13;
    const size_t nBins = 23;
    MatrixWorkspace_sptr inputWS = create2DWorkspace154(nHist, nBins);
    inputWS->mutableY(2)[6] = std::numeric_limits<double>::quiet_NaN();
    inputWS->mutableY(3)[13] = std::numeric_limits<double>::infinity();
    const auto inputXMode = inputWS->histogram(0).xMode();

    LineProfile alg;
    // Don't put output in ADS by default
    alg.setChild(true);
    alg.setRethrows(true);
    TS_ASSERT_THROWS_NOTHING(alg.initialize())
    TS_ASSERT(alg.isInitialized())
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("InputWorkspace", inputWS))
    TS_ASSERT_THROWS_NOTHING(alg.setPropertyValue("OutputWorkspace", "_unused_for_child"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Direction", "Horizontal"))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Centre", 3.5))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("HalfWidth", 0.5))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("Start", 0.0))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("End", static_cast<double>(nBins)))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("IgnoreNans", true))
    TS_ASSERT_THROWS_NOTHING(alg.setProperty("IgnoreInfs", true))
    TS_ASSERT_THROWS_NOTHING(alg.execute())
    TS_ASSERT(alg.isExecuted())

    Workspace2D_sptr outputWS = alg.getProperty("OutputWorkspace");
    TS_ASSERT(outputWS);
    TS_ASSERT_EQUALS(outputWS->getNumberHistograms(), 1)
    const auto hist = outputWS->histogram(0);
    TS_ASSERT_EQUALS(hist.xMode(), inputXMode)
    for (size_t i = 0; i < hist.x().size(); ++i) {
      TS_ASSERT_EQUALS(hist.x()[i], i + 1)
    }
    for (const auto y : hist.y()) {
      TS_ASSERT_EQUALS(y, inputWS->y(0)[0])
    }
    for (size_t i = 0; i < hist.e().size(); ++i) {
      if (i == 6 || i == 13) {
        TS_ASSERT_EQUALS(hist.e()[i], inputWS->e(0)[0])
        continue;
      }
      TS_ASSERT_EQUALS(hist.e()[i], std::sqrt(2 * inputWS->e(0)[0] *inputWS->e(0)[0]) / 2)
    }
    const auto vertAxis = outputWS->getAxis(1);
    TS_ASSERT_EQUALS(vertAxis->getValue(0), 3)
    TS_ASSERT_EQUALS(vertAxis->getValue(1), 5)
  }
};


#endif /* MANTID_ALGORITHMS_LINEPROFILETEST_H_ */
