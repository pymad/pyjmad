[![Build Status](https://travis-ci.org/pymad/pyjmad.svg?branch=master)](https://travis-ci.org/pymad/pyjmad)

# PyJMad
Yet another python wrapper around JMad using JPype. PyJMad aims for compatibility with other CERN Java-Python bridges, using cmmnbuild-dep-manager (and access to CERN resources) for easy side-by-side installation. A particular focus lies on interactive usage and integration with IPython/Jupyter.

### Set up:
```python
import pyjmad
jmad = pyjmad.JMad()
```

### Explore model definitions:
```python
jmad.model_definitions
```

### Setup a Model:
```python
md = jmad.model_definitions['LHC 2017']
jmad.create_model(md)
```
or simply:
```python
lhcModel = jmad.create_model('LHC 2017')
```

Set a Sequence and Optic to use:
```python
lhcModel.sequence = 'lhcb1'
lhcModel.optic = 'R2017a_A11mC11mA10mL10m'
```

### Twissing:
```python
twiss = lhcModel.twiss(variables=('S','BETX','BETY','X','Y'))
```
This will return a namedtuple:
* ``twiss.summary`` is a dict of the twiss summary
* ``twiss.data`` is a Pandas DataFrame of the twiss results

Plot it:
```python
plt.figure()
plt.plot(res.data.S, res.data.BETX)
plt.plot(res.data.S, res.data.BETY)
plt.show()
```

### Show and/or edit strengths:
```python
lhcModel.strengths
```
```python
lhcModel.strengths['on_x1'] = 140
lhcModel.strengths['on_x5'] = 140
print(lhcModel.strengths['on_x5'])
```
(jupyter/ipython autocompletion hints supported)

### Deal with Elements:
```python
print(lhcModel.elements)
corrector = lhcModel.elements['MCBCH.10L1.B1']
corrector.h_kick = 4.2e-6  # rad
# or equivalent
corrector.attributes['hkick'] = 4.2e-6
print(corrector.attributes)
```
(jupyter/ipython autocompletion hints supported, both on ``elements`` and ``attributes``)

List certain range of accelerator elements:
```python
lhcModel.elements['BPM.10L1.B1':'BPM.10R1.B1']
```

### Matching:
```python
from pyjmad.matching import *
mr = lhcModel.match(GlobalConstraint(Q1=62.28, Q2=60.31),
                    Vary('KQT4.L3', step=0.000001),
                    Vary('KQT4.R3', step=0.000001))
```

```python
mr = lhcModel.match(LocalConstraint('IP1', BETX=0.45, BETY=0.45),
                    Vary('KQX.L1', step=0.000001),
                    Vary('KQX.R1', step=0.000001))
```


### Open a JMad GUI
The GUI will share the state with the python script and can be used for interactive exploration. Note that on Mac OS X this currently blocks the main python thread due to Swing/Cocoa/GUI API limitations.
```python
jmad.open_jmad_gui()
```
