[![Build Status](https://travis-ci.org/pymad/pyjmad.svg?branch=master)](https://travis-ci.org/pymad/pyjmad)

# PyJMad
Yet another python wrapper around JMad using JPype. PyJMad aims for compatibility with other CERN Java-Python bridges,
using cmmnbuild-dep-manager (and access to CERN resources) for easy side-by-side installation. A particular focus lies
on interactive usage and integration with IPython/Jupyter.

### Set up:
```python
import pyjmad
jmad = pyjmad.JMad()
```

### Explore model packs
JMad model packs are now stored as Git repos, and accessed through [jmad-modelpack-service] - the "previous" style
of loading models from the Java class path is still supported through the special "INTERNAL" model pack. At the moment,
repositories must be hosted on a GitLab service, as they are accessed through the GitLab REST API.
```python
jmad.model_packs
```
Example output:
```text
ModelPackService [ 
 -> Enabled Repos: 
    - https://gitlab.cern.ch/jmad-modelpacks-cern
    - jmad:internal
 -> Available ModelPacks: 
    - INTERNAL
    - jmad-modelpack-lhc
    - jmad-modelpack-sps
    - jmad-modelpack-leir
    - jmad-modelpack-ps
]
```
The models are accessed through indexing model_packs. Jupyter/IPython autocompletion is supported at all stages.
```python
model_def = jmad.model_packs['jmad-modelpack-lhc'].branches['master'].models['LHC 2017']
```
#### Add a custom model pack repository:
```python
jmad.model_packs.add_repository('https://gitlab.cern.ch/jmad-repo-michi-testing')
```

[jmad-modelpack-service]: https://github.com/jmad/jmad-modelpack-service
### Setup a Model:
```python
md = jmad.model_packs['jmad-modelpack-lhc'].branches['master'].models['LHC 2017']
jmad.create_model(md)
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
