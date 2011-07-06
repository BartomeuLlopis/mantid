#ifndef INSTRUMENTACTOR_H_
#define INSTRUMENTACTOR_H_

#include "GLColor.h"
#include "GLActor.h"
#include "GLActorCollection.h"
#include "SampleActor.h"
#include "MantidColorMap.h"

#include "MantidGeometry/IInstrument.h"
#include "MantidAPI/SpectraDetectorTypes.h"

#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>

#include <vector>
#include <map>

#include <QObject>

namespace Mantid
{
  namespace API
  {
    class MatrixWorkspace;
  }
  namespace Geometry
  {
    class IDetector;
  }
}

//struct DetectorInfo
//{
//  GLColor color;
//  boost::shared_ptr<const Mantid::Geometry::IDetector> detector;
//};

/**
  \class  InstrumentActor
  \brief  InstrumentActor class is wrapper actor for the instrument.
  \author Srikanth Nagella
  \date   March 2009
  \version 1.0

   This class has the implementation for rendering Instrument. it provides the interface for picked ObjComponent and other
   operation for selective rendering of the instrument

  Copyright &copy; 2007 ISIS Rutherford Appleton Laboratory & NScD Oak Ridge National Laboratory

  This file is part of Mantid.

  Mantid is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3 of the License, or
  (at your option) any later version.

  Mantid is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  File change history is stored at: <https://svn.mantidproject.org/mantid/trunk/Code/Mantid>
*/
class InstrumentActor: public QObject, public GLActor
{
  Q_OBJECT
public:
	InstrumentActor(boost::shared_ptr<Mantid::API::MatrixWorkspace> workspace); ///< Constructor
	~InstrumentActor();								   ///< Destructor
	virtual std::string type()const {return "InstrumentActor";} ///< Type of the GL object
  void draw(bool picking = false)const;
  void getBoundingBox(Mantid::Kernel::V3D& minBound,Mantid::Kernel::V3D& maxBound)const{m_scene.getBoundingBox(minBound,maxBound);}
  bool accept(const GLActorVisitor& visitor);

  boost::shared_ptr<const Mantid::Geometry::IInstrument> getInstrument()const;
  boost::shared_ptr<const Mantid::API::MatrixWorkspace> getWorkspace()const{return m_workspace;}
  const MantidColorMap & getColorMap() const;
  void loadColorMap(const QString& ,bool reset_colors = true);
  void changeScaleType(int);
  void setIntegrationRange(const double& xmin,const double& xmax);
  double minValue()const{return m_DataMinValue;}
  double maxValue()const{return m_DataMaxValue;}
  void setMinValue(double value);
  void setMaxValue(double value);
  void setMinMaxRange(double vmin, double vmax);
  double minPositiveValue()const{return m_WkspDataPositiveMin;}
  double minBinValue()const{return m_BinMinValue;}
  double maxBinValue()const{return m_BinMaxValue;}
  bool wholeRange()const;
  size_t ndetectors()const{return m_detIDs.size();}
  boost::shared_ptr<Mantid::Geometry::IDetector> getDetector(size_t pickID)const;
  Mantid::detid_t getDetID(size_t pickID)const{return m_detIDs.at(pickID);}
  const std::vector<Mantid::detid_t>& getAllDetIDs()const{return m_detIDs;}
  GLColor getColor(Mantid::detid_t id)const;
  size_t getWorkspaceIndex(Mantid::detid_t id)const{return (*m_id2wi_map)[id];}
  double getIntegratedCounts(Mantid::detid_t id)const;
  void update();
  void invalidateDisplayLists()const{m_scene.invalidateDisplayList();}
  QString getCurrentColorMap()const{return m_currentColorMap;}
  static void BasisRotation(const Mantid::Kernel::V3D& Xfrom,
                  const Mantid::Kernel::V3D& Yfrom,
                  const Mantid::Kernel::V3D& Zfrom,
                  const Mantid::Kernel::V3D& Xto,
                  const Mantid::Kernel::V3D& Yto,
                  const Mantid::Kernel::V3D& Zto,
                  Mantid::Kernel::Quat& R,
                  bool out = false
                  );
signals:
  void colorMapChanged();
protected:
  void resetColors();
  void loadSettings();
  void saveSettings();
  /// Add a detid to the m_detIDs. The order of detids define the pickIDs for detectors. Returns pickID for added detector
  size_t push_back_detid(Mantid::detid_t)const;
  boost::shared_ptr<Mantid::API::MatrixWorkspace> m_workspace;
  MantidColorMap m_colorMap;
  /// integrated spectra
  std::vector<double> m_specIntegrs;
  /// The workspace data and bin range limits
  double m_WkspDataMin, m_WkspDataMax,m_WkspDataPositiveMin;
  double m_WkspBinMin, m_WkspBinMax;
  /// The user requested data and bin ranges
  double m_DataMinValue, m_DataMaxValue;
  double m_BinMinValue, m_BinMaxValue;
  boost::shared_ptr<const Mantid::Geometry::IInstrument::plottables> m_plottables;
  boost::scoped_ptr<Mantid::detid2index_map> m_id2wi_map;
  mutable std::vector<Mantid::detid_t> m_detIDs; ///< all det ids in the instrument in order of pickIDs, populated by Obj..Actor constructors
  mutable std::vector<GLColor> m_colors; ///< colors in order of workspace indexes
  QString m_currentColorMap;

  GLActorCollection m_scene;
  SampleActor* m_sampleActor;

  static double m_tolerance;

  friend class ObjComponentActor;
  friend class ObjCompAssemblyActor;
  friend class RectangularDetectorActor;
};

/// Sets visibility of an actor with a particular ComponentID
class SetVisibleComponentVisitor: public SetVisibilityVisitor
{
public:
  SetVisibleComponentVisitor(const Mantid::Geometry::ComponentID id):m_id(id){}
  bool visit(GLActor*)const;
  Mantid::Geometry::ComponentID getID()const{return m_id;}
private:
  Mantid::Geometry::ComponentID m_id;
};

/// Finds an actor with a particular ComponentID
class FindComponentVisitor: public SetVisibilityVisitor
{
public:
  FindComponentVisitor(const Mantid::Geometry::ComponentID id):m_id(id),m_actor(NULL){}
  bool visit(GLActor*)const;
  ComponentActor* getActor()const{return m_actor;}
private:
  Mantid::Geometry::ComponentID m_id;
  mutable ComponentActor* m_actor;
};

#endif /*InstrumentActor_H_*/

