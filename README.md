First try for a python wrapper around JMad. Needs cmmnbuild-dep-manager (and access to CERN resources) to run.

Example:
```python
import pyjmad
jmad = pyjmad.JMad()
jmad.model_definitions
lhcModel = jmad.create_model('LHC 2017')
lhcModel.sequence = 'lhcb1'
lhcModel.optic = 'R2017a_A11mC11mA10mL10m'
twiss = lhcModel.twiss(variables=('S','BETX','BETY','X','Y'))

print(twiss.summary)
print(twiss.data)

plt.figure()
plt.plot(res.data.S, res.data.BETX)
plt.plot(res.data.S, res.data.BETY)
plt.show()
```