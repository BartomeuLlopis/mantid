# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

import DirectILL_common as common
from mantid.api import (AlgorithmFactory, DataProcessorAlgorithm, InstrumentValidator,
                        MatrixWorkspaceProperty, PropertyMode, WorkspaceGroupProperty, WorkspaceUnitValidator)
from mantid.kernel import (CompositeValidator, Direction, IntBoundedValidator,
                           Property, StringListValidator)
from mantid.simpleapi import (ConvertUnits, MonteCarloAbsorption)


class DirectILLSelfShielding(DataProcessorAlgorithm):
    """A workflow algorithm for self-shielding corrections."""

    def __init__(self):
        """Initialize an instance of the algorithm."""
        DataProcessorAlgorithm.__init__(self)

    def category(self):
        """Return the algorithm's category."""
        return 'Workflow\\Inelastic'

    def name(self):
        """Return the algorithm's name."""
        return 'DirectILLSelfShielding'

    def summary(self):
        """Return a summary of the algorithm."""
        return 'Calculates self-shielding correction for the direct geometry TOF spectrometers at ILL.'

    def version(self):
        """Return the algorithm's version."""
        return 1

    def PyExec(self):
        """Execute the algorithm."""
        subalgLogging = self.getProperty(common.PROP_SUBALG_LOGGING).value == common.SUBALG_LOGGING_ON
        wsNamePrefix = self.getProperty(common.PROP_OUTPUT_WS).valueAsStr
        cleanupMode = self.getProperty(common.PROP_CLEANUP_MODE).value
        wsNames = common.NameSource(wsNamePrefix, cleanupMode)
        wsCleanup = common.IntermediateWSCleanup(cleanupMode, subalgLogging)

        # Get input workspace.
        mainWS = self._inputWS(wsNames, wsCleanup, subalgLogging)

        # Self shielding and empty container subtraction, if requested.
        correctionWS = self._selfShielding(mainWS, wsNames, wsCleanup, subalgLogging)

        self._finalize(correctionWS, wsCleanup)

    def PyInit(self):
        """Initialize the algorithm's input and output properties."""
        greaterThanOneInt = IntBoundedValidator(lower=2)
        inputWorkspaceValidator = CompositeValidator()
        inputWorkspaceValidator.add(InstrumentValidator())
        inputWorkspaceValidator.add(WorkspaceUnitValidator('TOF'))

        # Properties.
        self.declareProperty(MatrixWorkspaceProperty(
            name=common.PROP_INPUT_WS,
            defaultValue='',
            validator=inputWorkspaceValidator,
            optional=PropertyMode.Optional,
            direction=Direction.Input),
            doc='Input workspace.')
        self.declareProperty(MatrixWorkspaceProperty(name=common.PROP_OUTPUT_WS,
                                                     defaultValue='',
                                                     direction=Direction.Output),
                             doc='The output corrections workspace.')
        self.declareProperty(name=common.PROP_CLEANUP_MODE,
                             defaultValue=common.CLEANUP_ON,
                             validator=StringListValidator([
                                 common.CLEANUP_ON,
                                 common.CLEANUP_OFF]),
                             direction=Direction.Input,
                             doc='What to do with intermediate workspaces.')
        self.declareProperty(name=common.PROP_SUBALG_LOGGING,
                             defaultValue=common.SUBALG_LOGGING_OFF,
                             validator=StringListValidator([
                                 common.SUBALG_LOGGING_OFF,
                                 common.SUBALG_LOGGING_ON]),
                             direction=Direction.Input,
                             doc='Enable or disable subalgorithms to ' +
                                 'print in the logs.')
        self.declareProperty(name=common.PROP_NUMBER_OF_SIMULATION_WAVELENGTHS,
                             defaultValue=Property.EMPTY_INT,
                             validator=greaterThanOneInt,
                             direction=Direction.Input,
                             doc='Number of points where the calculation is performed (default: all).')

    def validateInputs(self):
        """Check for issues with user input."""
        return dict()

    def _finalize(self, outWS, wsCleanup):
        """Do final cleanup and set the output property."""
        self.setProperty(common.PROP_OUTPUT_WS, outWS)
        wsCleanup.cleanup(outWS)
        wsCleanup.finalCleanup()

    def _inputWS(self, wsNames, wsCleanup, subalgLogging):
        """Return the raw input workspace."""
        mainWS = self.getProperty(common.PROP_INPUT_WS).value
        wsCleanup.protect(mainWS)
        return mainWS

    def _selfShielding(self, mainWS, wsNames, wsCleanup, subalgLogging):
        """Return the self shielding corrections."""
        wavelengthWSName = wsNames.withSuffix('input_in_wavelength')
        wavelengthWS = ConvertUnits(InputWorkspace=mainWS,
                                    OutputWorkspace=wavelengthWSName,
                                    Target='Wavelength',
                                    EMode='Direct',
                                    EnableLogging=subalgLogging)
        wavelengthPoints = self.getProperty(common.PROP_NUMBER_OF_SIMULATION_WAVELENGTHS).value
        correctionWSName = wsNames.withSuffix('correction')
        correctionWS = MonteCarloAbsorption(InputWorkspace=wavelengthWS,
                                            OutputWorkspace=correctionWSName,
                                            NumberOfWavelengthPoints=wavelengthPoints,
                                            Interpolation='CSpline',
                                            EnableLogging=subalgLogging)
        wsCleanup.cleanup(wavelengthWS)
        correctionWS = ConvertUnits(InputWorkspace=correctionWS,
                                    OutputWorkspace=correctionWSName,
                                    Target='TOF',
                                    EMode='Direct',
                                    EnableLogging=subalgLogging)
        return correctionWS


AlgorithmFactory.subscribe(DirectILLSelfShielding)