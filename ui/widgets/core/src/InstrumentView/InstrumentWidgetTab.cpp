#include "MantidUiWidgetsCore/InstrumentView/InstrumentWidgetTab.h"
#include "MantidUiWidgetsCore/InstrumentView/InstrumentWidget.h"

namespace MantidQt {
namespace MantidWidgets {
InstrumentWidgetTab::InstrumentWidgetTab(InstrumentWidget *parent)
    : QFrame(parent), m_instrWidget(parent) {}

/**
* Return a pointer to the projection surface.
*/
boost::shared_ptr<ProjectionSurface> InstrumentWidgetTab::getSurface() const {
  return m_instrWidget->getSurface();
}
} // MantidWidgets
} // MantidQt
