#ifndef MUONFITPROPERTYBROWSER_H_
#define MUONFITPROPERTYBROWSER_H_

#include "MantidQtMantidWidgets/FitPropertyBrowser.h"
#include "MantidQtMantidWidgets/IMuonFitDataModel.h"
#include "MantidQtMantidWidgets/IMuonFitFunctionModel.h"

#include <QMap>
/* Forward declarations */
class QDockWidget;
class QLabel;
class QPushButton;
class QCheckBox;
class QMenu;
class QSignalMapper;
class QtTreePropertyBrowser;
class QtGroupPropertyManager;
class QtDoublePropertyManager;
class QtIntPropertyManager;
class QtBoolPropertyManager;
class QtStringPropertyManager;
class QtEnumPropertyManager;
class QtProperty;
class QtBrowserItem;
class QVBoxLayout;
class QGroupBox;
class QSplitter;
class QWidget;

namespace Mantid {
namespace API {
class IFitFunction;
class IPeakFunction;
class CompositeFunction;
}
}

namespace MantidQt {
namespace MantidWidgets {
class PropertyHandler;

class EXPORT_OPT_MANTIDQT_MANTIDWIDGETS MuonFitPropertyBrowser
    : public MantidQt::MantidWidgets::FitPropertyBrowser,
      public MantidQt::MantidWidgets::IMuonFitFunctionModel,
      public IMuonFitDataModel {
  Q_OBJECT

public:
  /// Constructor.
  MuonFitPropertyBrowser(QWidget *parent = NULL, QObject *mantidui = NULL);
  /// Initialise the layout.
  void init() override;
  /// Set the input workspace name
  void setWorkspaceName(const QString &wsName) override;
  /// Called when the fit is finished
  void finishHandle(const Mantid::API::IAlgorithm *alg) override;
  /// Add an extra widget into the browser
  void addExtraWidget(QWidget *widget);
  /// Set function externally
  void setFunction(const Mantid::API::IFunction_sptr func) override;
  /// Run a non-sequential fit
  void runFit() override;
  /// Run a sequential fit
  void runSequentialFit() override;
  /// Get the fitting function
  Mantid::API::IFunction_sptr getFunction() const override {
    return getFittingFunction();
  }
  /// Set list of workspaces to fit
  void setWorkspaceNames(const QStringList &wsNames) override;
  /// Get output name
  std::string outputName() const override;
  /// Prefix for simultaneous fit results
  static const std::string SIMULTANEOUS_PREFIX;
  /// Set label for simultaneous fit results
  void setSimultaneousLabel(const std::string &label) override {
    m_simultaneousLabel = label;
  }
  /// Get names of workspaces that are set to be fitted
  std::vector<std::string> getWorkspaceNamesToFit() const override {
    return m_workspacesToFit;
  }
  /// User changed dataset index to fit
  void userChangedDataset(int index) override {
    emit userChangedDatasetIndex(index);
  }
  /// Set multiple fitting mode on or off
  void setMultiFittingMode(bool enabled) override;
  void setTFAsymmMode(bool enabled) override;

  /// After fit checks done, continue
  void continueAfterChecks(bool sequential) override;
  /// Remove a plotted guess
  void doRemoveGuess() override { emit removeGuess(); }
  /// Plot a guess function
  void doPlotGuess() override { emit plotGuess(); }
  /// Whether a guess is plotted or not
  bool hasGuess() const override;

  /// Enable/disable the Fit button;
  virtual void setFitEnabled(bool yes) override;

  void doTFAsymmFit(int maxIterations);
  void setAvailableGroups(const QStringList &groups);
  void setAvailablePeriods(const QStringList &periods);

  QStringList getChosenGroups() const;
  QStringList getChosenPeriods() const;

  /// Clear list of selected groups
  void clearChosenGroups() const;
  void setAllGroups();
  void setGroupNames(const std::vector<std::string> groupNames);
  void setAllPairs();
  void setAllGroupsOrPairs(const bool isItGroup);
  void clearChosenPeriods() const;
  void setChosenGroup(const QString &group);
  void setAllPeriods();
  void setChosenPeriods(const QString &period);
  void setSingleFitLabel(std::string name);

public slots:
  /// Perform the fit algorithm
  void fit() override;
  /// Open sequential fit dialog
  void sequentialFit() override;

  void executeFitMenu(const QString &item) override;
  void groupBtnPressed();
  void periodBtnPressed();
  void generateBtnPressed();
  void combineBtnPressed();
  void setNumPeriods(size_t numPeriods);

signals:
  /// Emitted when sequential fit is requested by user
  void sequentialFitRequested();
  /// Emitted when function should be updated
  void functionUpdateRequested() override;
  /// Emitted when a fit or sequential fit is requested
  void functionUpdateAndFitRequested(bool sequential) override;
  /// Emitted when number of workspaces to fit is changed
  void workspacesToFitChanged(int n) override;
  /// Emitted when dataset index to fit is changed
  void userChangedDatasetIndex(int index) override;
  /// Emitted when "fit to raw data" is changed
  void fitRawDataClicked(bool enabled) override;
  void groupBoxClicked();
  void periodBoxClicked();
  void reselctGroupClicked(bool enabled);
  /// Emitted when fit is about to be run
  void preFitChecksRequested(bool sequential) override;

protected:
  void showEvent(QShowEvent *e) override;
  double normalization() const;
  void setNormalization();
private slots:
  void doubleChanged(QtProperty *prop) override;
  void boolChanged(QtProperty *prop) override;
  void enumChanged(QtProperty *prop) override;

private:
  /// new menu option
  QAction *m_fitActionTFAsymm;
  /// override populating fit menu
  void populateFitMenuButton(QSignalMapper *fitMapper, QMenu *fitMenu) override;

  /// Get the registered function names
  void populateFunctionNames() override;
  /// Check if the workspace can be used in the fit
  bool isWorkspaceValid(Mantid::API::Workspace_sptr) const override;
  /// After a simultaneous fit, add information to results table and group
  /// workspaces
  void finishAfterSimultaneousFit(const Mantid::API::IAlgorithm *fitAlg,
                                  const int nWorkspaces) const;

  void clearGroupCheckboxes();
  void addGroupCheckbox(const QString &name);
  void genGroupWindow();
  void genPeriodWindow();
  void genCombinePeriodWindow();
  void updateGroupDisplay();
  void updatePeriodDisplay();
  void setChosenPeriods(const QStringList &chosenPeriods);
  void clearPeriodCheckboxes();
  void addPeriodCheckbox(const QString &name);

  /// Splitter for additional widgets and splitter between this and browser
  QSplitter *m_widgetSplitter, *m_mainSplitter;
  /// Names of workspaces to fit
  std::vector<std::string> m_workspacesToFit;
  /// Label to use for simultaneous fits
  std::string m_simultaneousLabel;
  QtProperty *m_normalization;
  QStringList m_normalizationValue;
  QtProperty *m_keepNorm;

  QtBrowserItem *m_multiFitSettingsGroup;
  QtProperty *m_groupsToFit;
  QStringList m_groupsToFitOptions;
  /// Map of group names to checkboxes
  QMap<QString, QtProperty *> m_groupBoxes;
  QtProperty *m_showGroup;
  QStringList m_showGroupValue;

  QtProperty *m_periodsToFit;
  QStringList m_periodsToFitOptions;
  /// Map of group names to checkboxes
  QMap<QString, QtProperty *> m_periodBoxes;
  QtProperty *m_showPeriods;
  QStringList m_showPeriodValue;
  QLineEdit *m_positiveCombo;
  QLineEdit *m_negativeCombo;

  QPushButton *m_reselectGroupBtn;
  QPushButton *m_reselectPeriodBtn;
  QPushButton *m_generateBtn;
  QGroupBox *m_btnGroup;
  QDialog *m_groupWindow;
  QDialog *m_periodWindow;
  QDialog *m_comboWindow;

  std::vector<std::string> m_groupsList;
};

std::vector<double> readNormalization();
} // MantidQt
} // API

#endif /*MUONFITPROPERTYBROWSER_H_*/
