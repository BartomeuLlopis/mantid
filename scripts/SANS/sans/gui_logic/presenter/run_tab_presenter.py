from __future__ import (absolute_import, division, print_function)

import os
import copy
from mantid.kernel import Logger

from mantid.api import (AlgorithmManager, AnalysisDataService, FileFinder)
from mantid.kernel import (Property)
from ui.sans_isis.sans_data_processor_gui import SANSDataProcessorGui
from sans.gui_logic.models.state_gui_model import StateGuiModel
from sans.gui_logic.models.table_model import TableModel, TableIndexModel
from sans.gui_logic.presenter.gui_state_director import (GuiStateDirector)
from sans.gui_logic.presenter.settings_diagnostic_presenter import (SettingsDiagnosticPresenter)
from sans.gui_logic.sans_data_processor_gui_algorithm import SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME
from sans.gui_logic.presenter.property_manager_service import PropertyManagerService
from sans.gui_logic.gui_common import (get_reduction_mode_strings_for_gui, get_reduction_mode_strings_for_gui,
                                       OPTIONS_SEPARATOR, OPTIONS_INDEX, OPTIONS_EQUAL)

from sans.common.enums import (BatchReductionEntry, OutputMode, SANSInstrument, RebinType, RangeStepType, SampleShape)
from sans.common.file_information import (find_sans_file, SANSFileInformationFactory)
from sans.user_file.user_file_reader import UserFileReader
from sans.command_interface.batch_csv_file_parser import BatchCsvParser


sans_logger = Logger("SANS")


class RunTabPresenter(object):
    class ConcreteRunTabListener(SANSDataProcessorGui.RunTabListener):
        def __init__(self, presenter):
            super(RunTabPresenter.ConcreteRunTabListener, self).__init__()
            self._presenter = presenter

        def on_user_file_load(self):
            self._presenter.on_user_file_load()

        def on_batch_file_load(self):
            self._presenter.on_batch_file_load()

        def on_processed_clicked(self):
            self._presenter.on_processed_clicked()

        def on_processing_finished(self):
            self._presenter.on_processing_finished()

    def __init__(self, facility, view=None):
        super(RunTabPresenter, self).__init__()
        self._facility = facility

        # Presenter needs to have a handle on the view since it delegates it
        self._view = None
        self.set_view(view)

        # Models that are being used by the presenter
        self._state_model = None
        self._state_model = None
        self._table_model = None

        # Due to the nature of the DataProcessorWidget we need to provide an algorithm with at least one input
        # workspace and at least one output workspace. Our SANS state approach is not compatible with this. Hence
        # we provide a dummy workspace which is not used. We keep it invisible on the ADS and delete it when the
        # main_presenter is deleted.
        # This is not a nice solution but in line with the SANS dummy algorithm approach that we have provided
        # for the
        self._create_dummy_input_workspace()

        # File information for the first input
        self._file_information = None

        # Settings diagnostic tab presenter
        self._settings_diagnostic_tab_presenter = SettingsDiagnosticPresenter(self)

    def __del__(self):
        self._delete_dummy_input_workspace()

    def _default_gui_setup(self):
        # Set the possible reduction modes
        reduction_mode = get_reduction_mode_strings_for_gui()
        self._view.reduction_mode = reduction_mode

        # Set the step type options for wavelength
        wavelength_step_type = [RangeStepType.to_string(RangeStepType.Lin), RangeStepType.to_string(RangeStepType.Log)]
        self._view.wavelength_step_type = wavelength_step_type

        # Set the geometry options. This needs to include the option to read the sample shape from file.
        sample_shape = ["Read from file",
                        SampleShape.to_string(SampleShape.CylinderAxisUp),
                        SampleShape.to_string(SampleShape.Cuboid),
                        SampleShape.to_string(SampleShape.CylinderAxisAlong)]
        self._view.sample_shape = sample_shape

    # ------------------------------------------------------------------------------------------------------------------
    # Table + Actions
    # ------------------------------------------------------------------------------------------------------------------
    def set_view(self, view):
        if view is not None:
            pass
            self._view = view

            # Add a listener to the view
            listener = RunTabPresenter.ConcreteRunTabListener(self)
            self._view.add_listener(listener)

            # Default gui setup
            self._default_gui_setup()

            # Set appropriate view for the state diagnostic tab presenter
            self._settings_diagnostic_tab_presenter.set_view(self._view.settings_diagnostic_tab)

    def on_user_file_load(self):
        """
        Loads the user file. Populates the models and the view.
        """
        try:
            # 1. Get the user file path from the view
            user_file_path = self._view.get_user_file_path()

            if not user_file_path:
                return

            # 2. Get the full file path
            user_file_path = FileFinder.getFullPath(user_file_path)
            if not os.path.exists(user_file_path):
                raise RuntimeError("The user path {} does not exist. Make sure a valid user file path"
                                   " has been specified.".format(user_file_path))

            # Clear out the current view
            self._view.reset_all_fields_to_default()

            # 3. Read and parse the user file
            user_file_reader = UserFileReader(user_file_path)
            user_file_items = user_file_reader.read_user_file()

            # 4. Populate the model
            self._state_model = StateGuiModel(user_file_items)

            # 5. Update the views.
            self._update_view_from_state_model()
        except Exception as e:
            sans_logger.error("Loading of the user file failed. See here for more details: {}".format(str(e)))

    def on_batch_file_load(self):
        """
        Loads a batch file and populates the batch table based on that
        """
        try:
            # 1. Get the batch file from the view
            batch_file_path = self._view.get_batch_file_path()

            if not batch_file_path:
                return

            if not os.path.exists(batch_file_path):
                raise RuntimeError("The batch file path {} does not exist. Make sure a valid batch file path"
                                   " has been specified.".format(batch_file_path))

            # 2. Read the batch file
            batch_file_parser = BatchCsvParser(batch_file_path)
            parsed_rows = batch_file_parser.parse_batch_file()

            # 3. Clear the table
            self._view.clear_table()

            # 4. Populate the table
            for row in parsed_rows:
                self._populate_row_in_table(row)

            # 5. Populate the selected instrument and the correct detector selection
            self._setup_instrument_specific_settings()

        except RuntimeError as e:
            sans_logger.error("Loading of the batch file failed. See here for more details: {}".format(str(e)))

    def on_processed_clicked(self):
        """
        Prepares the batch reduction.

        0. Validate rows and create dummy workspace if it does not exist
        1. Sets up the states
        2. Adds a dummy input workspace
        3. Adds row index information
        """
        # 0. Validate rows
        self._create_dummy_input_workspace()
        self._validate_rows()

        # 1. Set up the states and convert them into property managers
        states = self.get_states()
        property_manager_service = PropertyManagerService()
        property_manager_service.add_states_to_pmds(states)

        # 2. Add dummy input workspace to Options column
        self._remove_dummy_workspaces_and_row_index()
        self._set_dummy_workspace()

        # 3. Add dummy row index to Options column
        self._set_indices()

    def on_processing_finished(self):
        self._remove_dummy_workspaces_and_row_index()

    def _add_to_options(self, row, property_name, property_value):
        """
        Adds a new property to the Options column

        @param row: The row where the Options column is being altered
        @param property_name: The property name on the GUI algorithm.
        @param property_value: The value which is being set for the property.
        Returns:

        """
        entry = property_name + OPTIONS_EQUAL + str(property_value)
        options = self._get_options(row)
        if options:
            options += OPTIONS_SEPARATOR + entry
        else:
            options = entry
        self._set_options(options, row)

    def _set_options(self, value, row):
        self._view.set_cell(value, row, OPTIONS_INDEX)

    def _get_options(self, row):
        return self._view.get_cell(row, OPTIONS_INDEX, convert_to=str)

    def is_empty_row(self, row):
        indices = range(OPTIONS_INDEX + 1)
        for index in indices:
            cell_value = self._view.get_cell(row, index, convert_to=str)
            if cell_value:
                return False
        return True

    def _remove_from_options(self, row, property_name):
        options = self._get_options(row)
        # Remove the property entry and the value
        individual_options = options.split(",")
        clean_options = []
        for individual_option in individual_options:
            if property_name not in individual_option:
                clean_options.append(individual_option)
        clean_options = ",".join(clean_options)
        self._set_options(clean_options, row)

    def _validate_rows(self):
        # If SampleScatter is empty, then don't run the reduction.
        # We allow empty rows for now, since we cannot remove them from Python.
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            if not self.is_empty_row(row):
                sample_scatter = self._view.get_cell(row, 0)
                if not sample_scatter:
                    raise RuntimeError("Row {} has not SampleScatter specified. Please correct this.".format(row))

    def get_processing_options(self):
        """
        Creates a processing string for the data processor widget

        Returns: A processing string for the data processor widget
        """
        global_options = ""

        # Check if optimizations should be used
        optimization_selection = "UseOptimizations=1" if self._view.use_optimizations else "UseOptimizations=0"
        global_options += optimization_selection

        # Get the output mode
        output_mode = self._view.output_mode
        output_mode_selection = "OutputMode=" + OutputMode.to_string(output_mode)
        global_options += ","
        global_options += output_mode_selection

        return global_options

    # ------------------------------------------------------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------------------------------------------------------
    def disable_controls(self):
        """
        Disable all input fields and buttons during the execution of the reduction.
        """
        pass

    def enable_controls(self):
        """
        Enable all input fields and buttons after the execution has completed.
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    # Table Model and state population
    # ------------------------------------------------------------------------------------------------------------------
    def get_states(self):
        """
        Gathers the state information and performs a reduction
        """
        # 1. Update the state model
        state_model_with_view_update = self._get_state_model_with_view_update()

        # 2. Update the table model
        table_model = self._get_table_model()

        # 3. Go through each row and construct a state object
        states = self._create_states(state_model_with_view_update, table_model)
        return states

    def get_row_indices(self):
        row_indices_which_are_not_empty = []
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            if not self.is_empty_row(row):
                row_indices_which_are_not_empty.append(row)
        return row_indices_which_are_not_empty

    def get_state_for_row(self, row_index):
        states = self.get_states()
        if row_index in list(states.keys()):
            return states[row_index]
        else:
            return None

    def _update_view_from_state_model(self):
        """
        Goes through all sub presenters and update the views based on the state model
        """
        # Front tab view
        self._set_on_view("zero_error_free")
        self._set_on_view("save_types")
        self._set_on_view("compatibility_mode")

        # Settings tab view
        self._set_on_view("reduction_dimensionality")
        self._set_on_view("reduction_mode")
        self._set_on_view("event_slices")

        self._set_on_view("wavelength_step_type")
        self._set_on_view("wavelength_min")
        self._set_on_view("wavelength_max")
        self._set_on_view("wavelength_step")

        self._set_on_view("absolute_scale")
        self._set_on_view("sample_shape")
        self._set_on_view("sample_height")
        self._set_on_view("sample_width")
        self._set_on_view("sample_thickness")
        self._set_on_view("z_offset")

        # Adjustment tab
        self._set_on_view("normalization_incident_monitor")
        self._set_on_view("normalization_interpolate")

        self._set_on_view("transmission_incident_monitor")
        self._set_on_view("transmission_interpolate")
        self._set_on_view("transmission_roi_files")
        self._set_on_view("transmission_mask_files")
        self._set_on_view("transmission_radius")
        self._set_on_view("transmission_monitor")
        self._set_on_view("transmission_m4_shift")

        self._set_on_view("pixel_adjustment_det_1")
        self._set_on_view("pixel_adjustment_det_2")
        self._set_on_view("wavelength_adjustment_det_1")
        self._set_on_view("wavelength_adjustment_det_2")

    def _set_on_view(self, attribute_name):
        attribute = getattr(self._state_model, attribute_name)
        if attribute:
            setattr(self._view, attribute_name, attribute)

    def _get_state_model_with_view_update(self):
        """
        Goes through all sub presenters and update the state model based on the views.

        Note that at the moment we have set up the view and the model such that the name of a property must be the same
        in the view and the model. This can be easily changed, but it also provides a good cohesion.
        """
        state_model = copy.deepcopy(self._state_model)

        # Run tab view
        self._set_on_state_model("zero_error_free", state_model)
        self._set_on_state_model("save_types", state_model)
        self._set_on_state_model("compatibility_mode", state_model)

        # Settings tab
        self._set_on_state_model("reduction_dimensionality", state_model)
        self._set_on_state_model("reduction_mode", state_model)
        self._set_on_state_model("event_slices", state_model)

        self._set_on_state_model("wavelength_step_type", state_model)
        self._set_on_state_model("wavelength_min", state_model)
        self._set_on_state_model("wavelength_max", state_model)
        self._set_on_state_model("wavelength_step", state_model)

        self._set_on_state_model("absolute_scale", state_model)
        self._set_on_state_model("sample_shape", state_model)
        self._set_on_state_model("sample_height", state_model)
        self._set_on_state_model("sample_width", state_model)
        self._set_on_state_model("sample_thickness", state_model)
        self._set_on_state_model("z_offset", state_model)

        # Adjustment tab
        self._set_on_state_model("normalization_incident_monitor", state_model)
        self._set_on_state_model("normalization_interpolate", state_model)

        self._set_on_state_model("transmission_incident_monitor", state_model)
        self._set_on_state_model("transmission_interpolate", state_model)
        self._set_on_state_model("transmission_roi_files", state_model)
        self._set_on_state_model("transmission_mask_files", state_model)
        self._set_on_state_model("transmission_radius", state_model)
        self._set_on_state_model("transmission_monitor", state_model)
        self._set_on_state_model("transmission_m4_shift", state_model)

        self._set_on_state_model("pixel_adjustment_det_1", state_model)
        self._set_on_state_model("pixel_adjustment_det_2", state_model)
        self._set_on_state_model("wavelength_adjustment_det_1", state_model)
        self._set_on_state_model("wavelength_adjustment_det_2", state_model)

        return state_model

    def _set_on_state_model(self, attribute_name, state_model):
        attribute = getattr(self._view, attribute_name)
        if attribute:
            setattr(state_model, attribute_name, attribute)

    def _get_table_model(self):
        # 1. Create a new table model
        user_file = self._view.get_user_file_path()
        batch_file = self._view.get_batch_file_path()

        table_model = TableModel()
        table_model.user_file = user_file
        self.batch_file = batch_file

        # 2. Iterate over each row, create a table row model and insert it
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            sample_scatter = self._view.get_cell(row=row, column=0, convert_to=str)
            sample_transmission = self._view.get_cell(row=row, column=1, convert_to=str)
            sample_direct = self._view.get_cell(row=row, column=2, convert_to=str)
            can_scatter = self._view.get_cell(row=row, column=3, convert_to=str)
            can_transmission = self._view.get_cell(row=row, column=4, convert_to=str)
            can_direct = self._view.get_cell(row=row, column=5, convert_to=str)

            # Get the options string
            options_string = self._get_options(row)

            table_index_model = TableIndexModel(row, sample_scatter, sample_transmission, sample_direct,
                                                can_scatter, can_transmission, can_direct,
                                                options_column_string=options_string)
            table_model.add_table_entry(row, table_index_model)
        return table_model

    def _create_states(self, state_model, table_model):
        """
        Here we create the states based on the settings in the models
        """
        number_of_rows = self._view.get_number_of_rows()
        states = {}
        gui_state_director = GuiStateDirector(table_model, state_model, self._facility)
        for row in range(number_of_rows):
            if not self.is_empty_row(row):
                try:
                    state = gui_state_director.create_state(row)
                    states.update({row: state})
                except ValueError as e:
                    sans_logger.error("There was a bad entry for row {}. See here for more details: {}".format(row, str(e)))
                    raise RuntimeError("There was a bad entry for row {}. "
                                       "See here for more details: {}".format(row, str(e)))
        return states

    def _populate_row_in_table(self, row):
        """
        Adds a row to the table
        """
        def get_string_entry(_tag, _row):
            _element = ""
            if _tag in _row:
                _element = _row[_tag]
            return _element

        # 1. Pull out the entries
        sample_scatter = get_string_entry(BatchReductionEntry.SampleScatter, row)
        sample_transmission = get_string_entry(BatchReductionEntry.SampleTransmission, row)
        sample_direct = get_string_entry(BatchReductionEntry.SampleDirect, row)
        can_scatter = get_string_entry(BatchReductionEntry.CanScatter, row)
        can_transmission = get_string_entry(BatchReductionEntry.CanTransmission, row)
        can_direct = get_string_entry(BatchReductionEntry.CanDirect, row)

        # 2. Create entry that can be understood by table
        row_entry = "SampleScatter:{0},SampleTransmission:{1},SampleDirect:{2}," \
                    "CanScatter:{3},CanTransmission:{4},CanDirect:{5}".format(sample_scatter, sample_transmission,
                                                                              sample_direct, can_scatter,
                                                                              can_transmission, can_direct)
        self._view.add_row(row_entry)

    # ------------------------------------------------------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------------------------------------------------------
    def _setup_instrument_specific_settings(self):
        # Get the first run number of the scatter data for the first table
        sample_scatter = self._view.get_cell(row=0, column=0, convert_to=str)

        # Check if it exists at all
        if not sample_scatter:
            return

        # Get the file information from
        file_information_factory = SANSFileInformationFactory()
        try:
            self._file_information = file_information_factory.create_sans_file_information(sample_scatter)
        except NotImplementedError:
            sans_logger.warning("Could not get file information from {}.".format(sample_scatter))
            self._file_information = None

        # Provide the instrument specific settings
        if self._file_information:
            # Set the instrument on the table
            instrument = self._file_information.get_instrument()
            self._view.set_instrument_settings(SANSInstrument.to_string(instrument))

            # Set the reduction mode
            reduction_mode = get_reduction_mode_strings_for_gui(instrument=instrument)
            self._view.reduction_mode = reduction_mode
        else:
            self._view.set_instrument_settings(SANSInstrument.to_string(SANSInstrument.NoInstrument))
            reduction_mode = get_reduction_mode_strings_for_gui()
            self._view.reduction_mode = reduction_mode

    # ------------------------------------------------------------------------------------------------------------------
    # Setting workaround for state in DataProcessorWidget
    # ------------------------------------------------------------------------------------------------------------------
    def _remove_dummy_workspaces_and_row_index(self):
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            self._remove_from_options(row, "InputWorkspace")
            self._remove_from_options(row, "RowIndex")

    def _set_indices(self):
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            to_set = Property.EMPTY_INT if self.is_empty_row(row) else row
            self._add_to_options(row, "RowIndex", to_set)

    def _set_dummy_workspace(self):
        number_of_rows = self._view.get_number_of_rows()
        for row in range(number_of_rows):
            self._add_to_options(row, "InputWorkspace", SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME)

    @staticmethod
    def _create_dummy_input_workspace():
        if not AnalysisDataService.doesExist(SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME):
            create_alg = AlgorithmManager.create("CreateSampleWorkspace")
            create_alg.initialize()
            create_alg.setProperty("OutputWorkspace",  SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME)
            create_alg.setProperty("WorkspaceType",  "Histogram")
            create_alg.setProperty("NumBanks",  1)
            create_alg.setProperty("NumMonitors",  1)
            create_alg.setProperty("BankPixelWidth",  1)
            create_alg.setProperty("XMin",  0)
            create_alg.setProperty("XMax",  1)
            create_alg.setProperty("BinWidth",  1)
            create_alg.execute()

    @staticmethod
    def _delete_dummy_input_workspace():
        if AnalysisDataService.doesExist(SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME):
            AnalysisDataService.remove(SANS_DUMMY_INPUT_ALGORITHM_PROPERTY_NAME)