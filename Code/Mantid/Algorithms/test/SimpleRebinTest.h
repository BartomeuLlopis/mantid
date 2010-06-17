#ifndef SIMPLEREBINTEST_H_
#define SIMPLEREBINTEST_H_

#include <cxxtest/TestSuite.h>

#include "MantidDataObjects/Workspace1D.h"
#include "MantidDataObjects/Workspace2D.h"
#include "MantidDataObjects/EventWorkspace.h"
#include "MantidAPI/AnalysisDataService.h"
#include "MantidAlgorithms/SimpleRebin.h"
#include "MantidAPI/WorkspaceProperty.h"

using namespace Mantid;
using namespace Mantid::Kernel;
using namespace Mantid::DataObjects;
using namespace Mantid::API;
using namespace Mantid::Algorithms;


class SimpleRebinTest : public CxxTest::TestSuite
{
public:
  double BIN_DELTA;
  int NUMPIXELS, NUMBINS;

  SimpleRebinTest()
  {
    BIN_DELTA = 2.0;
    NUMPIXELS = 20;
    NUMBINS = 50;
  }


  void testworkspace1D_dist()
  {
    Workspace1D_sptr test_in1D = Create1DWorkspace(50);
    test_in1D->isDistribution(true);
    AnalysisDataService::Instance().add("test_in1D", test_in1D);

    SimpleRebin rebin;
    rebin.initialize();
    rebin.setPropertyValue("InputWorkspace","test_in1D");
    rebin.setPropertyValue("OutputWorkspace","test_out");
    // Check it fails if "Params" property not set
    TS_ASSERT_THROWS( rebin.execute(), std::runtime_error );
    TS_ASSERT( ! rebin.isExecuted() );
    // Now set the property
    rebin.setPropertyValue("Params", "1.5,2.0,20,-0.1,30,1.0,35");
    TS_ASSERT(rebin.execute());
    TS_ASSERT(rebin.isExecuted());
    MatrixWorkspace_sptr rebindata = boost::dynamic_pointer_cast<MatrixWorkspace>(AnalysisDataService::Instance().retrieve("test_out"));
    const Mantid::MantidVec outX=rebindata->dataX(0);
    const Mantid::MantidVec outY=rebindata->dataY(0);
    const Mantid::MantidVec outE=rebindata->dataE(0);

    TS_ASSERT_DELTA(outX[7],15.5  ,0.000001);
    TS_ASSERT_DELTA(outY[7],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[7], sqrt(4.5)/2.0  ,0.000001);

    TS_ASSERT_DELTA(outX[12],24.2 ,0.000001);
    TS_ASSERT_DELTA(outY[12],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[12],sqrt(5.445)/2.42 ,0.000001);

    TS_ASSERT_DELTA(outX[17],32.0  ,0.000001);
    TS_ASSERT_DELTA(outY[17],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[17],sqrt(2.25) ,0.000001);
    bool dist=rebindata->isDistribution();
    TS_ASSERT(dist);
    AnalysisDataService::Instance().remove("test_in1D");
    AnalysisDataService::Instance().remove("test_out");
  }

  void testworkspace1D_nondist()
  {
    Workspace1D_sptr test_in1D = Create1DWorkspace(50);
    AnalysisDataService::Instance().add("test_in1D", test_in1D);

    SimpleRebin rebin;
    rebin.initialize();
    rebin.setPropertyValue("InputWorkspace","test_in1D");
    rebin.setPropertyValue("OutputWorkspace","test_out");
    rebin.setPropertyValue("Params", "1.5,2.0,20,-0.1,30,1.0,35");
    TS_ASSERT(rebin.execute());
    TS_ASSERT(rebin.isExecuted());
    MatrixWorkspace_sptr rebindata = boost::dynamic_pointer_cast<MatrixWorkspace>(AnalysisDataService::Instance().retrieve("test_out"));

    const Mantid::MantidVec outX=rebindata->dataX(0);
    const Mantid::MantidVec outY=rebindata->dataY(0);
    const Mantid::MantidVec outE=rebindata->dataE(0);

    TS_ASSERT_DELTA(outX[7],15.5  ,0.000001);
    TS_ASSERT_DELTA(outY[7],8.0 ,0.000001);
    TS_ASSERT_DELTA(outE[7],sqrt(8.0)  ,0.000001);
    TS_ASSERT_DELTA(outX[12],24.2  ,0.000001);
    TS_ASSERT_DELTA(outY[12],9.68 ,0.000001);
    TS_ASSERT_DELTA(outE[12],sqrt(9.68)  ,0.000001);
    TS_ASSERT_DELTA(outX[17],32  ,0.000001);
    TS_ASSERT_DELTA(outY[17],4.0 ,0.000001);
    TS_ASSERT_DELTA(outE[17],sqrt(4.0)  ,0.000001);
    bool dist=rebindata->isDistribution();
    TS_ASSERT(!dist);
    AnalysisDataService::Instance().remove("test_in1D");
    AnalysisDataService::Instance().remove("test_out");
  }

  void testworkspace2D_dist()
  {
    Workspace2D_sptr test_in2D = Create2DWorkspace(50,20);
    test_in2D->isDistribution(true);
    AnalysisDataService::Instance().add("test_in2D", test_in2D);

    SimpleRebin rebin;
    rebin.initialize();
    rebin.setPropertyValue("InputWorkspace","test_in2D");
    rebin.setPropertyValue("OutputWorkspace","test_out");
    rebin.setPropertyValue("Params", "1.5,2.0,20,-0.1,30,1.0,35");
    TS_ASSERT(rebin.execute());
    TS_ASSERT(rebin.isExecuted());
    MatrixWorkspace_sptr rebindata = boost::dynamic_pointer_cast<MatrixWorkspace>(AnalysisDataService::Instance().retrieve("test_out"));

    const Mantid::MantidVec outX=rebindata->dataX(5);
    const Mantid::MantidVec outY=rebindata->dataY(5);
    const Mantid::MantidVec outE=rebindata->dataE(5);
    TS_ASSERT_DELTA(outX[7],15.5  ,0.000001);
    TS_ASSERT_DELTA(outY[7],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[7],sqrt(4.5)/2.0  ,0.000001);

    TS_ASSERT_DELTA(outX[12],24.2 ,0.000001);
    TS_ASSERT_DELTA(outY[12],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[12],sqrt(5.445)/2.42  ,0.000001);

    TS_ASSERT_DELTA(outX[17],32.0  ,0.000001);
    TS_ASSERT_DELTA(outY[17],3.0 ,0.000001);
    TS_ASSERT_DELTA(outE[17],sqrt(2.25)  ,0.000001);
    bool dist=rebindata->isDistribution();
    TS_ASSERT(dist);

    AnalysisDataService::Instance().remove("test_in2D");
    AnalysisDataService::Instance().remove("test_out");
  }

  void xtestEventWorkspace()
  {
    EventWorkspace_sptr test_in = CreateEventWorkspace(NUMBINS, NUMPIXELS);
    AnalysisDataService::Instance().add("test_inEvent", test_in);

    const EventList el(test_in->getEventList(1));
    TS_ASSERT_EQUALS( el.dataX()[0], 0);
    TS_ASSERT_EQUALS( el.dataX()[1], BIN_DELTA);
    //Because of the way the events were faked, bins 0 to pixel-1 are 0, rest are 1
    TS_ASSERT_EQUALS( el.dataY()[0], 1);
    TS_ASSERT_EQUALS( el.dataY()[1], 1);
    TS_ASSERT_EQUALS( el.dataY()[NUMBINS-2], 1); //The last bin
    

//    // Mask a couple of bins for a test
//    test_in2D->maskBin(10,4);
//    test_in2D->maskBin(10,5);
//
    SimpleRebin rebin;
    rebin.initialize();
    rebin.setPropertyValue("InputWorkspace","test_inEvent");
    rebin.setPropertyValue("OutputWorkspace","test_out");
    rebin.setPropertyValue("Params", "1.5,2.0,20,-0.1,30,1.0,35");
    TS_ASSERT(rebin.execute());
    TS_ASSERT(rebin.isExecuted());

//    MatrixWorkspace_sptr rebindata = boost::dynamic_pointer_cast<MatrixWorkspace>(AnalysisDataService::Instance().retrieve("test_out"));
//    const Mantid::MantidVec& outX=rebindata->dataX(5);
//    const Mantid::MantidVec& outY=rebindata->dataY(5);
//    const Mantid::MantidVec& outE=rebindata->dataE(5);
//    TS_ASSERT_DELTA(outX[7],15.5  ,0.000001);
//    TS_ASSERT_DELTA(outY[7],8.0 ,0.000001);
//    TS_ASSERT_DELTA(outE[7],sqrt(8.0)  ,0.000001);
//    TS_ASSERT_DELTA(outX[12],24.2  ,0.000001);
//    TS_ASSERT_DELTA(outY[12],9.68 ,0.000001);
//    TS_ASSERT_DELTA(outE[12],sqrt(9.68)  ,0.000001);
//    TS_ASSERT_DELTA(outX[17],32  ,0.000001);
//    TS_ASSERT_DELTA(outY[17],4.0 ,0.000001);
//    TS_ASSERT_DELTA(outE[17],sqrt(4.0)  ,0.000001);
//    bool dist=rebindata->isDistribution();
//    TS_ASSERT(!dist);
//
//    // Test that the masking was propagated correctly
//    TS_ASSERT( test_in2D->hasMaskedBins(10) );
//    TS_ASSERT( rebindata->hasMaskedBins(10) );
//    TS_ASSERT_THROWS_NOTHING (
//      const MatrixWorkspace::MaskList& masks = rebindata->maskedBins(10);
//      TS_ASSERT_EQUALS( masks.size(),1 )
//      TS_ASSERT_EQUALS( masks.begin()->first, 1 )
//      TS_ASSERT_EQUALS( masks.begin()->second, 0.75 )
//    );
//
//    AnalysisDataService::Instance().remove("test_in2D");
//    AnalysisDataService::Instance().remove("test_out");
  }
    


private:

  EventWorkspace_sptr CreateEventWorkspace(int numbins, int numpixels)
  {
    EventWorkspace_sptr retVal(new EventWorkspace);
    retVal->initialize(numpixels,numbins,numbins-1);

    //Create the original X axis to histogram on.
    //Create the x-axis for histogramming.
    Kernel::cow_ptr<MantidVec> axis;
    MantidVec& xRef = axis.access();
    xRef.resize(numbins);
    for (int i = 0; i < numbins; ++i)
      xRef[i] = i*BIN_DELTA;


    //Make up some data for each pixels
    for (int i=0; i< numpixels; i++)
    {
      //Create one event for each bin
      EventList& events = retVal->getEventList(i);
      for (double ie=0; ie<numbins-1; ie++)
      {
        //Create a list of events in order, one per bin.
        events += TofEvent((ie*BIN_DELTA)+0.5, 1);
  }
    	retVal->setX(i,axis);
    }

    return retVal;
  }


  Workspace1D_sptr Create1DWorkspace(int size)
  {
    boost::shared_ptr<Mantid::MantidVec> y1(new Mantid::MantidVec(size-1,3.0));
    boost::shared_ptr<Mantid::MantidVec> e1(new Mantid::MantidVec(size-1,sqrt(3.0)));
    Workspace1D_sptr retVal(new Workspace1D);
    retVal->initialize(1,size,size-1);
    double j=1.0;
    for (int i=0; i<size; i++)
    {
      retVal->dataX()[i]=j*0.5;
      j+=1.5;
    }
    retVal->setData(y1,e1);
    return retVal;
  }
  
  Workspace2D_sptr Create2DWorkspace(int xlen, int ylen)
  {
    boost::shared_ptr<Mantid::MantidVec> x1(new Mantid::MantidVec(xlen,0.0));
    boost::shared_ptr<Mantid::MantidVec> y1(new Mantid::MantidVec(xlen-1,3.0));
    boost::shared_ptr<Mantid::MantidVec> e1(new Mantid::MantidVec(xlen-1,sqrt(3.0)));

    Workspace2D_sptr retVal(new Workspace2D);
    retVal->initialize(ylen,xlen,xlen-1);
    double j=1.0;

    for (int i=0; i<xlen; i++)
    {
      (*x1)[i]=j*0.5;
      j+=1.5;
    }

    for (int i=0; i< ylen; i++)
    {
      retVal->setX(i,x1);
      retVal->setData(i,y1,e1);
    }

    return retVal;
  }


};
#endif /* SIMPLEREBINTEST */
