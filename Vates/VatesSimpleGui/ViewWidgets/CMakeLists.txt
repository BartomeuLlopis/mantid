project( MantidVatesSimpleGuiViewWidgets )

# These are the C++ files to be compiled.
set( INCLUDE_FILES
  inc/MantidVatesSimpleGuiViewWidgets/AutoScaleRangeGenerator.h
  inc/MantidVatesSimpleGuiViewWidgets/CameraManager.h
  inc/MantidVatesSimpleGuiViewWidgets/BackgroundRgbProvider.h
  inc/MantidVatesSimpleGuiViewWidgets/ColorMapEditorPanel.h
  inc/MantidVatesSimpleGuiViewWidgets/ColorSelectionWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/ColorUpdater.h
  inc/MantidVatesSimpleGuiViewWidgets/LibHelper.h
  inc/MantidVatesSimpleGuiViewWidgets/MdViewerWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/MultisliceView.h
  inc/MantidVatesSimpleGuiViewWidgets/pqCameraToolbarNonOrthogonalAxes.h
  inc/MantidVatesSimpleGuiViewWidgets/pqCameraReactionNonOrthogonalAxes.h
  inc/MantidVatesSimpleGuiViewWidgets/VatesParaViewApplication.h
  inc/MantidVatesSimpleGuiViewWidgets/RebinAlgorithmDialogProvider.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksTableControllerVsi.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksTabWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/SaveScreenshotReaction.h
  inc/MantidVatesSimpleGuiViewWidgets/RebinnedSourcesManager.h
  inc/MantidVatesSimpleGuiViewWidgets/VisibleAxesColor.h
  inc/MantidVatesSimpleGuiViewWidgets/StandardView.h
  inc/MantidVatesSimpleGuiViewWidgets/SplatterPlotView.h
  inc/MantidVatesSimpleGuiViewWidgets/ThreesliceView.h
  inc/MantidVatesSimpleGuiViewWidgets/TimeControlWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/ViewBase.h
  inc/MantidVatesSimpleGuiViewWidgets/WidgetDllOption.h
  inc/MantidVatesSimpleGuiViewWidgets/VsiApplyBehaviour.h
)

set( SOURCE_FILES
  src/AutoScaleRangeGenerator.cpp
  src/CameraManager.cpp
  src/BackgroundRgbProvider.cpp
  src/ColorMapEditorPanel.cpp
  src/ColorSelectionWidget.cpp
  src/ColorUpdater.cpp
  src/MdViewerWidget.cpp
  src/MultisliceView.cpp
  src/RebinAlgorithmDialogProvider.cpp
  src/PeaksTableControllerVsi.cpp
  src/PeaksTabWidget.cpp
  src/PeaksWidget.cpp
  src/pqCameraToolbarNonOrthogonalAxes.cpp
  src/pqCameraReactionNonOrthogonalAxes.cpp
  src/SaveScreenshotReaction.cpp
  src/RebinnedSourcesManager.cpp
  src/VisibleAxesColor.cpp
  src/StandardView.cpp
  src/SplatterPlotView.cpp
  src/ThreesliceView.cpp
  src/TimeControlWidget.cpp
  src/VatesParaViewApplication.cpp
  src/ViewBase.cpp
  src/VsiApplyBehaviour.cpp
)

set( TEST_FILES
)

# These are the headers to be preprocessed using
# Qt's moc preprocessor.
qt4_wrap_cpp( MOC_SOURCES
  inc/MantidVatesSimpleGuiViewWidgets/ColorSelectionWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/ColorMapEditorPanel.h
  inc/MantidVatesSimpleGuiViewWidgets/MdViewerWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/MultisliceView.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksTableControllerVsi.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/PeaksTabWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/pqCameraToolbarNonOrthogonalAxes.h
  inc/MantidVatesSimpleGuiViewWidgets/pqCameraReactionNonOrthogonalAxes.h
  inc/MantidVatesSimpleGuiViewWidgets/SaveScreenshotReaction.h
  inc/MantidVatesSimpleGuiViewWidgets/RebinnedSourcesManager.h
  inc/MantidVatesSimpleGuiViewWidgets/StandardView.h
  inc/MantidVatesSimpleGuiViewWidgets/SplatterPlotView.h
  inc/MantidVatesSimpleGuiViewWidgets/ThreesliceView.h
  inc/MantidVatesSimpleGuiViewWidgets/TimeControlWidget.h
  inc/MantidVatesSimpleGuiViewWidgets/VatesParaViewApplication.h
  inc/MantidVatesSimpleGuiViewWidgets/ViewBase.h
  inc/MantidVatesSimpleGuiViewWidgets/VsiApplyBehaviour.h
)

# These are the ui files to be processed using
# Qt's ui file processor.
qt4_wrap_ui( UI_BUILT_SOURCES
  inc/MantidVatesSimpleGuiViewWidgets/ColorSelectionWidget.ui
  inc/MantidVatesSimpleGuiViewWidgets/ColorMapEditorPanel.ui
  inc/MantidVatesSimpleGuiViewWidgets/MdViewerWidget.ui
  inc/MantidVatesSimpleGuiViewWidgets/MultisliceView.ui
  inc/MantidVatesSimpleGuiViewWidgets/PeaksWidget.ui
  inc/MantidVatesSimpleGuiViewWidgets/PeaksTabWidget.ui
  inc/MantidVatesSimpleGuiViewWidgets/pqCameraToolbarNonOrthogonalAxes.ui
  inc/MantidVatesSimpleGuiViewWidgets/StandardView.ui
  inc/MantidVatesSimpleGuiViewWidgets/SplatterPlotView.ui
  inc/MantidVatesSimpleGuiViewWidgets/ThreesliceView.ui
  inc/MantidVatesSimpleGuiViewWidgets/TimeControlWidget.ui
)

# Add the QtWidgets icons
qt4_add_resources( RES_FILES icons/ViewWidgetsIcons.qrc )

# Setup the include locations.
include_directories(
  inc
  ${CMAKE_SOURCE_DIR}/MantidQt/API/inc
  ${CMAKE_SOURCE_DIR}/MantidQt/MantidWidgets/inc
  ${CMAKE_BINARY_DIR}/MantidQt/MantidWidgets
  ${CMAKE_SOURCE_DIR}/MantidQt/SliceViewer/inc
  ${CMAKE_BINARY_DIR}/MantidQt/SliceViewer
  ${CMAKE_SOURCE_DIR}/MantidQt/Factory/inc
  ${CMAKE_CURRENT_BINARY_DIR}
  ${CMAKE_CURRENT_BINARY_DIR}/../QtWidgets
  ${CMAKE_SOURCE_DIR}/MantidPlot/src
)

set( ALL_FILES
${INCLUDE_FILES}
${SOURCE_FILES}
${MOC_SOURCES}
${UI_BUILT_SOURCES}
${RES_FILES}
)

set( TEST_SUITES
    test/suite_MDEventWorkspace
    test/suite_MDHistoWorkspace
)

# For Windows
add_definitions( -DIN_MANTID_VATES_SIMPLEGUI_VIEWWIDGETS )
# Add the target for this directory
add_library( VatesSimpleGuiViewWidgets ${ALL_FILES} )
# Set the name of the generated library
set_target_properties( VatesSimpleGuiViewWidgets PROPERTIES OUTPUT_NAME MantidVatesSimpleGuiViewWidgets )
# Add to the 'VatesSimpleGui' group in VS
set_property( TARGET VatesSimpleGuiViewWidgets PROPERTY FOLDER MantidVatesSimpleGui )

include_directories( SYSTEM ${PARAVIEW_INCLUDE_DIRS} ${QWT_INCLUDE_DIR} ${PYTHON_INCLUDE_DIR} )

target_link_libraries( VatesSimpleGuiViewWidgets LINK_PRIVATE ${TCMALLOC_LIBRARIES_LINKTIME}
pqApplicationComponents
pqComponents
${vtkjsoncpp_LIBRARIES}
vtkPVServerManagerRendering
vtkRenderingFreeType
vtksys
${QT_LIBRARIES}
VatesSimpleGuiQtWidgets
MantidQtAPI
VatesAPI
${MANTID_SUBPROJECT_LIBS}
MantidQtSliceViewer
MantidQtFactory
${PYTHON_LIBRARIES}
MantidWidgets
${POCO_LIBRARIES}
${Boost_LIBRARIES}
)

if (OSX_VERSION VERSION_GREATER 10.8)
  set_target_properties ( VatesSimpleGuiViewWidgets PROPERTIES INSTALL_RPATH "@loader_path/../Contents/MacOS;@loader_path/../Contents/Libraries")
endif ()

# Create test file projects
include_directories ( SYSTEM ${CXXTEST_INCLUDE_DIR} ${GMOCK_INCLUDE_DIR} ${GTEST_INCLUDE_DIR} )

include_directories( inc ../../../Framework/TestHelpers/inc ../../../Framework/DataHandling/inc ../../../Framework/DataObjects/inc)
set ( TESTHELPER_SRCS ../../../Framework/TestHelpers/src/ComponentCreationHelper.cpp
                      ../../../Framework/TestHelpers/src/InstrumentCreationHelper.cpp
                      ../../../Framework/TestHelpers/src/WorkspaceCreationHelper.cpp
                      ../../../Framework/TestHelpers/src/MDEventsTestHelper.cpp
                      ../../../Framework/TestHelpers/src/StartFrameworkManager.cpp )
cxxtest_add_test( VatesSimpleGuiViewWidgetsTest ${TEST_FILES} )

target_link_libraries( VatesSimpleGuiViewWidgetsTest LINK_PRIVATE ${TCMALLOC_LIBRARIES_LINKTIME}
  VatesSimpleGuiViewWidgets
  ${vtkjsoncpp_LIBRARIES}
  DataHandling
  Kernel
  HistogramData
  DataObjects
  MantidQtAPI
  ${MANTID_SUBPROJECT_LIBS}
  ${POCO_LIBRARIES}
  ${Boost_LIBRARIES}
  ${GMOCK_LIBRARIES}
  ${GTEST_LIBRARIES} )

add_dependencies( AllTests VatesSimpleGuiViewWidgetsTest )
# Add to the 'UnitTests' group in VS
set_property ( TARGET VatesSimpleGuiViewWidgetsTest PROPERTY FOLDER "UnitTests" )

configure_file ( ${CMAKE_CURRENT_SOURCE_DIR}/inc/MantidVatesSimpleGuiViewWidgets/LibHelper.h.in
                 ${CMAKE_CURRENT_SOURCE_DIR}/inc/MantidVatesSimpleGuiViewWidgets/LibHelper.h )

if( SQUISH_FOUND )
  # Need to set the AUT first
  set( SQUISH_AUT MantidPlot )
  set( SQUISH_AUT_PATH $<TARGET_FILE_DIR:${SQUISH_AUT}> )

  # Need to set environmental variables next
  set( SQUISH_ENV_VARS
    PV_PLUGIN_PATH=$<TARGET_FILE_DIR:${SQUISH_AUT}>/${PVPLUGINS_DIR}/${PVPLUGINS_DIR}
    SCRIPTS_DIR=${CMAKE_CURRENT_SOURCE_DIR}/test/mp_scripts
    SQUISH_SCRIPT_DIR=${VSI_GLOBAL_SCRIPTS}:${CMAKE_CURRENT_SOURCE_DIR}/test/common/scripts
  )
  squish_add_test_suite( ${TEST_SUITES} )

endif()

install( TARGETS VatesSimpleGuiViewWidgets ${SYSTEM_PACKAGE_TARGET} DESTINATION ${PVPLUGINS_DIR} )
