#ifndef MANTID_DATAHANDLING_FAKEEVENTDATALISTENER_H_
#define MANTID_DATAHANDLING_FAKEEVENTDATALISTENER_H_

//----------------------------------------------------------------------
// Includes
//----------------------------------------------------------------------
#include "MantidAPI/ILiveListener.h"
#include "MantidDataObjects/EventWorkspace.h"
#include "MantidKernel/PseudoRandomNumberGenerator.h"
#include <Poco/Timer.h>
#include "MantidKernel/MultiThreaded.h"
#include "MantidKernel/DateAndTime.h"

namespace Mantid
{
  namespace DataHandling
  {
    /** An implementation of ILiveListener for testing purposes that fills its event
        workspace buffer with randomly generated events.

        Copyright &copy; 2012 ISIS Rutherford Appleton Laboratory & NScD Oak Ridge National Laboratory

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
     */
    class FakeEventDataListener : public API::ILiveListener
    {
    public:
      FakeEventDataListener();
      ~FakeEventDataListener();

      std::string name() const { return "FakeEventDataListener"; }
      bool supportsHistory() const { return false; } // For the time being at least
      bool buffersEvents() const { return true; }

      bool connect(const Poco::Net::SocketAddress& address);
      void start(Kernel::DateAndTime startTime = Kernel::DateAndTime());
      boost::shared_ptr<API::MatrixWorkspace> extractData();

      bool isConnected();
      ILiveListener::RunStatus runStatus();

    private:
      void generateEvents(Poco::Timer&);

      DataObjects::EventWorkspace_sptr m_buffer; ///< Used to buffer events between calls to extractData()
      Kernel::PseudoRandomNumberGenerator * m_rand; ///< Used in generation of random events
      Poco::Timer m_timer; ///< Used to call the event-generating function on a schedule
      int m_datarate;     ///< The data rate to (attempt to) generate in events/sec
      int m_callbackloop; ///< Number of times to loop within each generateEvents() call
      double m_endRunEvery; ///< Make a new run every N seconds

      /// Date and time of the next time to end the run
      Mantid::Kernel::DateAndTime m_nextEndRunTime;

      /// Fake run number to give
      int m_runNumber;

      /// Mutex to exclude generateEvents() and extractData().
      Kernel::Mutex m_mutex;
    };

  } // namespace DataHandling
} // namespace Mantid

#endif  /* MANTID_DATAHANDLING_FAKEEVENTDATALISTENER_H_ */
