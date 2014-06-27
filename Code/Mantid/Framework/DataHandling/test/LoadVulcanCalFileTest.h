#ifndef MANTID_DATAHANDLING_LOCALVULCANCALFILETEST_H_
#define MANTID_DATAHANDLING_LOCALVULCANCALFILETEST_H_

#include <cxxtest/TestSuite.h>
#include "MantidKernel/Timer.h"
#include "MantidKernel/System.h"
#include <iostream>
#include <iomanip>

#include "MantidDataHandling/LoadVulcanCalFile.h"
#include "MantidDataObjects/GroupingWorkspace.h"

using namespace Mantid::DataHandling;
using namespace Mantid::DataObjects;
using namespace Mantid::API;

class LoadVulcanCalFileTest : public CxxTest::TestSuite
{
public:

    
  void test_Init()
  {
    LoadVulcanCalFile alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
  }
  
  void test_exec()
  {
    // Name of the output workspace.
    std::string outWSName("LoadVulcanCalFileTest");
    std::string offsetfilename = "pid_offset_vulcan_new.dat";
    std::string badpixelfilename = "bad_pids_vulcan_new_6867_7323.dat";
  
    LoadVulcanCalFile alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("OffsetFilename", offsetfilename) );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("Grouping", "6Modules"));
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("BadPixelFilename", badpixelfilename ) );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("WorkspaceName", outWSName));
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("BankIDs", "21,22,23,26,27,28") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("EffectiveDIFCs", "16372.601900,16376.951300,16372.096300,16336.622200,16340.822400,16338.777300") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("Effective2Thetas", "90.091000,90.122000,90.089000,89.837000,89.867000,89.852000") );
    TS_ASSERT_THROWS_NOTHING( alg.execute(); );
    TS_ASSERT( alg.isExecuted() );

    // TS_ASSERT_EQUALS(1, 31232);
    return;

    
    std::string title = "offsets_2006_cycle064.cal";

    // Retrieve the workspace from data service. TODO: Change to your desired type
    GroupingWorkspace_sptr groupWS;
    TS_ASSERT_THROWS_NOTHING( groupWS = AnalysisDataService::Instance().retrieveWS<GroupingWorkspace>(outWSName+"_group") );
    TS_ASSERT(groupWS);  if (!groupWS) return;
    TS_ASSERT_EQUALS( groupWS->getTitle(), title);
    TS_ASSERT_EQUALS( int(groupWS->getValue(101001)), 2 );
    TS_ASSERT_EQUALS( int(groupWS->getValue(715079)), 7 );
    //Check if filename is saved
    TS_ASSERT_EQUALS(alg.getPropertyValue("CalFilename"),groupWS->run().getProperty("Filename")->value());

    OffsetsWorkspace_sptr offsetsWS;
    TS_ASSERT_THROWS_NOTHING( offsetsWS = AnalysisDataService::Instance().retrieveWS<OffsetsWorkspace>(outWSName+"_offsets") );
    TS_ASSERT(offsetsWS); if (!offsetsWS) return;
    TS_ASSERT_EQUALS( offsetsWS->getTitle(), title);
    TS_ASSERT_DELTA( offsetsWS->getValue(101001), -0.0497075, 1e-7 );
    TS_ASSERT_DELTA( offsetsWS->getValue(714021), 0.0007437, 1e-7 );
    //Check if filename is saved
    TS_ASSERT_EQUALS(alg.getPropertyValue("CalFilename"),offsetsWS->run().getProperty("Filename")->value());

    SpecialWorkspace2D_sptr maskWS;
    TS_ASSERT_THROWS_NOTHING( maskWS = AnalysisDataService::Instance().retrieveWS<SpecialWorkspace2D>(outWSName+"_mask") );
    TS_ASSERT(maskWS); if (!maskWS) return;
    TS_ASSERT_EQUALS( maskWS->getTitle(), title);
    /*
    TS_ASSERT_EQUALS( int(maskWS->getValue(101001)), 1 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(101003)), 0 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(101008)), 0 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(715079)), 1 );
    */
    TS_ASSERT_EQUALS( int(maskWS->getValue(101001)), 0 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(101003)), 1 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(101008)), 1 );
    TS_ASSERT_EQUALS( int(maskWS->getValue(715079)), 0 );
    TS_ASSERT( !maskWS->getInstrument()->getDetector(101001)->isMasked() );
    TS_ASSERT( maskWS->getInstrument()->getDetector(101003)->isMasked() );
    TS_ASSERT( maskWS->getInstrument()->getDetector(101008)->isMasked() );
    TS_ASSERT( !maskWS->getInstrument()->getDetector(715079)->isMasked() );
    //Check if filename is saved
    TS_ASSERT_EQUALS(alg.getPropertyValue("CalFilename"),maskWS->run().getProperty("Filename")->value());
    // Remove workspace from the data service.
    AnalysisDataService::Instance().remove(outWSName+"_group");
    AnalysisDataService::Instance().remove(outWSName+"_offsets");
    AnalysisDataService::Instance().remove(outWSName+"_mask");
  }


  void test_exec2Banks()
  {
    // Name of the output workspace.
    std::string outWSName("LoadVulcanCalFileTest");
    std::string offsetfilename = "pid_offset_vulcan_new.dat";
    std::string badpixelfilename = "bad_pids_vulcan_new_6867_7323.dat";

    LoadVulcanCalFile alg;
    TS_ASSERT_THROWS_NOTHING( alg.initialize() )
    TS_ASSERT( alg.isInitialized() )
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("OffsetFilename", offsetfilename) );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("Grouping", "2Banks"));
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("BadPixelFilename", badpixelfilename ) );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("WorkspaceName", outWSName));
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("BankIDs", "21,22,23,26,27,28") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("EffectiveDIFCs", "16372.601900,16376.951300,16372.096300,16336.622200,16340.822400,16338.777300") );
    TS_ASSERT_THROWS_NOTHING( alg.setPropertyValue("Effective2Thetas", "90.091000,90.122000,90.089000,89.837000,89.867000,89.852000") );
    TS_ASSERT_THROWS_NOTHING( alg.execute(); );
    TS_ASSERT( alg.isExecuted() );

    TS_ASSERT_EQUALS(1, 31232);
    return;
  }

};


#endif /* MANTID_DATAHANDLING_LOCALVULCANCALFILETEST_H_ */

