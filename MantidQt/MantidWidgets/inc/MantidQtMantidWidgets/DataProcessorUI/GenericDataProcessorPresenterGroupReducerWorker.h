#ifndef MANTIDQTMANTIDWIDGETS_GENERICDATAPROCESSORPRESENTER_GENERICDATAPROCESSORPRESENTERGROUPREDUCERWORKER_H
#define MANTIDQTMANTIDWIDGETS_GENERICDATAPROCESSORPRESENTER_GENERICDATAPROCESSORPRESENTERGROUPREDUCERWORKER_H

#include "MantidQtMantidWidgets/DataProcessorUI/GenericDataProcessorPresenter.h"

#include <QThread>

namespace MantidQt {
namespace MantidWidgets {

/**
Worker to run the reduction process for each group of the
GenericDataProcessorPresenter for the GUI it is attached to. It has
a finished() signal which is expected to be emittted when one of
these when the hard/long-work methods finish.

Copyright &copy; 2016 ISIS Rutherford Appleton Laboratory, NScD
Oak Ridge National Laboratory & European Spallation Source

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

File change history is stored at: <https://github.com/mantidproject/mantid>
Code Documentation is available at: <http://doxygen.mantidproject.org>
*/
class GenericDataProcessorPresenterGroupReducerWorker : public QObject {
  Q_OBJECT

public:
  GenericDataProcessorPresenterGroupReducerWorker(
      GenericDataProcessorPresenter *presenter, const GroupData &groupData,
      int groupIndex)
      : m_presenter(presenter), m_groupData(groupData),
        m_groupIndex(groupIndex) {}

private slots:
  void startWorker() {
    try {
      m_presenter->postProcessGroup(m_groupData);
      m_presenter->m_manager->addHighlighted(m_groupIndex);
      emit finished(0);
    } catch (std::exception &ex) {
      emit reductionErrorSignal(ex);
      emit finished(1);
    }
  }

signals:
  void finished(const int exitCode);
  void reductionErrorSignal(std::exception ex);

private:
  GenericDataProcessorPresenter *m_presenter;
  const GroupData m_groupData;
  int m_groupIndex;
};

} // namespace MantidWidgets
} // namespace MantidQt

#endif // MANTIDQTMANTIDWIDGETS_GENERICDATAPROCESSORPRESENTER_GENERICDATAPROCESSORPRESENTERGROUPREDUCERWORKER_H
