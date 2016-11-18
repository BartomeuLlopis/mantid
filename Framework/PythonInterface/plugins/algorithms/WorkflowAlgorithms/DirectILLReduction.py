# -*- coding: utf-8 -*-

from mantid.api import AlgorithmFactory, AnalysisDataServiceImpl, DataProcessorAlgorithm, FileAction, FileProperty, ITableWorkspaceProperty, MatrixWorkspaceProperty, mtd, PropertyMode,  WorkspaceProperty
from mantid.kernel import Direct, Direction, IntArrayProperty, StringListValidator, StringMandatoryValidator, UnitConversion
from mantid.simpleapi import AddSampleLog, CalculateFlatBackground,\
                             CloneWorkspace, ComputeCalibrationCoefVan,\
                             ConvertUnits, CorrectKiKf, CreateSingleValuedWorkspace, CreateWorkspace, DeleteWorkspace, DetectorEfficiencyCorUser, Divide, ExtractMonitors, ExtractSpectra, \
                             FindDetectorsOutsideLimits, FindEPP, GetEiMonDet, GroupWorkspaces, Integration, Load,\
                             MaskDetectors, MedianDetectorTest, MergeRuns, Minus, Multiply, NormaliseToMonitor, Plus, Rebin, Scale
import numpy

CLEANUP_DELETE = 'DeleteIntermediateWorkspaces'
CLEANUP_KEEP   = 'KeepIntermediateWorkspaces'

DIAGNOSTICS_YES   = 'DiagnoseDetectors'
DIAGNOSTICS_NO    = 'OmitDetectorDiagnostics'

INCIDENT_ENERGY_CALIBRATION_NO  = 'OmitIncidentEnergyCalibration'
INCIDENT_ENERGY_CALIBRATION_YES = 'CalibrateIncidentEnergy'

INDEX_TYPE_DETECTOR_ID     = 'DetectorID'
INDEX_TYPE_SPECTRUM_NUMBER = 'SpectrumNumber'
INDEX_TYPE_WORKSPACE_INDEX = 'WorkspaceIndex'

NORM_METHOD_MONITOR = 'Monitor'
NORM_METHOD_TIME    = 'AcquisitionTime'

PROP_BINNING_Q                        = 'QBinning'
PROP_BINNING_W                        = 'WBinning'
PROP_CD_WORKSPACE                     = 'CadmiumWorkspace'
PROP_CLEANUP_MODE                     = 'Cleanup'
PROP_DIAGNOSTICS_WORKSPACE            = 'DiagnosticsWorkspace'
PROP_DETECTORS_FOR_EI_CALIBRATION     = 'IncidentEnergyCalibrationDetectors'
PROP_DETECTOR_DIAGNOSTICS             = 'Diagnostics'
PROP_EC_WORKSPACE                     = 'EmptyCanWorkspace'
PROP_EPP_WORKSPACE                    = 'EPPWorkspace'
PROP_FLAT_BACKGROUND_SCALING          = 'FlatBackgroundScaling'
PROP_FLAT_BACKGROUND_WINDOW           = 'FlatBackgroundAveragingWindow'
PROP_FLAT_BACKGROUND_WORKSPACE        = 'FlatBackgroundWorkspace'
PROP_INCIDENT_ENERGY_CALIBRATION      = 'IncidentEnergyCalibration'
PROP_INCIDENT_ENERGY_WORKSPACE        = 'IncidentEnergyWorkspace'
PROP_INDEX_TYPE                       = 'IndexType'
PROP_INITIAL_ELASTIC_PEAK_REFERENCE   = 'InitialElasticPeakReference'
PROP_INPUT_FILE                       = 'InputFile'
PROP_INPUT_WORKSPACE                  = 'InputWorkspace'
PROP_MONITOR_EPP_WORKSPACE            = 'MonitorEPPWorkspace'
PROP_MONITOR_INDEX                    = 'Monitor'
PROP_NORMALISATION                    = 'Normalisation'
PROP_OUTPUT_DIAGNOSTICS_WORKSPACE     = 'OutputDiagnosticsWorkspace'
PROP_OUTPUT_EPP_WORKSPACE             = 'OutputEPPWorkspace'
PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE = 'OutputFlatBackgroundWorkspace'
PROP_OUTPUT_INCIDENT_ENERGY_WORKSPACE = 'OutputIncidentEnergyWorkspace'
PROP_OUTPUT_MONITOR_EPP_WORKSPACE     = 'OutputMonitorEPPWorkspace'
PROP_OUTPUT_WORKSPACE                 = 'OutputWorkspace'
PROP_REDUCTION_TYPE                   = 'ReductionType'
PROP_TRANSMISSION                     = 'Transmission'
PROP_USER_MASK                        = 'MaskedDetectors'
PROP_VANADIUM_WORKSPACE               = 'VanadiumWorkspace'

REDUCTION_TYPE_CD = 'Empty can/cadmium'
REDUCTION_TYPE_EC = REDUCTION_TYPE_CD
REDUCTION_TYPE_SAMPLE = 'Sample'
REDUCTION_TYPE_VANADIUM = 'Vanadium'

temp_workspaces = []

def namelogging(method):
    '''
    Decorator used within the NameSource class.
    '''
    def wrapper(self):
        name = method(self)
        self._names.add(name)
        return name
    return wrapper

# Name generator for temporary workspaces.
# TODO We may want to hide these and delete afterwards.
class NameSource:

    def __init__(self, prefix, cleanupMode):
        self._names = set()
        self._prefix = prefix
        if cleanupMode == CLEANUP_DELETE:
            self._prefix = '__' + prefix

    @namelogging
    def background(self):
        return self._prefix + '_bkg'

    @namelogging
    def backgroundSubtracted(self):
        return self._prefix + '_bkgsubtr'

    @namelogging
    def badDetectorSpuriousBkg(self):
        return self._prefix + '_bkgdiagn'

    @namelogging
    def badDetectorZeroCounts(self):
        return self._prefix + '_zerocountdiagn'

    @namelogging
    def cdSubtractedEc(self):
        return self._prefix + '_Cd_subtracted_EC'

    @namelogging
    def cdSubtractedSample(self):
        return self._prefix + '_Cd_subtracted'

    @namelogging
    def detectorEfficiencyCorrected(self):
        return self._prefix + '_deteff'

    @namelogging
    def diagnostics(self):
        return self._prefix + '_diagnostics_all'

    @namelogging
    def ecSubtracted(self):
        return self._prefix + '_ecsubtr'

    @namelogging
    def eiCalibrated(self):
        return self._prefix + '_ecalib'

    @namelogging
    def eiCalibration(self):
        return self._prefix + '_calibrated_incident_energy'

    @namelogging
    def energyConverted(self):
        return self._prefix +'_econv'

    @namelogging
    def epp(self):
        return self._prefix + '_epp'

    def getNames(self):
        '''
        Returns a set of all names already generated.
        '''
        return self._names

    @namelogging
    def incidentEnergy(self):
        return self._prefix + '_ie'

    @namelogging
    def kikf(self):
        return self._prefix + '_kikf'

    @namelogging
    def masked(self):
        return self._prefix + '_masked'

    @namelogging
    def merged(self):
        return self._prefix + '_merged'

    @namelogging
    def monitor(self):
        return self._prefix + '_monitors'

    @namelogging
    def monitorEPP(self):
        return self._prefix + '_monepp'

    @namelogging
    def monitorsExtracted(self):
        return self._prefix + '_detectors'

    @namelogging
    def normalizationFactorMonitor(self):
        return self._prefix + '_mon_norm_factor'

    @namelogging
    def normalizationFactorTime(self):
        return self._prefix + '_time_norm_factor'

    @namelogging
    def normalised(self):
        return self._prefix + '_norm'

    @namelogging
    def raw(self):
        return self._prefix + '_raw'

    @namelogging
    def rebinned(self):
        return self._prefix + '_rebinned'

    @namelogging
    def transmission(self):
        return self._prefix + '_transmission'

    @namelogging
    def transmissionCorrectedCdSubtracted(self):
        return self._prefix + '_transmission_corrected_Cd_subtracted'

    @namelogging
    def transmissionCorrectedEc(self):
        return self._prefix + '_transmission_corrected_EC'

    @namelogging
    def vanadiumNormalized(self):
        return self._prefix + '_vnorm'

def setAsBad(ws, index):
    ws.dataY(index)[0] += 1

class DirectILLReduction(DataProcessorAlgorithm):

    def __init__(self):
        DataProcessorAlgorithm.__init__(self)

    def category(self):
        return 'Workflow\\Inelastic'

    def name(self):
        return 'DirectILLReduction'

    def summary(self):
        return 'Data reduction workflow for the direct geometry time-of-flight spectrometers at ILL'

    def version(self):
        return 1

    def PyExec(self):
        reductionType = self.getProperty(PROP_REDUCTION_TYPE).value
        workspaceNamePrefix = self.getProperty(PROP_OUTPUT_WORKSPACE).valueAsStr
        cleanupMode = self.getProperty(PROP_CLEANUP_MODE).value
        workspaceNames = NameSource(workspaceNamePrefix, cleanupMode)
        indexType = self.getProperty(PROP_INDEX_TYPE).value

        # The variable 'workspace' shall hold the current 'main' data
        # throughout the algorithm.
        if self.getProperty(PROP_INPUT_FILE).value:
            # Load data
            inputFilename = self.getProperty(PROP_INPUT_FILE).value
            outWs = workspaceNames.raw()
            eppReference = self.getProperty(PROP_INITIAL_ELASTIC_PEAK_REFERENCE).value
            if eppReference:
                if mtd.doesExist(str(eppReference)):
                    workspace = Load(Filename=inputFilename,
                                     OutputWorkspace=outWs,
                                     WorkspaceVanadium=eppReference)
                else:
                    workspace = Load(Filename=inputFilename,
                                     OutputWorkspace=outWs,
                                     FilenameVanadium=eppReference)
            else:
                workspace = Load(Filename=inputFilename,
                                 OutputWorkspace=outWs,
                                 FilenameVanadium=eppReference)
            # Now merge the loaded files (if required)
            outWsName = workspaceNames.merged()
            workspace = MergeRuns(InputWorkspaces=workspace,
                                  OutputWorkspace=outWsName)

        elif self.getProperty(PROP_INPUT_WORKSPACE).value:
            workspace = self.getProperty(PROP_INPUT_WORKSPACE).value

        # Extract monitors to a separate workspace
        outWsName = workspaceNames.monitorsExtracted()
        monitorWorkspace = workspaceNames.monitor()
        workspace, monitorWorkspace = ExtractMonitors(InputWorkspace=workspace,
                                                      DetectorWorkspace=outWsName,
                                                      MonitorWorkspace=monitorWorkspace)
        monitorIndex = self.getProperty(PROP_MONITOR_INDEX).value
        monitorIndex = self._convertToWorkspaceIndex(monitorIndex, monitorWorkspace)

        # Fit time-independent background
        # ATM monitor background is ignored
        bkgInWs = self.getProperty(PROP_FLAT_BACKGROUND_WORKSPACE).value
        bkgOutWs = self.getPropertyValue(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE)
        # Fit background regardless of where it actually comes from.
        if bkgOutWs or not bkgInWs:
            if not bkgOutWs:
                bkgOutWs = workspaceNames.background()
            bkgWindow = self.getProperty(PROP_FLAT_BACKGROUND_WINDOW).value
            bkgScaling = self.getProperty(PROP_FLAT_BACKGROUND_SCALING).value
            bkgWorkspace = CalculateFlatBackground(InputWorkspace=workspace,
                                                   OutputWorkspace=bkgOutWs,
                                                   Mode='Moving Average',
                                                   OutputMode='Return Background',
                                                   SkipMonitors=False,
                                                   NullifyNegativeValues=False,
                                                   AveragingWindowWidth=bkgWindow)
            bkgWorkspace = Scale(InputWorkspace = bkgWorkspace,
                                 OutputWorkspace = bkgWorkspace,
                                 Factor = bkgScaling)
            if self.getProperty(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE).value:
                self.setProperty(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE, bkgOutWs)
        if bkgInWs:
            bkgWorkspace = self.getProperty(PROP_FLAT_BACKGROUND_WORKSPACE).value
            if bkgWorkspace and self.getProperty(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE).value:
                self.setProperty(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE, bkgOutWs)
        # Subtract time-independent background
        outWs = workspaceNames.backgroundSubtracted()
        workspace = Minus(LHSWorkspace=workspace,
                          RHSWorkspace=bkgWorkspace,
                          OutputWorkspace=outWs)

        # Find elastic peak positions
        eppInWs = self.getProperty(PROP_EPP_WORKSPACE).value
        monitorEppInWs = self.getProperty(PROP_MONITOR_EPP_WORKSPACE).value
        eppOutWs = self.getPropertyValue(PROP_OUTPUT_EPP_WORKSPACE)
        monitorEppOutWs = self.getPropertyValue(PROP_OUTPUT_MONITOR_EPP_WORKSPACE)
        # Same as with time-independent backgrounds: the EPP table may
        # came from outside. Otherwise make our own.
        if eppOutWs or not eppInWs:
            if not eppOutWs:
                eppOutWs = workspaceNames.epp()
            if not monitorEppOutWs:
                monitorEppOutWs = workspaceNames.monitorEPP()
            eppWorkspace = FindEPP(InputWorkspace = workspace,
                                   OutputWorkspace = eppOutWs)
            monitorEppWorkspace = FindEPP(InputWorkspace = monitorWorkspace,
                                          OutputWorkspace = monitorEppOutWs)
            if self.getPropertyValue(PROP_OUTPUT_EPP_WORKSPACE):
                self.setProperty(PROP_OUTPUT_EPP_WORKSPACE, eppWorkspace)
            if self.getPropertyValue(PROP_OUTPUT_MONITOR_EPP_WORKSPACE):
                self.setProperty(PROP_OUTPUT_MONITOR_EPP_WORKSPACE, monitorEppWorkspace)
        if eppInWs:
            eppWorkspace = self.getProperty(PROP_EPP_WORKSPACE).value
            monitorEppWorkspace = self.getProperty(PROP_MONITOR_EPP_WORKSPACE).value
            if not eppOutWs:
                # In any case, some output is required.
                eppOutWs = "dummy_output"
                emptyOutput = CreateSingleValuedWorkspace(OutputWorkspace=bkgOutWs,
                                                          DataValue = 0)
                self.setProperty(PROP_OUTPUT_EPP_WORKSPACE, eppOutWs)
                self.setProperty(PROP_OUTPUT_MONITOR_EPP_WORKSPACE, eppOutWs)

        # Detector diagnostics, if requested.
        if self.getProperty(PROP_DETECTOR_DIAGNOSTICS).value == DIAGNOSTICS_YES:
            diagnosticsWs = self.getProperty(PROP_DIAGNOSTICS_WORKSPACE).value
            # No input diagnostics workspace? Diagnose!
            if not diagnosticsWs:
                # 1. Detectors with zero counts.
                outWsName = workspaceNames.badDetectorZeroCounts()
                zeroCountDiagnostics, nFailures = FindDetectorsOutsideLimits(InputWorkspace=workspace,
                                                                             OutputWorkspace=outWsName)
                # 2. Detectors with high background
                outWsName = workspaceNames.badDetectorSpuriousBkg()
                bkgDiagnostics, nFailures = MedianDetectorTest(InputWorkspace=bkgWorkspace,
                                                               OutputWorkspace=outWsName,
                                                               LowThreshold=0.0,
                                                               HighThreshold=10,
                                                               LowOutlier=0.0)
                outWsName = workspaceNames.diagnostics()
                diagnosticsWs = Plus(LHSWorkspace=zeroCountDiagnostics,
                                     RHSWorkspace=bkgDiagnostics,
                                     OutputWorkspace=outWsName)
            # Mask detectors identified as bad.
            outWsName = workspaceNames.masked()
            workspace = CloneWorkspace(InputWorkspace=workspace,
                                       OutputWorkspace=outWsName)
            MaskDetectors(Workspace=workspace,
                          MaskedWorkspace=diagnosticsWs)
            # Save output if desired.
            if not self.getProperty(PROP_OUTPUT_DIAGNOSTICS_WORKSPACE).isDefault:
                self.setProperty(PROP_OUTPUT_DIAGNOSTICS_WORKSPACE, diagnosticsWs)
        # Apply user mask.
        userMask = self.getProperty(PROP_USER_MASK).value
        if indexType == INDEX_TYPE_DETECTOR_ID:
            MaskDetectors(Workspace=workspace,
                          DetectorList=userMask)
        elif indexType == INDEX_TYPE_SPECTRUM_NUMBER:
            MaskDetectors(Workspace=workspace,
                          SpectraList=userMask)
        elif indexType == INDEX_TYPE_WORKSPACE_INDEX:
            MaskDetectors(Workspace=workspace,
                          WorkspaceIndexList=userMask)
        else:
            raise RuntimeError('Unknown ' + PROP_INDEX_TYPE)

        # Get calibrated incident energy from somewhere
        # It should come from the same place as the epp workspace.
        # Or should it?
        eiCalibration = self.getProperty(PROP_INCIDENT_ENERGY_CALIBRATION).value
        if eiCalibration == INCIDENT_ENERGY_CALIBRATION_YES:
            instrument = workspace.getInstrument().getName()
            eiWs = self.getProperty(PROP_INCIDENT_ENERGY_WORKSPACE).value
            if not eiWs and instrument in ['IN4', 'IN6']:
                eiCalibrationDets = self.getProperty(PROP_DETECTORS_FOR_EI_CALIBRATION).value
                pulseInterval = workspace.getRun().getLogData('pulse_interval').value
                energy = GetEiMonDet(DetectorWorkspace=workspace,
                                     DetectorEPPTable=eppWorkspace,
                                     IndexType=indexType,
                                     Detectors=eiCalibrationDets,
                                     MonitorWorkspace=monitorWorkspace,
                                     MonitorEppTable=monitorEppWorkspace,
                                     Monitor=monitorIndex,
                                     PulseInterval=pulseInterval)
                eiWsName = workspaceNames.incidentEnergy()
                eiWs = CreateSingleValuedWorkspace(OutputWorkspace=eiWsName,
                                                   DataValue=energy)
            else:
                self.log().error('Instrument ' + instrument + ' not supported for incident energy calibration')
            if eiWs:
                # Update incident energy
                energy = mtd[eiWsName].readY(0)[0]
                outWs = workspaceNames.eiCalibrated()
                workspace = CloneWorkspace(InputWorkspace=workspace,
                                           OutputWorkspace=outWs)
                AddSampleLog(Workspace=workspace,
                             LogName='Ei',
                             LogText=str(energy),
                             LogType='Number',
                             NumberType='Double',
                             LogUnit='meV')
                wavelength = UnitConversion.run('Energy', 'Wavelength', energy, 0, 0, 0, Direct, 5)
                AddSampleLog(Workspace=workspace,
                             Logname='wavelength',
                             LogText=str(wavelength),
                             LogType='Number',
                             NumberType='Double',
                             LogUnit='Ångström')
                if not self.getProperty(PROP_OUTPUT_INCIDENT_ENERGY_WORKSPACE).isDefault:
                    self.setProperty(PROP_OUTPUT_INCIDENT_ENERGY_WORKSPACE, eiWs)

        # Normalisation to monitor/time
        normalisationMethod = self.getProperty(PROP_NORMALISATION).value
        if normalisationMethod:
            if normalisationMethod == NORM_METHOD_MONITOR:
                outWs = workspaceNames.normalised()
                normFactorWsName = workspaceNames.normalizationFactorMonitor()
                eppRow = monitorEppWorkspace.row(monitorIndex)
                sigma = eppRow['Sigma']
                centre = eppRow['PeakCentre']
                begin = centre - 3 * sigma
                end = centre + 3 * sigma
                workspace, normFactor = NormaliseToMonitor(InputWorkspace=workspace,
                                                           OutputWorkspace=outWs,
                                                           MonitorWorkspace=monitorWorkspace,
                                                           MonitorWorkspaceIndex=monitorIndex,
                                                           IntegrationRangeMin=begin,
                                                           IntegrationRangeMax=end,
                                                           NormFactorWS=normFactorWsName)
            elif normalisationMethod == NORM_METHOD_TIME:
                outWs = workspaceNames.normalised()
                normFactorWsName=workspaceNames.normalizationFactorTime()
                time = CreateSingleValuedWorkspace(OutputWorkspace=normFactorWsName,
                                                   DataValue=inWs.getLogData('actual_time').value)
                workspace = Divide(LHSWorkspace=workspace,
                                   RHSWorkspace=time,
                                   OutputWorkspace=outWs)
                DeleteWorkspace(Workspace=time)
            else:
                raise RuntimeError('Unknonwn normalisation method ' + normalisationMethod)

        # Reduction for empty can and cadmium ends here.
        if reductionType == REDUCTION_TYPE_CD or reductionType == REDUCTION_TYPE_EC:
            self._finalize(workspace, workspaceNames)
            return

        # Continuing with vanadium and sample reductions.

        # Empty can subtraction
        ecWs = self.getProperty(PROP_EC_WORKSPACE).value
        if ecWs:
            outWs = workspaceNames.ecSubtracted()
            cdWs = self.getProperty(PROP_CD_WORKSPACE).value
            transmission = self.getProperty(PROP_TRANSMISSION).value
            transmissionWsName = workspaceNames.transmission()
            transmission = CreateSingleValuedWorkspace(OutputWorkspace=transmissionWsName,
                                                       DataValue=transmission)
            # If Cd, calculate
            # out = (in - Cd) / transmission - (EC - Cd)
            if cdWs:
                cdSubtractedEcWsName = workspaceNames.cdSubtractedEc()
                ecWs = Minus(LHSWorkspace=ecWs,
                             RHSWorkspace=cdWs,
                             OutputWorkspace=cdSubtractedEcWsName)
                cdSubtractedWsName = workspaceNames.cdSubtractedSample()
                workspace = Minus(LHSWorkspace=workspace,
                                  RHSWorkspace=cdWs,
                                  OutputWorkspace=cdSubtractedWsName)
                correctedCdSubtractedWsName = workspaceNames.transmissionCorrectedCdSubtracted()
                workspace = Divide(LHSWorkspace=workspace,
                                   RHSWorkspace=transmission,
                                   OutputWorkspace=correctedCdSubtractedWsName)
                ecSubtractedWsName = workspaceNames.ecSubtracted()
                workspace = Minus(LHSWorkspace=workspace,
                                  RHSWorkspace=ecWs,
                                  OutputWorkspace=ecSubtractedWsName)
            # If no Cd, calculate
            # out = in - transmission * EC
            else:
                correctedEcWsName = workspaceNames.transmissionCorrectedEc()
                ecWs = Multiply(LHSWorkspace=ecWs,
                                RHSWorkspace=transmission,
                                OutputWorkspace=correctedEcWsName)
                ecSubtractedWsName = workspaceNames.ecSubtracted()
                workspace = Minus(LHSWorkspace=workspace,
                                  RHSWorkspace=ecWs,
                                  OutputWorkspace=ecSubtractedWsName)

        # Reduction for vanadium ends here.
        if reductionType == REDUCTION_TYPE_VANADIUM:
            # We output an integrated vanadium, ready to be used for
            # normalization.
            outWs = self.getPropertyValue(PROP_OUTPUT_WORKSPACE)
            # TODO For the time being, we may just want to integrate
            # the vanadium data as `ComputeCalibrationCoef` does not do
            # the best possible Debye-Waller correction.
            workspace = ComputeCalibrationCoefVan(VanadiumWorkspace=workspace,
                                                  EPPTable=eppWorkspace,
                                                  OutputWorkspace=outWs)
            self._finalize(workspace, workspaceNames)
            return

        # Continuing with sample reduction.

        # Vanadium normalisation
        vanadiumNormFactors = self.getProperty(PROP_VANADIUM_WORKSPACE).value
        if vanadiumNormFactors:
            outWs = workspaceNames.vanadiumNormalized()
            workspace = Divide(LHSWorkspace=workspace,
                               RHSWorkspace=vanadiumNormFactors,
                               OutputWorkspace=outWs)

        # Convert units from TOF to energy
        outWs = workspaceNames.energyConverted()
        workspace = ConvertUnits(InputWorkspace = workspace,
                                 OutputWorkspace = outWs,
                                 Target = 'DeltaE',
                                 EMode = 'Direct')

        # KiKf conversion
        outWs = workspaceNames.kikf()
        workspace = CorrectKiKf(InputWorkspace = workspace,
                                OutputWorkspace = outWs)

        # Rebinning
        # TODO automatize binning in w. Do we need rebinning in q as well?
        params = self.getProperty(PROP_BINNING_W).value
        if params:
            outWs = workspaceNames.rebinned()
            workspace = Rebin(InputWorkspace = workspace,
                              OutputWorkspace = outWs,
                              Params = params)

        # Detector efficiency correction
        outWs = workspaceNames.detectorEfficiencyCorrected()
        workspace = DetectorEfficiencyCorUser(InputWorkspace = workspace,
                                              OutputWorkspace = outWs)

        # TODO Self-shielding corrections

        self._finalize(workspace, workspaceNames)

    def PyInit(self):
        # TODO Property validation.
        # Inputs
        self.declareProperty(FileProperty(PROP_INPUT_FILE,
                                          '',
                                          action=FileAction.OptionalLoad,
                                          extensions=['nxs']))
        self.declareProperty(MatrixWorkspaceProperty(PROP_INPUT_WORKSPACE,
                                                     '',
                                                     optional=PropertyMode.Optional,
                                                     direction=Direction.Input))
        self.declareProperty(WorkspaceProperty(PROP_OUTPUT_WORKSPACE,
                             '',
                             direction=Direction.Output),
                             doc='The output of the algorithm')
        self.declareProperty(PROP_REDUCTION_TYPE,
                             REDUCTION_TYPE_SAMPLE,
                             validator=StringListValidator([REDUCTION_TYPE_SAMPLE, REDUCTION_TYPE_VANADIUM, REDUCTION_TYPE_CD, REDUCTION_TYPE_EC]),
                             direction=Direction.Input,
                             doc='Type of the reduction workflow and output')
        self.declareProperty(PROP_CLEANUP_MODE,
                             CLEANUP_DELETE,
                             validator=StringListValidator([CLEANUP_DELETE, CLEANUP_KEEP]),
                             direction=Direction.Input,
                             doc='What to do with intermediate workspaces')
        self.declareProperty(PROP_INITIAL_ELASTIC_PEAK_REFERENCE,
                             '',
                             direction=Direction.Input,
                             doc="Reference file or workspace for initial 'EPP' sample log entry")
        self.declareProperty(MatrixWorkspaceProperty(PROP_VANADIUM_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Reduced vanadium workspace')
        self.declareProperty(MatrixWorkspaceProperty(PROP_EC_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Reduced empty can workspace')
        self.declareProperty(MatrixWorkspaceProperty(PROP_CD_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Reduced cadmium workspace')
        self.declareProperty(ITableWorkspaceProperty(PROP_EPP_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Table workspace containing results from the FindEPP algorithm')
        self.declareProperty(ITableWorkspaceProperty(PROP_MONITOR_EPP_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Table workspace containing results from the FindEPP algorithm for the monitor workspace')
        self.declareProperty(PROP_INDEX_TYPE,
                             INDEX_TYPE_WORKSPACE_INDEX,
                             direction=Direction.Input,
                             doc='Type of numbers in ' + PROP_MONITOR_INDEX + ' and ' + PROP_DETECTORS_FOR_EI_CALIBRATION + ' properties')
        self.declareProperty(PROP_MONITOR_INDEX,
                             0,
                             direction=Direction.Input,
                             doc='Index of the main monitor')
        self.declareProperty(PROP_INCIDENT_ENERGY_CALIBRATION,
                             INCIDENT_ENERGY_CALIBRATION_YES,
                             validator=StringListValidator([INCIDENT_ENERGY_CALIBRATION_YES, INCIDENT_ENERGY_CALIBRATION_YES]),
                             direction=Direction.Input,
                             doc='Enable or disable incident energy calibration on IN4 and IN6')
        self.declareProperty(PROP_DETECTORS_FOR_EI_CALIBRATION,
                             '',
                             direction=Direction.Input,
                             doc='List of detectors used for the incident energy calibration')
        self.declareProperty(MatrixWorkspaceProperty(PROP_INCIDENT_ENERGY_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='A single-valued workspace holding the calibrated incident energy')
        self.declareProperty(PROP_FLAT_BACKGROUND_SCALING,
                             1.0,
                             direction=Direction.Input,
                             doc='Flat background scaling constant')
        self.declareProperty(PROP_FLAT_BACKGROUND_WINDOW,
                             30,
                             direction=Direction.Input,
                             doc='Running average window width (in bins) for flat background')
        self.declareProperty(MatrixWorkspaceProperty(PROP_FLAT_BACKGROUND_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Workspace from which to get flat background data')
        self.declareProperty(IntArrayProperty(PROP_USER_MASK,
                                              '',
                                              direction=Direction.Input),
                             doc='List of spectra to mask')
        self.declareProperty(PROP_DETECTOR_DIAGNOSTICS,
                             DIAGNOSTICS_YES,
                             validator=StringListValidator([DIAGNOSTICS_YES, DIAGNOSTICS_NO]),
                             direction=Direction.Input,
                             doc='If true, run detector diagnostics or apply ' + PROP_DIAGNOSTICS_WORKSPACE)
        self.declareProperty(MatrixWorkspaceProperty(PROP_DIAGNOSTICS_WORKSPACE,
                                                     '',
                                                     Direction.Input,
                                                     PropertyMode.Optional),
                             doc='Detector diagnostics workspace obtained from another reduction run.')
        self.declareProperty(PROP_NORMALISATION,
                             NORM_METHOD_MONITOR,
                             validator=StringListValidator([NORM_METHOD_MONITOR, NORM_METHOD_TIME]),
                             direction=Direction.Input,
                             doc='Normalisation method')
        self.declareProperty(PROP_TRANSMISSION,
                             1.0,
                             direction=Direction.Input,
                             doc='Sample transmission for empty can subtraction')
        self.declareProperty(PROP_BINNING_Q,
                             '',
                             direction=Direction.Input,
                             doc='Rebinning in q')
        self.declareProperty(PROP_BINNING_W,
                             '',
                             direction=Direction.Input,
                             doc='Rebinning in w')
        # Rest of the output properties.
        self.declareProperty(ITableWorkspaceProperty(PROP_OUTPUT_EPP_WORKSPACE,
                             '',
                             direction=Direction.Output,
                             optional=PropertyMode.Optional),
                             doc='Output workspace for elastic peak positions')
        self.declareProperty(WorkspaceProperty(PROP_OUTPUT_INCIDENT_ENERGY_WORKSPACE,
                                               '',
                                               direction=Direction.Output,
                                               optional=PropertyMode.Optional),
                             doc='Output workspace for calibrated inciden energy')
        self.declareProperty(ITableWorkspaceProperty(PROP_OUTPUT_MONITOR_EPP_WORKSPACE,
                             '',
                             direction=Direction.Output,
                             optional=PropertyMode.Optional),
                             doc='Output workspace for elastic peak positions')
        self.declareProperty(WorkspaceProperty(PROP_OUTPUT_FLAT_BACKGROUND_WORKSPACE,
                             '',
                             direction=Direction.Output,
                             optional=PropertyMode.Optional),
                             doc='Output workspace for flat background')
        self.declareProperty(WorkspaceProperty(PROP_OUTPUT_DIAGNOSTICS_WORKSPACE,
                                               '',
                                               direction=Direction.Output,
                                               optional=PropertyMode.Optional),
                             doc='Output workspace for detector diagnostics')

    def validateInputs(self):
        """
        Checks for issues with user input.
        """
        issues = dict()

        fileGiven = not self.getProperty(PROP_INPUT_FILE).isDefault
        wsGiven = not self.getProperty(PROP_INPUT_WORKSPACE).isDefault
        # Validate an input exists
        if fileGiven == wsGiven:
            issues[PROP_INPUT_FILE] = 'Must give either an input file or an input workspace.'

        return issues

    def _convertToWorkspaceIndex(self, i, workspace):
        indexType = self.getProperty(PROP_INDEX_TYPE).value
        if indexType == INDEX_TYPE_WORKSPACE_INDEX:
            return i
        elif indexType == INDEX_TYPE_SPECTRUM_NUMBER:
            return workspace.getIndexFromSpectrumNumber(i)
        else: # INDEX_TYPE_DETECTOR_ID
            for j in range(workspace.getNumberHistograms()):
                if workspace.getSpectrum(j).hasDetectorID(i):
                    return j
            raise RuntimeError('No workspace index found for detector id {0}'.format(i))

    def _finalize(self, outputWorkspace, workspaceNames):
        self.setProperty(PROP_OUTPUT_WORKSPACE, outputWorkspace)

        if self.getProperty(PROP_CLEANUP_MODE).value == CLEANUP_DELETE:
            # TODO: what can we delete earlier from this set?
            for ws in workspaceNames.getNames():
                if mtd.doesExist(ws):
                    DeleteWorkspace(Workspace = ws)

        self.log().debug('Finished')

AlgorithmFactory.subscribe(DirectILLReduction)