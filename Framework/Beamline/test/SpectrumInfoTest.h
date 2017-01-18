#ifndef MANTID_BEAMLINE_SPECTRUMINFOTEST_H_
#define MANTID_BEAMLINE_SPECTRUMINFOTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidBeamline/SpectrumInfo.h"
#include "MantidBeamline/SpectrumDefinition.h"

using namespace Mantid::Beamline;

class SpectrumInfoTest : public CxxTest::TestSuite {
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static SpectrumInfoTest *createSuite() { return new SpectrumInfoTest(); }
  static void destroySuite(SpectrumInfoTest *suite) { delete suite; }

  void test_size() {
    TS_ASSERT_EQUALS(SpectrumInfo(0).size(), 0);
    TS_ASSERT_EQUALS(SpectrumInfo(1).size(), 1);
  }

  void test_spectrumDefinition() {
    SpectrumInfo info(1);
    TS_ASSERT_EQUALS(info.spectrumDefinition(0).size(), 0);
  }

  void test_setSpectrumDefinition() {
    SpectrumDefinition def;
    def.add(7, 5);
    TS_ASSERT_EQUALS(def.size(), 1);
    SpectrumInfo info(3);
    info.setSpectrumDefinition(1, def);
    TS_ASSERT_EQUALS(info.spectrumDefinition(1)[0],
                     (std::pair<size_t, size_t>(7, 5)));
    TS_ASSERT_EQUALS(def.size(), 1);
  }

  void test_setSpectrumDefinition_move() {
    SpectrumDefinition def;
    def.add(7, 5);
    TS_ASSERT_EQUALS(def.size(), 1);
    SpectrumInfo info(3);
    info.setSpectrumDefinition(1, std::move(def));
    TS_ASSERT_EQUALS(info.spectrumDefinition(1)[0],
                     (std::pair<size_t, size_t>(7, 5)));
    TS_ASSERT_EQUALS(def.size(), 0);
  }

  void test_setSpectrumDefinition_is_thread_safe() {
    SpectrumInfo info(10000);
    int64_t size = static_cast<int64_t>(info.size());
    auto copy(info); // Make a copy to exercise the COW mechanism.
#pragma omp parallel for
    for (int64_t i = 0; i < size; ++i) {
      SpectrumDefinition def;
      def.add(i);
      info.setSpectrumDefinition(i, def);
    }
    for (int64_t i = 0; i < size; ++i) {
      TS_ASSERT_EQUALS(info.spectrumDefinition(i)[0],
                       (std::pair<size_t, size_t>(i, 0)));
    }
  }
};

#endif /* MANTID_BEAMLINE_SPECTRUMINFOTEST_H_ */
