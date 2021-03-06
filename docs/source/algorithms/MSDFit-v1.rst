.. algorithm::

.. summary::

.. alias::

.. properties::

Description
-----------

Fits :math:`log(intensity)` vs :math:`Q^{2}` with a straight line for each run
to obtain the mean square displacement for a given range of runs.

This algorithm operates on the QSquared workspace (*_q2*) generated by the
:ref:`ElasticWindowMultiple <algm-ElasticWindowMultiple>` algorithm.

Workflow
--------

.. diagram:: MSDFit-v1_wkflw.dot

Usage
-----

**Example - Performing MSDFit on simulated data.**

.. testcode:: ExGeneratedDataFit

    # Create some data that is similar to the output of ElasticWindowMultiple
    sample = CreateSampleWorkspace(Function='User Defined',
                    UserDefinedFunction='name=ExpDecay,Height=1,Lifetime=6',
                    NumBanks=1, BankPixelWidth=1, XUnit='QSquared', XMin=0.0,
                    XMax=5.0, BinWidth=0.1)

    msd, param, fit = MSDFit(InputWorkspace=sample,
                             XStart=0.0, XEnd=5.0,
                             SpecMin=0, SpecMax=0)

    print 'A0: ' + str(msd.readY(0))
    print 'A1: ' + str(msd.readY(1))

Output:

.. testoutput:: ExGeneratedDataFit

    A0: [ 0.95908058]
    A1: [ 0.11014908]

.. categories::

.. sourcelink::
  :cpp: None
  :h: None
