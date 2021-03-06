from __future__ import (absolute_import, division, print_function)
import numpy as np
import re
import warnings
from six import string_types


# RegEx pattern matching a composite function parameter name, eg f2.Sigma.
FN_PATTERN = re.compile('f(\\d+)\\.(.+)')

# RegEx pattern matching a composite function parameter name, eg f2.Sigma. Multi-spectrum case.
FN_MS_PATTERN = re.compile('f(\\d+)\\.f(\\d+)\\.(.+)')


def makeWorkspace(xArray, yArray):
    """Create a workspace that doesn't appear in the ADS"""
    from mantid.api import AlgorithmManager
    alg = AlgorithmManager.createUnmanaged('CreateWorkspace')
    alg.initialize()
    alg.setChild(True)
    alg.setProperty('DataX', xArray)
    alg.setProperty('DataY', yArray)
    alg.setProperty('OutputWorkspace', 'dummy')
    alg.execute()
    return alg.getProperty('OutputWorkspace').value


def islistlike(arg):
    return (not hasattr(arg, "strip")) and (hasattr(arg, "__getitem__") or hasattr(arg, "__iter__"))


#pylint: disable=too-many-instance-attributes,too-many-public-methods
class CrystalField(object):
    """Calculates the crystal fields for one ion"""

    ion_nre_map = {'Ce': 1, 'Pr': 2, 'Nd': 3, 'Pm': 4, 'Sm': 5, 'Eu': 6, 'Gd': 7,
                   'Tb': 8, 'Dy': 9, 'Ho': 10, 'Er': 11, 'Tm': 12, 'Yb': 13}

    allowed_symmetries = ['C1', 'Ci', 'C2', 'Cs', 'C2h', 'C2v', 'D2', 'D2h', 'C4', 'S4', 'C4h',
                          'D4', 'C4v', 'D2d', 'D4h', 'C3', 'S6', 'D3', 'C3v', 'D3d', 'C6', 'C3h',
                          'C6h', 'D6', 'C6v', 'D3h', 'D6h', 'T', 'Td', 'Th', 'O', 'Oh']

    default_peakShape = 'Gaussian'
    default_background = 'FlatBackground'
    default_spectrum_size = 200

    field_parameter_names = ['BmolX','BmolY','BmolZ','BextX','BextY','BextZ',
                             'B20','B21','B22','B40','B41','B42','B43','B44','B60','B61','B62','B63','B64','B65','B66',
                             'IB21','IB22','IB41','IB42','IB43','IB44','IB61','IB62','IB63','IB64','IB65','IB66']

    def __init__(self, Ion, Symmetry, **kwargs):
        """
        Constructor.

        @param Ion: A rare earth ion. Possible values:
                    Ce, Pr, Nd, Pm, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb

        @param Symmetry: Symmetry of the field. Possible values:
                         C1, Ci, C2, Cs, C2h, C2v, D2, D2h, C4, S4, C4h, D4, C4v, D2d, D4h, C3,
                         S6, D3, C3v, D3d, C6, C3h, C6h, D6, C6v, D3h, D6h, T, Td, Th, O, Oh

        @param kwargs: Other field parameters and attributes. Acceptable values include:
                        ToleranceEnergy:     energy tolerance,
                        ToleranceIntensity:  intensity tolerance,
                        ResolutionModel:     A resolution model.
                        FWHMVariation:       Absolute value of allowed variation of a peak width during a fit.
                        FixAllPeaks:         A boolean flag that fixes all parameters of the peaks.

                        Field parameters:

                        BmolX: The x-component of the molecular field,
                        BmolY: The y-component of the molecular field,
                        BmolZ: The z-component of the molecular field,
                        BextX: The x-component of the external field,
                        BextY: The y-component of the external field,
                        BextZ: The z-component of the external field,
                        B20: Real part of the B20 field parameter,
                        B21: Real part of the B21 field parameter,
                        B22: Real part of the B22 field parameter,
                        B40: Real part of the B40 field parameter,
                        B41: Real part of the B41 field parameter,
                        B42: Real part of the B42 field parameter,
                        B43: Real part of the B43 field parameter,
                        B44: Real part of the B44 field parameter,
                        B60: Real part of the B60 field parameter,
                        B61: Real part of the B61 field parameter,
                        B62: Real part of the B62 field parameter,
                        B63: Real part of the B63 field parameter,
                        B64: Real part of the B64 field parameter,
                        B65: Real part of the B65 field parameter,
                        B66: Real part of the B66 field parameter,
                        IB21: Imaginary part of the B21 field parameter,
                        IB22: Imaginary part of the B22 field parameter,
                        IB41: Imaginary part of the B41 field parameter,
                        IB42: Imaginary part of the B42 field parameter,
                        IB43: Imaginary part of the B43 field parameter,
                        IB44: Imaginary part of the B44 field parameter,
                        IB61: Imaginary part of the B61 field parameter,
                        IB62: Imaginary part of the B62 field parameter,
                        IB63: Imaginary part of the B63 field parameter,
                        IB64: Imaginary part of the B64 field parameter,
                        IB65: Imaginary part of the B65 field parameter,
                        IB66: Imaginary part of the B66 field parameter,


                        Each of the following parameters can be either a single float or an array of floats.
                        They are either all floats or all arrays of the same size.

                        IntensityScaling: A scaling factor for the intensity of each spectrum.
                        FWHM: A default value for the full width at half maximum of the peaks.
                        Temperature: A temperature "of the spectrum" in Kelvin
                        PhysicalProperty: A list of PhysicalProperties objects denoting the required data type
                                          Note that physical properties datasets should follow inelastic spectra
                                          See the Crystal Field Python Interface help page for more details.
        """

        self._background = None

        if 'Temperature' in kwargs:
            temperature = kwargs['Temperature']
            del kwargs['Temperature']
        else:
            temperature = -1

        # Create self.function attribute
        self._makeFunction(Ion, Symmetry, temperature)
        self.Temperature = temperature
        self.Ion = Ion
        self.Symmetry = Symmetry
        self._resolutionModel = None
        self._physprop = None

        free_parameters = []
        for key in kwargs:
            if key == 'ToleranceEnergy':
                self.ToleranceEnergy = kwargs[key]
            elif key == 'ToleranceIntensity':
                self.ToleranceIntensity = kwargs[key]
            elif key == 'IntensityScaling':
                self.IntensityScaling = kwargs[key]
            elif key == 'FWHM':
                self.FWHM = kwargs[key]
            elif key == 'ResolutionModel':
                self.ResolutionModel = kwargs[key]
            elif key == 'NPeaks':
                self.NPeaks = kwargs[key]
            elif key == 'FWHMVariation':
                self.FWHMVariation = kwargs[key]
            elif key == 'FixAllPeaks':
                self.FixAllPeaks = kwargs[key]
            elif key == 'PhysicalProperty':
                self.PhysicalProperty = kwargs[key]
            else:
                # Crystal field parameters
                self.function.setParameter(key, kwargs[key])
                free_parameters.append(key)

        for param in CrystalField.field_parameter_names:
            if param not in free_parameters:
                self.function.fixParameter(param)

        self._setPeaks()

        # Eigensystem
        self._dirty_eigensystem = True
        self._eigenvalues = None
        self._eigenvectors = None
        self._hamiltonian = None

        # Peak lists
        self._dirty_peaks = True
        self._peakList = None

        # Spectra
        self._dirty_spectra = True
        self._spectra = {}
        self._plot_window = {}

        # self._setDefaultTies()
        self.chi2 = None

    def _makeFunction(self, ion, symmetry, temperature):
        from mantid.simpleapi import FunctionFactory
        if temperature is not None and islistlike(temperature) and len(temperature) > 1:
            self.function = FunctionFactory.createFunction('CrystalFieldMultiSpectrum')
            self._isMultiSpectrum = True
            tempStr = 'Temperatures'
        else:
            self.function = FunctionFactory.createFunction('CrystalFieldSpectrum')
            self._isMultiSpectrum = False
            tempStr = 'Temperature'
        self.function.setAttributeValue('Ion', ion)
        self.function.setAttributeValue('Symmetry', symmetry)
        if temperature:
            temperature = [float(val) for val in temperature] if islistlike(temperature) else float(temperature)
            self.function.setAttributeValue(tempStr, temperature)

    def _remakeFunction(self, temperature):
        """Redefines the internal function, e.g. when `Temperature` (number of datasets) change"""
        fieldParams = self._getFieldParameters()
        self._makeFunction(self.Ion, self.Symmetry, temperature)
        for item in fieldParams.items():
            self.function.setParameter(item[0], item[1])
        for param in CrystalField.field_parameter_names:
            if param not in fieldParams.keys():
                self.function.fixParameter(param)

    def _setPeaks(self):
        from .function import PeaksFunction
        if self._isMultiSpectrum:
            self._peaks = []
            for i in range(self.NumberOfSpectra):
                self._peaks.append(PeaksFunction(self.crystalFieldFunction, 'f%s.' % i, 1))
        else:
            self._peaks = PeaksFunction(self.crystalFieldFunction, '', 0)

    @property
    def crystalFieldFunction(self):
        if not self._isMultiSpectrum and self.background is not None:
            return self.function[1]
        else:
            return self.function

    def makePeaksFunction(self, i):
        """Form a definition string for the CrystalFieldPeaks function
        @param i: Index of a spectrum.
        """
        temperature = self._getTemperature(i)
        out = 'name=CrystalFieldPeaks,Ion=%s,Symmetry=%s,Temperature=%s' % (self.Ion, self.Symmetry, temperature)
        out += ',ToleranceEnergy=%s,ToleranceIntensity=%s' % (self.ToleranceEnergy, self.ToleranceIntensity)
        out += ',%s' % ','.join(['%s=%s' % item for item in self._getFieldParameters().items()])
        return out

    def makeSpectrumFunction(self, i=0):
        """Form a definition string for the CrystalFieldSpectrum function
        @param i: Index of a spectrum.
        """
        if not self._isMultiSpectrum:
            return str(self.function)
        else:
            funs = self.function.createEquivalentFunctions()
            return str(funs[i])

    def makePhysicalPropertiesFunction(self, i=0):
        """Form a definition string for one of the crystal field physical properties functions
        @param i: Index of the dataset (default=0), or a PhysicalProperties object.
        """
        if hasattr(i, 'toString'):
            out = i.toString()
        else:
            if self._physprop is None:
                raise RuntimeError('Physical properties environment not defined.')
            ppobj = self._physprop[i] if islistlike(self._physprop) else self._physprop
            if hasattr(ppobj, 'toString'):
                out = ppobj.toString()
            else:
                return ''
        out += ',Ion=%s,Symmetry=%s' % (self.Ion, self.Symmetry)
        fieldParams = self._getFieldParameters()
        if len(fieldParams) > 0:
            out += ',%s' % ','.join(['%s=%s' % item for item in fieldParams.items()])
        ties = self._getFieldTies()
        if len(ties) > 0:
            out += ',ties=(%s)' % ties
        constraints = self._getFieldConstraints()
        if len(constraints) > 0:
            out += ',constraints=(%s)' % constraints
        return out

    def makeMultiSpectrumFunction(self):
        import re
        return re.sub(r'FWHM[X|Y]\d+=\(\),', '', str(self.function))

    @property
    def Ion(self):
        """Get value of Ion attribute. For example:

        cf = CrystalField(...)
        ...
        ion = cf.Ion
        """
        return self.crystalFieldFunction.getAttributeValue('Ion')

    @Ion.setter
    def Ion(self, value):
        """Set new value of Ion attribute. For example:

        cf = CrystalField(...)
        ...
        cf.Ion = 'Pr'
        """
        if value not in self.ion_nre_map.keys():
            msg = 'Value %s is not allowed for attribute Ion.\nList of allowed values: %s' % \
                  (value, ', '.join(list(self.ion_nre_map.keys())))
            raise RuntimeError(msg)
        self.crystalFieldFunction.setAttributeValue('Ion', value)
        self._dirty_eigensystem = True
        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def Symmetry(self):
        """Get value of Symmetry attribute. For example:

        cf = CrystalField(...)
        ...
        symm = cf.Symmetry
        """
        return self.crystalFieldFunction.getAttributeValue('Symmetry')

    @Symmetry.setter
    def Symmetry(self, value):
        """Set new value of Symmetry attribute. For example:

        cf = CrystalField(...)
        ...
        cf.Symmetry = 'Td'
        """
        if value not in self.allowed_symmetries:
            msg = 'Value %s is not allowed for attribute Symmetry.\nList of allowed values: %s' % \
                  (value, ', '.join(self.allowed_symmetries))
            raise RuntimeError(msg)
        self.crystalFieldFunction.setAttributeValue('Symmetry', value)
        self._dirty_eigensystem = True
        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def ToleranceEnergy(self):
        """Get energy tolerance"""
        return self.crystalFieldFunction.getAttributeValue('ToleranceEnergy')

    @ToleranceEnergy.setter
    def ToleranceEnergy(self, value):
        """Set energy tolerance"""
        self.crystalFieldFunction.setAttributeValue('ToleranceEnergy', float(value))
        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def ToleranceIntensity(self):
        """Get intensity tolerance"""
        return self.crystalFieldFunction.getAttributeValue('ToleranceIntensity')

    @ToleranceIntensity.setter
    def ToleranceIntensity(self, value):
        """Set intensity tolerance"""
        self.crystalFieldFunction.setAttributeValue('ToleranceIntensity', float(value))
        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def IntensityScaling(self):
        if not self._isMultiSpectrum:
            return self.crystalFieldFunction.getParameterValue('IntensityScaling')
        iscaling = []
        for i in range(self.NumberOfSpectra):
            paramName = 'IntensityScaling%s' % i
            iscaling.append(self.crystalFieldFunction.getParameterValue(paramName))
        return iscaling

    @IntensityScaling.setter
    def IntensityScaling(self, value):
        if not self._isMultiSpectrum:
            if islistlike(value):
                if len(value) == 1:
                    value = value[0]
                else:
                    raise ValueError('IntensityScaling is expected to be a single floating point value')
            self.crystalFieldFunction.setParameter('IntensityScaling', value)
        else:
            n = self.NumberOfSpectra
            if not islistlike(value) or len(value) != n:
                raise ValueError('IntensityScaling is expected to be a list of %s values' % n)
            for i in range(n):
                paramName = 'IntensityScaling%s' % i
                self.crystalFieldFunction.setParameter(paramName, value[i])

        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def Temperature(self):
        attrName = 'Temperatures' if self._isMultiSpectrum else 'Temperature'
        return self.crystalFieldFunction.getAttributeValue(attrName)

    @Temperature.setter
    def Temperature(self, value):
        if islistlike(value) and len(value) == 1:
            value = value[0]
        if self._isMultiSpectrum:
            if not islistlike(value):
                # Try to keep current set of field parameters.
                self._remakeFunction(float(value))
                return
            self.crystalFieldFunction.setAttributeValue('Temperatures', value)
        else:
            if islistlike(value):
                self._remakeFunction(value)
                return
            self.crystalFieldFunction.setAttributeValue('Temperature', float(value))
        self._dirty_peaks = True
        self._dirty_spectra = True

    @property
    def FWHM(self):
        attrName = 'FWHMs' if self._isMultiSpectrum else 'FWHM'
        fwhm = self.crystalFieldFunction.getAttributeValue(attrName)
        if self._isMultiSpectrum:
            nDatasets = len(self.Temperature)
            if len(fwhm) != nDatasets:
                return list(fwhm) * nDatasets
        return fwhm

    @FWHM.setter
    def FWHM(self, value):
        if islistlike(value) and len(value) == 1:
            value = value[0]
        if self._isMultiSpectrum:
            if not islistlike(value):
                value = [value] * self.NumberOfSpectra
            self.crystalFieldFunction.setAttributeValue('FWHMs', value)
        else:
            if islistlike(value):
                raise ValueError('FWHM is expected to be a single floating point value')
            self.crystalFieldFunction.setAttributeValue('FWHM', float(value))
        self._dirty_spectra = True

    @property
    def FWHMVariation(self):
        return self.crystalFieldFunction.getAttributeValue('FWHMVariation')

    @FWHMVariation.setter
    def FWHMVariation(self, value):
        self.crystalFieldFunction.setAttributeValue('FWHMVariation', float(value))
        self._dirty_spectra = True

    def __getitem__(self, item):
        return self.crystalFieldFunction.getParameterValue(item)

    def __setitem__(self, key, value):
        self._dirty_spectra = True
        self.crystalFieldFunction.setParameter(key, value)

    @property
    def ResolutionModel(self):
        return self._resolutionModel

    @ResolutionModel.setter
    def ResolutionModel(self, value):
        from .function import ResolutionModel
        if isinstance(value, ResolutionModel):
            self._resolutionModel = value
        else:
            self._resolutionModel = ResolutionModel(value)
        if self._isMultiSpectrum:
            if not self._resolutionModel.multi or self._resolutionModel.NumberOfSpectra != self.NumberOfSpectra:
                raise RuntimeError('Resolution model is expected to have %s functions, found %s' %
                                   (self.NumberOfSpectra, self._resolutionModel.NumberOfSpectra))
            for i in range(self.NumberOfSpectra):
                model = self._resolutionModel.model[i]
                self.crystalFieldFunction.setAttributeValue('FWHMX%s' % i, model[0])
                self.crystalFieldFunction.setAttributeValue('FWHMY%s' % i, model[1])
        else:
            model = self._resolutionModel.model
            self.crystalFieldFunction.setAttributeValue('FWHMX', model[0])
            self.crystalFieldFunction.setAttributeValue('FWHMY', model[1])

    @property
    def FixAllPeaks(self):
        return self.crystalFieldFunction.getAttributeValue('FixAllPeaks')

    @FixAllPeaks.setter
    def FixAllPeaks(self, value):
        self.crystalFieldFunction.setAttributeValue('FixAllPeaks', value)

    @property
    def PeakShape(self):
        return self.crystalFieldFunction.getAttributeValue('PeakShape')

    @PeakShape.setter
    def PeakShape(self, value):
        self.crystalFieldFunction.setAttributeValue('PeakShape', value)

    @property
    def NumberOfSpectra(self):
        return self.crystalFieldFunction.getNumberDomains()

    @property
    def NPeaks(self):
        return self.crystalFieldFunction.getAttributeValue('NPeaks')

    @NPeaks.setter
    def NPeaks(self, value):
        self.crystalFieldFunction.setAttributeValue('NPeaks', value)

    @property
    def peaks(self):
        return self._peaks

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        """
        Define the background function.
        Args:
            value: an instance of function.Background class or a list of instances
                in a multi-spectrum case
        """
        from .function import Background
        from mantid.simpleapi import FunctionFactory
        if self._background is not None:
            raise ValueError('Background has been set already')
        if not isinstance(value, Background):
            raise TypeError('Expected a Background object, found %s' % str(value))
        if not self._isMultiSpectrum:
            fun_str = value.toString() + ';' + str(self.function)
            self.function = FunctionFactory.createInitialized(fun_str)
            self._background = self._makeBackgroundObject(value)
            self._setPeaks()
        else:
            self.function.setAttributeValue("Background", value.toString())
            self._background = []
            for ispec in range(self.NumberOfSpectra):
                prefix = 'f%s.' % ispec
                self._background.append(self._makeBackgroundObject(value, prefix))

    def _makeBackgroundObject(self, value, prefix=''):
        from .function import Background, Function
        if value.peak is not None and value.background is not None:
            peak = Function(self.function, prefix=prefix + 'f0.f0.')
            background = Function(self.function, prefix=prefix + 'f0.f1.')
        elif value.peak is not None:
            peak = Function(self.function, prefix=prefix + 'f0.')
            background = None
        elif value.background is not None:
            peak = None
            background = Function(self.function, prefix=prefix + 'f0.')
        return Background(peak=peak, background=background)

    @property
    def PhysicalProperty(self):
        return self._physprop

    @PhysicalProperty.setter
    def PhysicalProperty(self, value):
        from .function import PhysicalProperties
        vlist = value if islistlike(value) else [value]
        if all([isinstance(pp, PhysicalProperties) for pp in vlist]):
            nOldPP = len(self._physprop) if islistlike(self._physprop) else (0 if self._physprop is None else 1)
            self._physprop = value
        else:
            errmsg = 'PhysicalProperty input must be a PhysicalProperties'
            errmsg += ' instance or a list of such instances'
            raise ValueError(errmsg)
        # If a spectrum (temperature) is already defined, or multiple physical properties
        # given, redefine the CrystalFieldMultiSpectrum function.
        if not self.isPhysicalPropertyOnly or islistlike(self.PhysicalProperty):
            tt = self.Temperature if islistlike(self.Temperature) else [self.Temperature]
            ww = list(self.FWHM) if islistlike(self.FWHM) else [self.FWHM]
            # Last n-set of temperatures correspond to PhysicalProperties
            if nOldPP > 0:
                tt = tt[:-nOldPP]
            # Removes 'negative' temperature, which is a flag for no INS dataset
            tt = [val for val in tt if val > 0]
            pptt = [0 if val.Temperature is None else val.Temperature for val in vlist]
            self._remakeFunction(list(tt)+pptt)
            if len(tt) > 0 and len(pptt) > 0:
                ww += [0] * len(pptt)
            self.FWHM = ww
            ppids = [pp.TypeID for pp in vlist]
            self.function.setAttributeValue('PhysicalProperties', [0]*len(tt)+ppids)
            for attribs in [pp.getAttributes(i+len(tt)) for i, pp in enumerate(vlist)]:
                for item in attribs.items():
                    self.function.setAttributeValue(item[0], item[1])

    @property
    def isPhysicalPropertyOnly(self):
        return (not islistlike(self.Temperature) and self.Temperature < 0
                and self.PhysicalProperty is not None)

    def ties(self, **kwargs):
        """Set ties on the field parameters.

        @param kwargs: Ties as name=value pairs: name is a parameter name,
            the value is a tie string or a number. For example:
                tie(B20 = 0.1, IB23 = '2*B23')
        """
        for tie in kwargs:
            self.crystalFieldFunction.tie(tie, str(kwargs[tie]))

    def constraints(self, *args):
        """
        Set constraints for the field parameters.

        @param args: A list of constraints. For example:
                constraints('B00 > 0', '0.1 < B43 < 0.9')
        """
        self.crystalFieldFunction.addConstraints(','.join(args))

    def getEigenvalues(self):
        self._calcEigensystem()
        return self._eigenvalues

    def getEigenvectors(self):
        self._calcEigensystem()
        return self._eigenvectors

    def getHamiltonian(self):
        self._calcEigensystem()
        return self._hamiltonian

    def getPeakList(self, i=0):
        """Get the peak list for spectrum i as a numpy array"""
        self._calcPeaksList(i)
        peaks = np.array([self._peakList.column(0), self._peakList.column(1)])
        return peaks

    def getSpectrum(self, i=0, workspace=None, ws_index=0):
        """
        Get the i-th spectrum calculated with the current field and peak parameters.

        Alternatively can be called getSpectrum(workspace, ws_index). Spectrum index i is assumed zero.

        Examples:

            cf.getSpectrum() # Return the first spectrum calculated on a generated set of x-values.
            cf.getSpectrum(1, ws, 5) # Calculate the second spectrum using the x-values from the 6th spectrum
                                     # in workspace ws.
            cf.getSpectrum(ws) # Calculate the first spectrum using the x-values from the 1st spectrum
                               # in workspace ws.
            cf.getSpectrum(ws, 3) # Calculate the first spectrum using the x-values from the 4th spectrum
                                  # in workspace ws.

        @param i: Index of a spectrum to get.
        @param workspace: A workspace to base on. If not given the x-values of the output spectrum will be
                          generated.
        @param ws_index:  An index of a spectrum from workspace to use.
        @return: A tuple of (x, y) arrays
        """
        if self._dirty_spectra:
            self._spectra = {}
            self._dirty_spectra = False

        wksp = workspace
        # Allow to call getSpectrum with a workspace as the first argument.
        if not isinstance(i, int):
            if wksp is not None:
                if not isinstance(wksp, int):
                    raise RuntimeError('Spectrum index is expected to be int. Got %s' % i.__class__.__name__)
                ws_index = wksp
            wksp = i
            i = 0

        if (self.Temperature[i] if islistlike(self.Temperature) else self.Temperature) < 0:
            raise RuntimeError('You must first define a temperature for the spectrum')

        # Workspace is given, always calculate
        if wksp is None:
            xArray = None
        elif isinstance(wksp, list) or isinstance(wksp, np.ndarray):
            xArray = wksp
        else:
            return self._calcSpectrum(i, wksp, ws_index)

        if xArray is None:
            if i in self._spectra:
                return self._spectra[i]
            else:
                x_min, x_max = self.calc_xmin_xmax(i)
                xArray = np.linspace(x_min, x_max, self.default_spectrum_size)

        yArray = np.zeros_like(xArray)
        wksp = makeWorkspace(xArray, yArray)
        self._spectra[i] = self._calcSpectrum(i, wksp, 0)
        return self._spectra[i]

    def getHeatCapacity(self, workspace=None, ws_index=0):
        """
        Get the heat cacpacity calculated with the current crystal field parameters

        Examples:

            cf.getHeatCapacity()    # Returns the heat capacity from 1 < T < 300 K in 1 K steps
            cf.getHeatCapacity(ws)  # Returns the heat capacity with temperatures given by ws.
            cf.getHeatCapacity(ws, ws_index)  # Use the spectrum indicated by ws_index for x-values

        @param workspace: Either a Mantid workspace whose x-values will be used as the temperatures
                          to calculate the heat capacity; or a list of numpy ndarray of temperatures.
                          Temperatures are in Kelvin.
        @param ws_index:  The index of a spectrum in workspace to use (default=0).
        """
        from .function import PhysicalProperties
        return self._getPhysProp(PhysicalProperties('Cv'), workspace, ws_index)

    def getSusceptibility(self, *args, **kwargs):
        """
        Get the magnetic susceptibility calculated with the current crystal field parameters.
        The susceptibility is calculated using Van Vleck's formula (2nd order perturbation theory)

        Examples:

            cf.getSusceptibility()      # Returns the susceptibility || [001] for 1<T<300 K in 1 K steps
            cf.getSusceptibility(T)     # Returns the susceptibility with temperatures given by T.
            cf.getSusceptibility(ws, 0) # Use x-axis of spectrum 0 of workspace ws as temperature
            cf.getSusceptibility(T, [1, 1, 1])  # Returns the susceptibility along [111].
            cf.getSusceptibility(T, 'powder')   # Returns the powder averaged susceptibility
            cf.getSusceptibility(T, 'cgs')      # Returns the susceptibility || [001] in cgs normalisation
            cf.getSusceptibility(..., Inverse=True)  # Calculates the inverse susceptibility instead
            cf.getSusceptibility(Temperature=ws, ws_index=0, Hdir=[1, 1, 0], Unit='SI', Inverse=True)

        @param Temperature: Either a Mantid workspace whose x-values will be used as the temperatures
                            to calculate the heat capacity; or a list or numpy ndarray of temperatures.
                            Temperatures are in Kelvin.
        @param ws_index: The index of a spectrum to use (default=0) if using a workspace for x.
        @param Hdir: The magnetic field direction to calculate the susceptibility along. Either a
                     Cartesian vector with z along the quantisation axis of the CF parameters, or the
                     string 'powder' (case insensitive) to get the powder averaged susceptibility
                     default: [0, 0, 1]
        @param Unit: Any one of the strings 'bohr', 'SI' or 'cgs' (case insensitive) to indicate whether
                     to output in atomic (bohr magneton/Tesla/ion), SI (m^3/mol) or cgs (cm^3/mol) units.
                     default: 'cgs'
        @param Inverse: Whether to calculate the susceptibility (Inverse=False, default) or inverse
                        susceptibility (Inverse=True).
        """
        from .function import PhysicalProperties

        # Sets defaults / parses keyword arguments
        workspace = kwargs['Temperature'] if 'Temperature' in kwargs.keys() else None
        ws_index = kwargs['ws_index'] if 'ws_index' in kwargs.keys() else 0

        # Parses argument list
        args = list(args)
        if len(args) > 0:
            workspace = args.pop(0)
        if 'mantid' in str(type(workspace)) and len(args) > 0:
            ws_index = args.pop(0)

        # _calcSpectrum updates parameters and susceptibility has a 'Lambda' parameter which other
        # CF functions don't have. This causes problems if you want to calculate another quantity after
        x, y = self._getPhysProp(PhysicalProperties('chi', *args, **kwargs), workspace, ws_index)
        return x, y

    def getMagneticMoment(self, *args, **kwargs):
        """
        Get the magnetic moment calculated with the current crystal field parameters.
        The moment is calculated by adding a Zeeman term to the CF Hamiltonian and then diagonlising
        the result. This function calculates either M(H) [default] or M(T), but can only calculate
        a 1D function (e.g. not M(H,T) simultaneously).

        Examples:

            cf.getMagneticMoment()       # Returns M(H) for H||[001] from 0 to 30 T in 0.1 T steps
            cf.getMagneticMoment(H)      # Returns M(H) for H||[001] at specified values of H (in Tesla)
            cf.getMagneticMoment(ws, 0)  # Use x-axis of spectrum 0 of ws as applied field magnitude.
            cf.getMagneticMoment(H, [1, 1, 1])  # Returns the magnetic moment along [111].
            cf.getMagneticMoment(H, 'powder')   # Returns the powder averaged M(H)
            cf.getMagneticMoment(H, 'cgs')      # Returns the moment || [001] in cgs units (emu/mol)
            cf.getMagneticMoment(Temperature=T) # Returns M(T) for H=1T || [001] at specified T (in K)
            cf.getMagneticMoment(10, [1, 1, 0], Temperature=T) # Returns M(T) for H=10T || [110].
            cf.getMagneticMoment(..., Inverse=True)  # Calculates 1/M instead (keyword only)
            cf.getMagneticMoment(Hmag=ws, ws_index=0, Hdir=[1, 1, 0], Unit='SI', Temperature=T, Inverse=True)

        @param Hmag: The magnitude of the applied magnetic field in Tesla, specified either as a Mantid
                     workspace whose x-values will be used; or a list or numpy ndarray of field points.
                     If Temperature is specified as a list / array / workspace, Hmag must be scalar.
                     (default: 0-30T in 0.1T steps, or 1T if temperature vector specified)
        @param Temperature: The temperature in Kelvin at which to calculate the moment.
                            Temperature is a keyword argument only. Can be a list, ndarray or workspace.
                            If Hmag is a list / array / workspace, Temperature must be scalar.
                            (default=1K)
        @param ws_index: The index of a spectrum to use (default=0) if using a workspace for x.
        @param Hdir: The magnetic field direction to calculate the susceptibility along. Either a
                     Cartesian vector with z along the quantisation axis of the CF parameters, or the
                     string 'powder' (case insensitive) to get the powder averaged susceptibility
                     default: [0, 0, 1]
        @param Unit: Any one of the strings 'bohr', 'SI' or 'cgs' (case insensitive) to indicate whether
                     to output in atomic (bohr magneton/ion), SI (Am^2/mol) or cgs (emu/mol) units.
                     default: 'bohr'
        @param Inverse: Whether to calculate the susceptibility (Inverse=False, default) or inverse
                        susceptibility (Inverse=True). Inverse is a keyword argument only.
        """
        from .function import PhysicalProperties

        # Sets defaults / parses keyword arguments
        workspace = None
        ws_index = kwargs['ws_index'] if 'ws_index' in kwargs.keys() else 0
        hmag = kwargs['Hmag'] if 'Hmag' in kwargs.keys() else 1.
        temperature = kwargs['Temperature'] if 'Temperature' in kwargs.keys() else 1.

        # Checks whether to calculate M(H) or M(T)
        hmag_isscalar = (not islistlike(hmag) or len(hmag) == 1)
        hmag_isvector = (islistlike(hmag) and len(hmag) > 1)
        t_isscalar = (not islistlike(temperature) or len(temperature) == 1)
        t_isvector = (islistlike(temperature) and len(temperature) > 1)
        if hmag_isscalar and (t_isvector or 'mantid' in str(type(temperature))):
            typeid = 4
            workspace = temperature
            kwargs['Hmag'] = hmag[0] if islistlike(hmag) else hmag
        else:
            typeid = 3
            if t_isscalar and (hmag_isvector or 'mantid' in str(type(hmag))):
                workspace = hmag
            kwargs['Temperature'] = temperature[0] if islistlike(temperature) else temperature

        # Parses argument list
        args = list(args)
        if len(args) > 0:
            if typeid == 4:
                kwargs['Hmag'] = args.pop(0)
            else:
                workspace = args.pop(0)
        if 'mantid' in str(type(workspace)) and len(args) > 0:
            ws_index = args.pop(0)

        pptype = 'M(T)' if (typeid == 4) else 'M(H)'
        self._typeid = self._str2id(typeid) if isinstance(typeid, string_types) else int(typeid)

        return self._getPhysProp(PhysicalProperties(pptype, *args, **kwargs), workspace, ws_index)

    def plot(self, i=0, workspace=None, ws_index=0, name=None):
        """Plot a spectrum. Parameters are the same as in getSpectrum(...)"""
        from mantidplot import plotSpectrum
        from mantid.api import AlgorithmManager
        createWS = AlgorithmManager.createUnmanaged('CreateWorkspace')
        createWS.initialize()

        xArray, yArray = self.getSpectrum(i, workspace, ws_index)
        ws_name = name if name is not None else 'CrystalField_%s' % self.Ion

        if isinstance(i, int):
            if workspace is None:
                if i > 0:
                    ws_name += '_%s' % i
                createWS.setProperty('DataX', xArray)
                createWS.setProperty('DataY', yArray)
                createWS.setProperty('OutputWorkspace', ws_name)
                createWS.execute()
                plot_window = self._plot_window[i] if i in self._plot_window else None
                self._plot_window[i] = plotSpectrum(ws_name, 0, window=plot_window, clearWindow=True)
            else:
                ws_name += '_%s' % workspace
                if i > 0:
                    ws_name += '_%s' % i
                createWS.setProperty('DataX', xArray)
                createWS.setProperty('DataY', yArray)
                createWS.setProperty('OutputWorkspace', ws_name)
                createWS.execute()
                plotSpectrum(ws_name, 0)
        else:
            ws_name += '_%s' % i
            createWS.setProperty('DataX', xArray)
            createWS.setProperty('DataY', yArray)
            createWS.setProperty('OutputWorkspace', ws_name)
            createWS.execute()
            plotSpectrum(ws_name, 0)

    def update(self, func):
        """
        Update values of the fitting parameters.
        @param func: A IFunction object containing new parameter values.
        """
        self.function = func
        if self._background is not None:
            if isinstance(self._background, list):
                for background in self._background:
                    background.update(func)
            else:
                self._background.update(func)
        self._setPeaks()

    def calc_xmin_xmax(self, i):
        """Calculate the x-range containing interesting features of a spectrum (for plotting)
        @param i: If an integer is given then calculate the x-range for the i-th spectrum.
                  If None given get the range covering all the spectra.
        @return: Tuple (xmin, xmax)
        """
        peaks = self.getPeakList(i)
        x_min = np.min(peaks[0])
        x_max = np.max(peaks[0])
        # dx probably should depend on peak widths
        deltaX = np.abs(x_max - x_min) * 0.1
        if x_min < 0:
            x_min -= deltaX
        x_max += deltaX
        return x_min, x_max

    def __add__(self, other):
        if isinstance(other, CrystalFieldMulti):
            return other.__radd__(self)
        return CrystalFieldMulti(CrystalFieldSite(self, 1.0), other)

    def __mul__(self, factor):
        ffactor = float(factor)
        if ffactor == 0.0:
            msg = 'Intensity scaling factor for %s(%s) is set to zero ' % (self.Ion, self.Symmetry)
            warnings.warn(msg, SyntaxWarning)
        return CrystalFieldSite(self, ffactor)

    def __rmul__(self, factor):
        return self.__mul__(factor)

    def _getTemperature(self, i):
        """Get temperature value for i-th spectrum."""
        if not self._isMultiSpectrum:
            if i != 0:
                raise RuntimeError('Cannot evaluate spectrum %s. Only 1 temperature is given.' % i)
            return float(self.Temperature)
        else:
            temperatures = self.Temperature
            nTemp = len(temperatures)
            if -nTemp <= i < nTemp:
                return float(temperatures[i])
            else:
                raise RuntimeError('Cannot evaluate spectrum %s. Only %s temperatures are given.' % (i, nTemp))

    def _getFWHM(self, i):
        """Get default FWHM value for i-th spectrum."""
        if not self._isMultiSpectrum:
            # if i != 0 assume that value for all spectra
            return float(self.FWHM)
        else:
            fwhm = self.FWHM
            nFWHM = len(fwhm)
            if -nFWHM <= i < nFWHM:
                return float(fwhm[i])
            else:
                raise RuntimeError('Cannot get FWHM for spectrum %s. Only %s FWHM are given.' % (i, nFWHM))

    def _getIntensityScaling(self, i):
        """Get default intensity scaling value for i-th spectrum."""
        if self._intensityScaling is None:
            raise RuntimeError('Default intensityScaling must be set.')
        if islistlike(self._intensityScaling):
            return self._intensityScaling[i] if len(self._intensityScaling) > 1 else self._intensityScaling[0]
        else:
            return self._intensityScaling

    def _getPeaksFunction(self, i):
        if isinstance(self.peaks, list):
            return self.peaks[i]
        return self.peaks

    def _getFieldParameters(self):
        """
        Get the values of non-zero field parameters.
        Returns:
            a dict with name: value pairs.
        """
        params = {}
        for name in self.field_parameter_names:
            value = self.crystalFieldFunction.getParameterValue(name)
            if value != 0.0:
                params[name] = value
        return params

    def _getFieldTies(self):
        import re
        ties = re.match('ties=\((.*?)\)', str(self.crystalFieldFunction))
        return ties.group(1) if ties else ''

    def _getFieldConstraints(self):
        import re
        constraints = re.match('constraints=\((.*?)\)', str(self.crystalFieldFunction))
        return constraints.group(1) if constraints else ''

    def _getPhysProp(self, ppobj, workspace, ws_index):
        """
        Returns a physical properties calculation
        @param ppobj: a PhysicalProperties object indicating the physical property type and environment
        @param workspace: workspace or array/list of x-values.
        @param ws_index:  An index of a spectrum in workspace to use.
        """
        try:
            typeid = ppobj.TypeID
        except AttributeError:
            raise RuntimeError('Invalid PhysicalProperties object specified')

        defaultX = [np.linspace(1, 300, 300), np.linspace(1, 300, 300), np.linspace(0, 30, 300),
                    np.linspace(0, 30, 300)]
        funstr = self.makePhysicalPropertiesFunction(ppobj)
        if workspace is None:
            xArray = defaultX[typeid - 1]
        elif isinstance(workspace, list) or isinstance(workspace, np.ndarray):
            xArray = workspace
        else:
            return self._calcSpectrum(funstr, workspace, ws_index)

        yArray = np.zeros_like(xArray)
        wksp = makeWorkspace(xArray, yArray)
        return self._calcSpectrum(funstr, wksp, ws_index)

    def _calcEigensystem(self):
        """Calculate the eigensystem: energies and wavefunctions.
        Also store them and the hamiltonian.
        Protected method. Shouldn't be called directly by user code.
        """
        if self._dirty_eigensystem:
            import CrystalField.energies as energies
            nre = self.ion_nre_map[self.Ion]
            self._eigenvalues, self._eigenvectors, self._hamiltonian = \
                energies.energies(nre, **self._getFieldParameters())
            self._dirty_eigensystem = False

    def _calcPeaksList(self, i):
        """Calculate a peak list for spectrum i"""
        if self._dirty_peaks:
            from mantid.api import AlgorithmManager
            alg = AlgorithmManager.createUnmanaged('EvaluateFunction')
            alg.initialize()
            alg.setChild(True)
            alg.setProperty('Function', self.makePeaksFunction(i))
            del alg['InputWorkspace']
            alg.setProperty('OutputWorkspace', 'dummy')
            alg.execute()
            self._peakList = alg.getProperty('OutputWorkspace').value

    def _calcSpectrum(self, i, workspace, ws_index, funstr=None):
        """Calculate i-th spectrum.

        @param i: Index of a spectrum or function string
        @param workspace: A workspace used to evaluate the spectrum function.
        @param ws_index:  An index of a spectrum in workspace to use.
        """
        from mantid.api import AlgorithmManager
        alg = AlgorithmManager.createUnmanaged('EvaluateFunction')
        alg.initialize()
        alg.setChild(True)
        alg.setProperty('Function', i if isinstance(i, string_types) else self.makeSpectrumFunction(i))
        alg.setProperty("InputWorkspace", workspace)
        alg.setProperty('WorkspaceIndex', ws_index)
        alg.setProperty('OutputWorkspace', 'dummy')
        alg.execute()
        out = alg.getProperty('OutputWorkspace').value
        # Create copies of the x and y because `out` goes out of scope when this method returns
        # and x and y get deallocated
        return np.array(out.readX(0)), np.array(out.readY(1))

    def isMultiSpectrum(self):
        return self._isMultiSpectrum


class CrystalFieldSite(object):
    """
    A helper class for the multi-site algebra. It is a result of the '*' operation between a CrystalField
    and a number. Multiplication sets the abundance for the site and which the returned object holds.
    """
    def __init__(self, crystalField, abundance):
        self.crystalField = crystalField
        self.abundance = abundance

    def __add__(self, other):
        if isinstance(other, CrystalField):
            return CrystalFieldMulti(self, CrystalFieldSite(other, 1))
        elif isinstance(other, CrystalFieldSite):
            return CrystalFieldMulti(self, other)
        elif isinstance(other, CrystalFieldMulti):
            return other.__radd__(self)
        raise TypeError('Unsupported operand type(s) for +: CrystalFieldSite and %s' % other.__class__.__name__)


class CrystalFieldMulti(object):
    """CrystalFieldMulti represents crystal field of multiple ions."""

    def __init__(self, *args):
        self.sites = []
        self.abundances = []
        for arg in args:
            if isinstance(arg, CrystalField):
                self.sites.append(arg)
                self.abundances.append(1.0)
            elif isinstance(arg, CrystalFieldSite):
                self.sites.append(arg.crystalField)
                self.abundances.append(arg.abundance)
            else:
                raise RuntimeError('Cannot include an object of type %s into a CrystalFieldMulti' % type(arg))
        self._ties = {}

    def makeSpectrumFunction(self):
        fun = ';'.join([a.makeSpectrumFunction() for a in self.sites])
        fun += self._makeIntensityScalingTies()
        ties = self.getTies()
        if len(ties) > 0:
            fun += ';ties=(%s)' % ties
        return 'composite=CompositeFunction,NumDeriv=1;' + fun

    def makePhysicalPropertiesFunction(self):
        # Handles relative intensities. Scaling factors here a fixed attributes not
        # variable parameters and we require the sum to be unity.
        factors = np.array(self.abundances)
        sum_factors = np.sum(factors)
        factstr = [',ScaleFactor=%s' % (str(factors[i] / sum_factors)) for i in range(len(self.sites))]
        fun = ';'.join([a.makePhysicalPropertiesFunction()+factstr[i] for a,i in enumerate(self.sites)])
        ties = self.getTies()
        if len(ties) > 0:
            fun += ';ties=(%s)' % ties
        return fun

    def makeMultiSpectrumFunction(self):
        fun = ';'.join([a.makeMultiSpectrumFunction() for a in self.sites])
        fun += self._makeIntensityScalingTiesMulti()
        ties = self.getTies()
        if len(ties) > 0:
            fun += ';ties=(%s)' % ties
        return 'composite=CompositeFunction,NumDeriv=1;' + fun

    def ties(self, **kwargs):
        """Set ties on the parameters."""
        for tie in kwargs:
            self._ties[tie] = kwargs[tie]

    def getTies(self):
        ties = ['%s=%s' % item for item in self._ties.items()]
        return ','.join(ties)

    def getSpectrum(self, i=0, workspace=None, ws_index=0):
        tt = []
        for site in self.sites:
            tt = tt + (list(site.Temperature) if islistlike(site.Temperature) else [site.Temperature])
        if any([val < 0 for val in tt]):
            raise RuntimeError('You must first define a temperature for the spectrum')
        largest_abundance= max(self.abundances)
        if workspace is not None:
            xArray, yArray = self.sites[0].getSpectrum(i, workspace, ws_index)
            yArray *= self.abundances[0] / largest_abundance
            ia = 1
            for arg in self.sites[1:]:
                _, yyArray = arg.getSpectrum(i, workspace, ws_index)
                yArray += yyArray * self.abundances[ia] / largest_abundance
                ia += 1
            return xArray, yArray
        x_min = 0.0
        x_max = 0.0
        for arg in self.sites:
            xmin, xmax = arg.calc_xmin_xmax(i)
            if xmin < x_min:
                x_min = xmin
            if xmax > x_max:
                x_max = xmax
        xArray = np.linspace(x_min, x_max, CrystalField.default_spectrum_size)
        _, yArray = self.sites[0].getSpectrum(i, xArray, ws_index)
        yArray *= self.abundances[0] / largest_abundance
        ia = 1
        for arg in self.sites[1:]:
            _, yyArray = arg.getSpectrum(i, xArray, ws_index)
            yArray += yyArray * self.abundances[ia] / largest_abundance
            ia += 1
        return xArray, yArray

    def update(self, func):
        nFunc = func.nFunctions()
        assert nFunc == len(self.sites)
        for i in range(nFunc):
            self.sites[i].update(func[i])

    def update_multi(self, func):
        nFunc = func.nFunctions()
        assert nFunc == len(self.sites)
        for i in range(nFunc):
            self.sites[i].update_multi(func[i])

    def _makeIntensityScalingTies(self):
        """
        Make a tie string that ties IntensityScaling's of the sites according to their abundances.
        """
        n_sites = len(self.sites)
        if n_sites < 2:
            return ''
        factors = np.array(self.abundances)
        i_largest = np.argmax(factors)
        largest_factor = factors[i_largest]
        tie_template = 'f%s.IntensityScaling=%s*' + 'f%s.IntensityScaling' % i_largest
        ties = []
        for i in range(n_sites):
            if i != i_largest:
                ties.append(tie_template % (i, factors[i] / largest_factor))
        s = ';ties=(%s)' % ','.join(ties)
        return s

    def _makeIntensityScalingTiesMulti(self):
        """
        Make a tie string that ties IntensityScaling's of the sites according to their abundances.
        """
        n_sites = len(self.sites)
        if n_sites < 2:
            return ''
        factors = np.array(self.abundances)
        i_largest = np.argmax(factors)
        largest_factor = factors[i_largest]
        tie_template = 'f{1}.IntensityScaling{0}={2}*f%s.IntensityScaling{0}' % i_largest
        ties = []
        n_spectra = self.sites[0].NumberOfSpectra
        for spec in range(n_spectra):
            for i in range(n_sites):
                if i != i_largest:
                    ties.append(tie_template.format(spec, i, factors[i] / largest_factor))
        s = ';ties=(%s)' % ','.join(ties)
        return s

    @property
    def isPhysicalPropertyOnly(self):
        return all([a.isPhysicalPropertyOnly for a in self.sites])

    @property
    def PhysicalProperty(self):
        return [a.PhysicalProperty for a in self.sites]

    @PhysicalProperty.setter
    def PhysicalProperty(self, value):
        for a in self.sites:
            a.PhysicalProperty = value

    @property
    def NumberOfSpectra(self):
        """ Returns the number of expected workspaces """
        num_spec = []
        for site in self.sites:
            num_spec.append(site.NumberOfSpectra)
        if len(set(num_spec)) > 1:
            raise ValueError('Number of spectra for each site not consistent with each other')
        return num_spec[0]

    @property
    def Temperature(self):
        tt = []
        for site in self.sites:
            tt.append([val for val in (site.Temperature if islistlike(site.Temperature) else [site.Temperature])])
        if len(set([tuple(val) for val in tt])) > 1:
            raise ValueError('Temperatures of spectra for each site not consistent with each other')
        return tt[0]

    @Temperature.setter
    def Temperature(self, value):
        for site in self.sites:
            site.Temperature = value

    def __add__(self, other):
        if isinstance(other, CrystalFieldMulti):
            cfm = CrystalFieldMulti()
            cfm.sites += self.sites + other.sites
            cfm.abundances += self.abundances + other.abundances
            return cfm
        elif isinstance(other, CrystalField):
            cfm = CrystalFieldMulti()
            cfm.sites += self.sites + [other]
            cfm.abundances += self.abundances + [1]
            return cfm
        elif isinstance(other, CrystalFieldSite):
            cfm = CrystalFieldMulti()
            cfm.sites += self.sites + [other.crystalField]
            cfm.abundances += self.abundances + [other.abundance]
            return cfm
        else:
            raise TypeError('Cannot add %s to CrystalFieldMulti' % other.__class__.__name__)

    def __radd__(self, other):
        if isinstance(other, CrystalFieldMulti):
            cfm = CrystalFieldMulti()
            cfm.sites += other.sites + self.sites
            cfm.abundances += other.abundances + self.abundances
            return cfm
        elif isinstance(other, CrystalField):
            cfm = CrystalFieldMulti()
            cfm.sites += [other] + self.sites
            cfm.abundances += [1] + self.abundances
            return cfm
        elif isinstance(other, CrystalFieldSite):
            cfm = CrystalFieldMulti()
            cfm.sites += [other.crystalField] + self.sites
            cfm.abundances += [other.abundance] + self.abundances
            return cfm
        else:
            raise TypeError('Cannot add %s to CrystalFieldMulti' % other.__class__.__name__)

    def __len__(self):
        return len(self.sites)

    def __getitem__(self, item):
        return self.sites[item]


#pylint: disable=too-few-public-methods
class CrystalFieldFit(object):
    """
    Object that controls fitting.
    """

    def __init__(self, Model=None, Temperature=None, FWHM=None, InputWorkspace=None, **kwargs):
        self.model = Model
        if Temperature is not None:
            self.model.Temperature = Temperature
        if FWHM is not None:
            self.model.FWHM = FWHM
        self._input_workspace = InputWorkspace
        self._output_workspace_base_name = 'fit'
        self._fit_properties = kwargs
        self._function = None
        self._estimated_parameters = None

    def fit(self):
        """
        Run Fit algorithm. Update function parameters.
        """
        self.check_consistency()
        if isinstance(self._input_workspace, list):
            return self._fit_multi()
        else:
            return self._fit_single()

    def monte_carlo(self, **kwargs):
        fix_all_peaks = self.model.FixAllPeaks
        self.model.FixAllPeaks = True
        if isinstance(self._input_workspace, list):
            self._monte_carlo_multi(**kwargs)
        else:
            self._monte_carlo_single(**kwargs)
        self.model.FixAllPeaks = fix_all_peaks

    def estimate_parameters(self, EnergySplitting, Parameters, **kwargs):
        from CrystalField.normalisation import split2range
        from mantid.api import mtd
        self.check_consistency()
        ranges = split2range(Ion=self.model.Ion, EnergySplitting=EnergySplitting,
                             Parameters=Parameters)
        constraints = [('%s<%s<%s' % (-bound, parName, bound)) for parName, bound in ranges.items()]
        self.model.constraints(*constraints)
        if 'Type' not in kwargs or kwargs['Type'] == 'Monte Carlo':
            if 'OutputWorkspace' in kwargs and kwargs['OutputWorkspace'].strip() != '':
                output_workspace = kwargs['OutputWorkspace']
            else:
                output_workspace = 'estimated_parameters'
                kwargs['OutputWorkspace'] = output_workspace
        else:
            output_workspace = None
        self.monte_carlo(**kwargs)
        if output_workspace is not None:
            self._estimated_parameters = mtd[output_workspace]

    def get_number_estimates(self):
        """
        Get a number of parameter sets estimated with self.estimate_parameters().
        """
        if self._estimated_parameters is None:
            return 0
        else:
            return self._estimated_parameters.columnCount() - 1

    def select_estimated_parameters(self, index):
        ne = self.get_number_estimates()
        if ne == 0:
            raise RuntimeError('There are no estimated parameters.')
        if index >= ne:
            raise RuntimeError('There are only %s sets of estimated parameters, requested set #%s' % (ne, index))
        for row in range(self._estimated_parameters.rowCount()):
            name = self._estimated_parameters.cell(row, 0)
            value = self._estimated_parameters.cell(row, index)
            self.model[name] = value
            if self._function is not None:
                self._function.setParameter(name, value)

    def _monte_carlo_single(self, **kwargs):
        """
        Call EstimateFitParameters algorithm in a single spectrum case.
        Args:
            **kwargs: Properties of the algorithm.
        """
        from mantid.api import AlgorithmManager
        fun = self.model.makeSpectrumFunction()
        if 'CrystalFieldMultiSpectrum' in fun:
            # Hack to ensure that 'PhysicalProperties' attribute is first
            # otherwise it won't set up other attributes properly
            fun = re.sub(r'(name=.*?,)(.*?)(PhysicalProperties=\(.*?\),)',r'\1\3\2', fun)
        alg = AlgorithmManager.createUnmanaged('EstimateFitParameters')
        alg.initialize()
        alg.setProperty('Function', fun)
        alg.setProperty('InputWorkspace', self._input_workspace)
        for param in kwargs:
            alg.setProperty(param, kwargs[param])
        alg.execute()
        function = alg.getProperty('Function').value
        self.model.update(function)
        self._function = function

    def _monte_carlo_multi(self, **kwargs):
        """
        Call EstimateFitParameters algorithm in a multi-spectrum case.
        Args:
            **kwargs: Properties of the algorithm.
        """
        from mantid.api import AlgorithmManager
        fun = self.model.makeMultiSpectrumFunction()
        if 'CrystalFieldMultiSpectrum' in fun:
            fun = re.sub(r'(name=.*?,)(.*?)(PhysicalProperties=\(.*?\),)',r'\1\3\2', fun)
        alg = AlgorithmManager.createUnmanaged('EstimateFitParameters')
        alg.initialize()
        alg.setProperty('Function', fun)
        alg.setProperty('InputWorkspace', self._input_workspace[0])
        i = 1
        for workspace in self._input_workspace[1:]:
            alg.setProperty('InputWorkspace_%s' % i, workspace)
            i += 1
        for param in kwargs:
            alg.setProperty(param, kwargs[param])
        alg.execute()
        function = alg.getProperty('Function').value
        self.model.update(function)
        self._function = function

    def _fit_single(self):
        """
        Fit when the model has a single spectrum.
        """
        from mantid.api import AlgorithmManager
        if self._function is None:
            if self.model.isPhysicalPropertyOnly:
                fun = self.model.makePhysicalPropertiesFunction()
            else:
                fun = self.model.makeSpectrumFunction()
        else:
            fun = str(self._function)
        if 'CrystalFieldMultiSpectrum' in fun:
            fun = re.sub(r'(name=.*?,)(.*?)(PhysicalProperties=\(.*?\),)',r'\1\3\2', fun)
        alg = AlgorithmManager.createUnmanaged('Fit')
        alg.initialize()
        alg.setProperty('Function', fun)
        alg.setProperty('InputWorkspace', self._input_workspace)
        alg.setProperty('Output', 'fit')
        self._set_fit_properties(alg)
        alg.execute()
        function = alg.getProperty('Function').value
        self.model.update(function)
        self.model.chi2 = alg.getProperty('OutputChi2overDoF').value

    def _fit_multi(self):
        """
        Fit when the model has multiple spectra.
        """
        from mantid.api import AlgorithmManager
        fun = self.model.makeMultiSpectrumFunction()
        if 'CrystalFieldMultiSpectrum' in fun:
            fun = re.sub(r'(name=.*?,)(.*?)(PhysicalProperties=\(.*?\),)',r'\1\3\2', fun)
        alg = AlgorithmManager.createUnmanaged('Fit')
        alg.initialize()
        alg.setProperty('Function', fun)
        alg.setProperty('InputWorkspace', self._input_workspace[0])
        i = 1
        for workspace in self._input_workspace[1:]:
            alg.setProperty('InputWorkspace_%s' % i, workspace)
            i += 1
        alg.setProperty('Output', 'fit')
        self._set_fit_properties(alg)
        alg.execute()
        function = alg.getProperty('Function').value
        self.model.update(function)
        self.model.chi2 = alg.getProperty('OutputChi2overDoF').value

    def _set_fit_properties(self, alg):
        for prop in self._fit_properties.items():
            alg.setProperty(*prop)

    def check_consistency(self):
        """ Checks that list input variables are consistent """
        num_ws = self.model.NumberOfSpectra
        errmsg = 'Number of input workspaces not consistent with model'
        if islistlike(self._input_workspace):
            if num_ws != len(self._input_workspace):
                raise ValueError(errmsg)
            # If single element list, force use of _fit_single()
            if len(self._input_workspace) == 1:
                self._input_workspace = self._input_workspace[0]
        elif num_ws != 1:
            raise ValueError(errmsg)
        if not self.model.isPhysicalPropertyOnly:
            tt = self.model.Temperature
            if any([val < 0 for val in (tt if islistlike(tt) else [tt])]):
                raise RuntimeError('You must first define a temperature for the spectrum')
