#ifndef MANTID_ALGORITHMS_CORELLICROSSCORRELATETEST_H_
#define MANTID_ALGORITHMS_CORELLICROSSCORRELATETEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidAlgorithms/CorelliCrossCorrelate.h"
#include "MantidKernel/DateAndTime.h"
#include "MantidDataObjects/EventWorkspace.h"
#include "MantidKernel/TimeSeriesProperty.h"
#include <iostream>
#include <iomanip>


using Mantid::Algorithms::CorelliCrossCorrelate;
using namespace Mantid::API;
using namespace Mantid::DataObjects;
using namespace Mantid::Kernel;

class CorelliCrossCorrelateTest : public CxxTest::TestSuite
{
public:
  // This pair of boilerplate methods prevent the suite being created statically
  // This means the constructor isn't called when running other tests
  static CorelliCrossCorrelateTest *createSuite() { return new CorelliCrossCorrelateTest(); }
  static void destroySuite( CorelliCrossCorrelateTest *suite ) { delete suite; }


  void test_Init()
  {
    CorelliCrossCorrelate alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
  }
  
  void test_exec()
  {
    // Name of the output workspace.
    std::string outWSName("CorelliCrossCorrelateTest_OutputWS");

    IAlgorithm_sptr lei = AlgorithmFactory::Instance().create("LoadEmptyInstrument", 1);
    lei->initialize();
    lei->setPropertyValue("Filename", "CORELLI_Definition.xml");
    lei->setPropertyValue("OutputWorkspace", "CorelliCrossCorrelateTest_OutputWS");
    lei->setPropertyValue("MakeEventWorkspace", "1");
    lei->execute();

    EventWorkspace_sptr ws;
    ws = AnalysisDataService::Instance().retrieveWS<EventWorkspace>("CorelliCrossCorrelateTest_OutputWS");
    ws->sortAll(TOF_SORT, NULL);

    DateAndTime startTime("2007-11-30T16:17:00");
    EventList *evlist = ws->getEventListPtr(0);

    evlist->addEventQuickly( TofEvent(double(10.0),startTime+double(0.007)));
    evlist->addEventQuickly( TofEvent(double(100.0),startTime+double(0.012)));
    evlist->addEventQuickly( TofEvent(double(1000.0),startTime+double(0.012)));
    evlist->addEventQuickly( TofEvent(double(10000.0),startTime+double(0.012)));
    evlist->addEventQuickly( TofEvent(double(1222.0),startTime+double(0.03)));

    ws->getAxis(0)->setUnit("TOF");

    double freq = 293.383;
    double period = 1/freq;
    auto tdc = new TimeSeriesProperty<int>("chopper4_TDC");
    for (int i=0; i<10; i++){
      double tdcTime=i*period;
      tdc->addValue(startTime+tdcTime,1);
    }
    ws->mutableRun().addLogData(tdc);

    auto motorSpeed = new TimeSeriesProperty<double>("BL9:Chop:Skf4:MotorSpeed");
    motorSpeed->addValue(startTime,freq);
    ws->mutableRun().addLogData(motorSpeed);

    CorelliCrossCorrelate alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("InputWorkspace", "CorelliCrossCorrelateTest_OutputWS") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("OutputWorkspace", "CorelliCrossCorrelateTest_OutputWS") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("TimingOffset", "20000") );
    TS_ASSERT_THROWS_NOTHING( alg.execute(); );
    TS_ASSERT( alg.isExecuted() );
    
    // Retrieve the workspace from data service. TODO: Change to your desired type
    TS_ASSERT_THROWS_NOTHING( ws = AnalysisDataService::Instance().retrieveWS<EventWorkspace>("CorelliCrossCorrelateTest_OutputWS") );
    TS_ASSERT(ws);
    if (!ws) return;
    
    std::vector<WeightedEvent>& events = evlist->getWeightedEvents();

    TS_ASSERT_DELTA(events[0].weight(),-1.99392,0.00001)
    TS_ASSERT_DELTA(events[1].weight(),-1.99392,0.00001)
    TS_ASSERT_DELTA(events[2].weight(),2.00612,0.00001)
    TS_ASSERT_DELTA(events[3].weight(),2.00612,0.00001)
    TS_ASSERT_DELTA(events[4].weight(),-1.99392,0.00001)

    // Remove workspace from the data service.
    AnalysisDataService::Instance().remove(outWSName);
  }
  
};


#endif /* MANTID_ALGORITHMS_CORELLICROSSCORRELATETEST_H_ */
