/*WIKI* 


This algorithm was developed for the Merlin instrument but may be used with other instruments if appropriate scaling data is available.
The scaling data should give the true centre point location of each pixel detector in the instrument.
This may be obtained by a calibration run and post-processing of the results.
Since the calibration data may vary with time, it is not convenient to store it in the instrument XML definition file.
Instead it can be stored as an ACSII file with the extension ".sca" or within the ".raw" file associated with the data, as data on the
position of each detector (r,theta,phi).

A scaling file (extension .sca) is expected to be an ASCII file with three header lines.
Of these, only the second line is actual read and the first item on this line should 
give the number of detectors described by the file as an integer value.
Each subsequent line after the first three will give the information for one detector with at least the five
ordered values <i>detector_ID</i>, <i>detector_offset</i>, <i>l2</i>, <i>code</i>, <i>theta</i> and <i>phi</i>.
Of these values only the <i>detector_ID</i> and the new position (<i>l2, theta, phi</i>) are used.
The latter three values are taken as defining the true position of the detector
in spherical polar coordinates relative to the origin (sample position).
If a raw file is given the true positions are taken from this instead.

This algorithm creates a parameter map for the instrument that applies a shift to each
detector so that is at the correct position.
Monitors are not moved.
Because the shift of detector locations can alter the effective width of the pixel
it is necessary to apply a scaling factor.
While each shift can have components in all three primary axes (X,Y,Z), it is assumed that a single PSD will maintain the co-linear nature of pixel centres.
The width scaling factor for a pixel <i>i</i> is approximated as average of the left and right side scalings cased by the change
in relative spacings with respect to neighbour pixels.
End of detector pixels only have one scaling value to use.
It is assumed that the scaling is both small and smooth so that the approximate scaling is reasonable.

Scaling and position correction will be reflected in properties of the detector objects including values such as the solid
angle, bounding box, etc.
The detector numbering in Merlin uses sequential numbers for pixels within a PSD and non-sequential jumps between PSDs.
This algorithm uses these jumps to identify individual PSDs.

To apply this algorithm to instruments other than Merlin it may be necessary to modify the code depending on the type of detectors
present and how they are numbered.

If the tube detector performance enhancement is used the results of the algorithm will not be visible in the instrument view in MantidPlot, at the same time all calclations will be performed correctly. 

=== Optional properties ===
ScalingOpt - this integer value controls the way in which the scaling is calculated for pixels that have both left and right values for the scaling.
The default is to just average the two together.
Setting this to 1 causes the maximum scaling to be used and setting it to 2 uses the maximum scaling plus 5% to be used.

===Subalgorithms used===
None


*WIKI*/
// SetScalingPSD
// @author Ronald Fowler
//----------------------------------------------------------------------
// Includes
//----------------------------------------------------------------------
#include "MantidDataHandling/SetScalingPSD.h"
#include "MantidKernel/ArrayProperty.h"
#include "MantidAPI/FileProperty.h"
#include "MantidAPI/WorkspaceValidators.h"
#include <cmath>
#include <fstream>
#include "LoadRaw/isisraw.h"


namespace Mantid
{
namespace DataHandling
{

  // Register the algorithm into the algorithm factory
  DECLARE_ALGORITHM(SetScalingPSD)
  
  /// Sets documentation strings for this algorithm
  void SetScalingPSD::initDocs()
  {
    this->setWikiSummary("For an instrument with Position Sensitive Detectors (PSDs) the \"engineering\" positions of individual detectors may not match the true areas where neutrons are detected. This algorithm reads data on the calibrated location of the detectors and adjusts the parametrized instrument geometry accordingly. ");
    this->setOptionalMessage("For an instrument with Position Sensitive Detectors (PSDs) the 'engineering' positions of individual detectors may not match the true areas where neutrons are detected. This algorithm reads data on the calibrated location of the detectors and adjusts the parametrized instrument geometry accordingly.");
  }
  

  using namespace Kernel;
  using namespace API;
  using namespace Geometry;

  /// Empty default constructor
  SetScalingPSD::SetScalingPSD() :
      Algorithm()
  {
  }

  /** Initialisation method.
   *
   */
  void SetScalingPSD::init()
  {
    // Declare required input parameters for algorithm
    std::vector<std::string> exts;
    exts.push_back(".sca");
    exts.push_back(".raw");
    declareProperty(new FileProperty("ScalingFilename","", FileProperty::Load, exts),
        "The name of the scaling calibrations file to read, including its\n"
        "full or relative path. The file extension must be either .sca or\n"
        ".raw (filenames are case sensitive on linux)" );
    declareProperty(new WorkspaceProperty<>("Workspace","",Direction::InOut),
      "The name of the workspace to apply the scaling to. This must be\n"
      "associated with an instrument appropriate for the scaling file" );
    BoundedValidator<int> *mustBePositive = new BoundedValidator<int>();
    mustBePositive->setLower(0);
    declareProperty("ScalingOption",0, mustBePositive,
      "Control scaling calculation - 0 => use average of left and right\n"
      "scaling (default). 1 => use maximum scaling. 2 => maximum + 5%" );
  }

  /** Executes the algorithm.
   *
   *  @throw runtime_error Thrown if algorithm cannot execute
   */
  void SetScalingPSD::exec()
  {
    // Retrieve the filename and output workspace name from the properties
    m_filename = getPropertyValue("ScalingFilename");
    //m_workspace = getPropertyValue("Workspace");
    m_workspace = getProperty("Workspace");
    m_scalingOption = getProperty("ScalingOption");
    std::vector<Kernel::V3D> truepos;
    processScalingFile(m_filename,truepos);
    //calculateDetectorShifts(truepos);
    
    return;
  }

  /** Read the scaling information from a file (e.g. merlin_detector.sca) or from the RAW file (.raw)
   *  @param scalingFile :: Name of scaling file .sca
   *  @param truepos :: V3D vector of actual positions as read from the file
   *  @return False if unable to open file, True otherwise
   */
  bool SetScalingPSD::processScalingFile(const std::string& scalingFile, std::vector<Kernel::V3D>& truepos)
  {
      // Read the scaling information from a text file (.sca extension) or from a raw file (.raw)
      // This is really corrected positions as (r,theta,phi) for each detector
      // Compare these with the instrument values to determine the change in position and the scaling
      // which may be necessary for each pixel if in a tube.
      // movePos is used to updated positions
      std::map<int,Kernel::V3D> posMap;
      std::map<int,Kernel::V3D>::iterator it;
      std::map<int,double> scaleMap;
      std::map<int,double>::iterator its;

      Instrument_const_sptr instrument = m_workspace->getInstrument();
      if(scalingFile.find(".sca")!=std::string::npos || scalingFile.find(".SCA")!=std::string::npos)
      {
          // read a .sca text format file
          // format consists of a short header followed by one line per detector

          std::ifstream sFile(scalingFile.c_str());
          if (!sFile)
          {
              g_log.error() << "Unable to open scaling file " << scalingFile << std::endl;
              return false;
          }
          std::string str;
          getline(sFile,str); // skip header line should be <filename> generated by <prog>
          int detectorCount;
          getline(sFile,str); // get detector count line
          std::istringstream istr(str);
          istr >> detectorCount;
          if(detectorCount<1)
          {
              g_log.error("Bad detector count in scaling file");
              throw std::runtime_error("Bad detector count in scaling file"); 
          }
          truepos.reserve(detectorCount);
          getline(sFile,str); // skip title line
          int detIdLast=-10;
          Kernel::V3D truPosLast,detPosLast;
         
          Progress prog(this,0.0,0.5,detectorCount);
          // Now loop through lines, one for each detector/monitor. The latter are ignored.
        
          while(getline(sFile,str))
          {
              if (str.empty() || str[0] == '#') continue;
              std::istringstream istr(str);

              // read 6 values from the line to get the 3 (l2,theta,phi) of interest
              int detIndex,code;
              double l2,theta,phi,offset;
              istr >> detIndex >> offset >> l2 >> code >> theta >> phi;

              // sanity check on angles - l2 should be +ve but sample file has a few -ve values
              // on monitors
              if(theta > 181.0 || theta < -1 || phi < -181 || phi > 181)
              {
                  g_log.error("Position angle data out of range in .sca file");
                  throw std::runtime_error("Position angle data out of range in .sca file"); 
              }
              Kernel::V3D truPos;
              // use abs as correction file has -ve l2 for first few detectors
              truPos.spherical(fabs(l2),theta,phi);
              truepos.push_back(truPos);
              //
              Geometry::IDetector_const_sptr det;
              try
              {
                det = instrument->getDetector(detIndex);
              }
              catch(Kernel::Exception::NotFoundError &)
              {
                continue;
              }
              Kernel::V3D detPos = det->getPos();
              Kernel::V3D shift=truPos-detPos;

              // scaling applied to dets that are not monitors and have sequential IDs
              if(detIdLast==detIndex-1 && !det->isMonitor())
              {
                  Kernel::V3D diffI=detPos-detPosLast;
                  Kernel::V3D diffT=truPos-truPosLast;
                  double scale=diffT.norm()/diffI.norm();
                  Kernel::V3D scaleDir=diffT/diffT.norm();
                  // Wish to store the scaling in a map, if we already have a scaling
                  // for this detector (i.e. from the other side) we average the two
                  // values. End of tube detectors only have one scaling estimate.
                  scaleMap[detIndex]=scale;
                  its=scaleMap.find(detIndex-1);
                  if(its==scaleMap.end())
                      scaleMap[detIndex-1]=scale;
                  else
                      its->second=0.5*(its->second+scale);
                  //std::cout << detIndex << scale << scaleDir << std::endl;
              }
              detIdLast=detIndex;
              detPosLast=detPos;
              truPosLast=truPos;
              posMap[detIndex]=shift;
              //
              prog.report();
          }
      }
      else if(scalingFile.find(".raw")!=std::string::npos || scalingFile.find(".RAW")!=std::string::npos )
      {
          std::vector<int> detID;
          std::vector<Kernel::V3D> truepos;
          getDetPositionsFromRaw(scalingFile,detID,truepos);
          //
          int detectorCount = static_cast<int>(detID.size());
          if(detectorCount<1)
          {
              g_log.error("Failed to read any detectors from RAW file");
              throw std::runtime_error("Failed to read any detectors from RAW file");
          }
          int detIdLast=-10;
          Kernel::V3D truPosLast,detPosLast;
          Progress prog(this,0.0,0.5,detectorCount);
          for(int i=0;i<detectorCount;i++)
          {
              int detIndex=detID[i];
              Geometry::IDetector_const_sptr det;
              try
              {
                det = instrument->getDetector(detIndex);
              }
              catch(Kernel::Exception::NotFoundError &)
              {
                continue;
              }
              Kernel::V3D detPos = det->getPos();
              Kernel::V3D shift=truepos[i]-detPos;

              if(detIdLast==detIndex-1 && !det->isMonitor()) 
              {
                  Kernel::V3D diffI=detPos-detPosLast;
                  Kernel::V3D diffT=truepos[i]-truPosLast;
                  double scale=diffT.norm()/diffI.norm();
                  Kernel::V3D scaleDir=diffT/diffT.norm();
                  scaleMap[detIndex]=scale;
                  its=scaleMap.find(detIndex-1);
                  if(its==scaleMap.end())
                  {
                      scaleMap[detIndex-1]=scale;
                  }
                  else
                  {
                      if(m_scalingOption==0)
                          its->second=0.5*(its->second+scale); //average of two 
                      else if(m_scalingOption==1)
                      {
                          if(its->second < scale)
                              its->second=scale; //max
                      }
                      else if(m_scalingOption==2)
                      {
                          if(its->second < scale)
                              its->second=scale;
                          its->second *= 1.05;  // max+5%
                      }
                      else
                          its->second=3.0; // crazy test value
                  }
                  //std::cout << detIndex << scale << scaleDir << std::endl;
              }
              detIdLast=detID[i];
              detPosLast=detPos;
              truPosLast=truepos[i];
              posMap[detIndex]=shift;
              //
              prog.report();
          }
      }
      movePos( m_workspace, posMap, scaleMap);
      return true;
  }



void SetScalingPSD::movePos(API::MatrixWorkspace_sptr& WS, std::map<int,Kernel::V3D>& posMap,
                            std::map<int,double>& scaleMap)
{

  /** Move all the detectors to their actual positions, as stored in posMap and
  *   set their scaling as in scaleMap
  *   @param WS :: pointer to the workspace 
  *   @param posMap :: A map of integer detector ID and corresponding position shift
  *   @param scaleMap :: A map of integer detectorID and corresponding scaling (in Y)
  */
  std::map<int,Kernel::V3D>::iterator iter = posMap.begin();
  boost::shared_ptr<const Instrument> inst = WS->getInstrument();
  boost::shared_ptr<const IComponent> comp;

  // Want to get all the detectors to move, but don't want to do this one at a time
  // since the search (based on MoveInstrument findBy methods) is going to be too slow
  // Hence findAll gets a vector of IComponent for all detectors, as m_vectDet.
  m_vectDet.reserve(posMap.size());
  findAll(inst);

  double scale,maxScale=-1e6,minScale=1e6,aveScale=0.0;
  int scaleCount=0;
  //progress 50% here inside the for loop
  //double prog=0.5;
  Progress prog(this,0.5,1.0, static_cast<int>(m_vectDet.size()));
  // loop over detector (IComps)
  for(size_t id=0;id<m_vectDet.size();id++)
  {
      V3D Pos,shift;// New relative position
      comp = m_vectDet[id];
      boost::shared_ptr<const IDetector> det = boost::dynamic_pointer_cast<const IDetector>(comp);
      int idet=0;
      if (det) idet=det->getID();

      iter=posMap.find(idet); // check if we have a shift
      if(iter==posMap.end()) continue;
      shift=iter->second;
      // First set it to the new absolute position (code from MoveInstrument)
      Pos = comp->getPos() + shift;
    
      // Then find the corresponding relative position
      boost::shared_ptr<const IComponent> parent = comp->getParent();
      if (parent)
      {
          Pos -= parent->getPos();
          Quat rot = parent->getRelativeRot();
          rot.inverse();
          rot.rotate(Pos);
      }
    
      //Need to get the address to the base instrument component
      Geometry::ParameterMap& pmap = WS->instrumentParameters();
      pmap.addV3D(comp.get(), "pos", Pos);

      // Set the "sca" instrument parameter
      std::map<int,double>::iterator it=scaleMap.find(idet);
      if(it!=scaleMap.end())
      {
          scale=it->second;
          if(minScale>scale) minScale=scale;
          if(maxScale<scale) maxScale=scale;
          aveScale+=fabs(1.0-scale);
          scaleCount++;
          pmap.addV3D(comp.get(),"sca",V3D(1.0,it->second,1.0));
      }
      //
      //prog+= double(1)/m_vectDet.size();
      //progress(prog);
      prog.report();
  }
  g_log.debug() << "Range of scaling factors is " << minScale << " to " << maxScale << "\n"
                << "Average abs scaling fraction is " << aveScale/scaleCount << "\n";
  return;
}

/** Find all detectors in the comp and push the IComp pointers onto m_vectDet
 * @param comp :: The component to search
 */
void SetScalingPSD::findAll(boost::shared_ptr<const Geometry::IComponent> comp)
{
    boost::shared_ptr<const IDetector> det = boost::dynamic_pointer_cast<const IDetector>(comp);
    if (det)
    {
       m_vectDet.push_back(comp);
       return;
    }
    boost::shared_ptr<const ICompAssembly> asmb = boost::dynamic_pointer_cast<const ICompAssembly>(comp);
    if (asmb)
        for(int i=0;i<asmb->nelements();i++)
        {
            findAll((*asmb)[i]);
        }
    return;
}

/** Read detector true positions from raw file
 * @param rawfile :: Name of raw file
 * @param detID :: Vector of detector numbers
 * @param pos :: V3D of detector positions corresponding to detID
 */
void SetScalingPSD::getDetPositionsFromRaw(std::string rawfile,std::vector<int>& detID, std::vector<Kernel::V3D>& pos)
{
  (void) rawfile; // Avoid compiler warning

    // open raw file
    ISISRAW iraw(NULL);
    if (iraw.readFromFile(m_filename.c_str(),false) != 0)
    {
      g_log.error("Unable to open file " + m_filename);
      throw Exception::FileError("Unable to open File:" , m_filename);
    }
    // get detector information
    const int numDetector = iraw.i_det;    // number of detectors
    const int* const rawDetID = iraw.udet;    // detector IDs
    const float* const r = iraw.len2;      // distance from sample
    const float* const angle = iraw.tthe;  // angle between indicent beam and direction from sample to detector (two-theta)
    const float* const phi=iraw.ut;
    // Is ut01 (=phi) present? Sometimes an array is present but has wrong values e.g.all 1.0 or all 2.0
    bool phiPresent = iraw.i_use>0 && phi[0]!= 1.0 && phi[0] !=2.0;
    if( ! phiPresent )
    {
         g_log.error("Unable to get Phi values from the raw file");
    }
    detID.reserve(numDetector);
    pos.reserve(numDetector);
    Kernel::V3D point;
    for (int i = 0; i < numDetector; ++i)
    {
       point.spherical(r[i], angle[i], phi[i]);
       pos.push_back(point);
       detID.push_back(rawDetID[i]);
    }
}


} // namespace DataHandling
} // namespace Mantid
