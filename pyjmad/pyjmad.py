# -*- coding: utf-8 -*-
from collections import namedtuple, MutableMapping, Mapping, OrderedDict

import cmmnbuild_dep_manager
import numpy as np
import pandas as pd

mgr = cmmnbuild_dep_manager.Manager('pyjmad')
jpype = mgr.start_jpype_jvm()

cern = jpype.JPackage('cern')
org = jpype.JPackage('org')
java = jpype.JPackage('java')
com = jpype.JPackage('com')

JMadServiceFactory = cern.accsoft.steering.jmad.service.JMadServiceFactory
Doubles = com.google.common.primitives.Doubles
JMadGui = cern.accsoft.steering.jmad.gui.JMad
JMadGuiPreferencesImpl = cern.accsoft.steering.jmad.gui.manage.impl.JMadGuiPreferencesImpl
TfsResultRequestImpl = cern.accsoft.steering.jmad.domain.result.tfs.TfsResultRequestImpl
Iterables = com.google.common.collect.Iterables


class JMad(object):
    def __init__(self):
        self._jmadService = JMadServiceFactory.createJMadService()
        self._jmadModelDefinitionManager = self._jmadService.getModelDefinitionManager()
        self._jmadModelManager = self._jmadService.getModelManager()

    @property
    def model_definitions(self):
        class HtmlDict(dict):
            def _repr_html_(self):
                return ''.join([s._repr_html_() for s in self.values()])
        return HtmlDict({m.getName(): ModelDefinition(m) for m in
                self._jmadModelDefinitionManager.getAllModelDefinitions()})

    def create_model(self, model):
        if type(model) is str:
            model = self.model_definitions[model]
        elif type(model) is not ModelDefinition:
            model = ModelDefinition(model)
        return Model(self._jmadService.createModel(model._jmadModelDefinition))

    def open_jmad_gui(self):
        prefs = JMadGuiPreferencesImpl()
        prefs.setExitOnClose(False)
        prefs.setCleanupOnClose(False)
        prefs.setMainFrame(False)
        jpype.setupGuiEnvironment(lambda: JMadGui(self._jmadService, prefs, None).show())




class Model(object):
    def __init__(self, jmadModel):
        self._jmadModel = jmadModel
        self.definition = ModelDefinition(jmadModel.getModelDefinition())
        if not jmadModel.isInitialized():
            jmadModel.init()

    def twiss(self, variables, element_filter=None):
        if isinstance(variables, str):
            variables = [variables, ]
        request = TfsResultRequestImpl.createDefaultRequest()
        for var in variables:
            request.addVariable(MadxTwissVariable._jmad_variable(var))
        if element_filter is not None:
            request.addElementFilter(element_filter)
        tfs_result = self._jmadModel.twiss(request)
        return _jmad_TfsResult_to_pandas(tfs_result)

    @property
    def name(self):
        return self.definition.name

    @property
    def optic(self):
        jmadOptic = self._jmadModel.getActiveOpticsDefinition()
        if jmadOptic is None:
            return None
        else:
            return jmadOptic.getName()

    @optic.setter
    def optic(self, optic):
        jmadOptic = self.definition._jmad_opticDefinition(optic)
        if jmadOptic is None:
            raise ValueError('Invalid Optic: ' + jmadOptic)
        self._jmadModel.setActiveOpticsDefinition(jmadOptic)

    @property
    def sequence(self):
        jmadRange = self._jmadModel.getActiveRange()
        if jmadRange is None:
            return None
        else:
            return SequenceDefinition(jmadRange.getRangeDefinition().getSequenceDefinition())

    @sequence.setter
    def sequence(self, sequence):
        jmadSequence = self.definition._jmad_sequenceDefinition(sequence)
        if jmadSequence is None:
            raise ValueError('Invalid sequence: ' + sequence)
        self._jmadModel.setActiveRangeDefinition(jmadSequence.getDefaultRangeDefinition())
    
    @property
    def range(self):
        return self._jmadModel.getActiveRange().getName()

    @range.setter
    def range(self, range):
        return self._jmadModel.setActiveRangeDefinition(self.sequence._jmad_rangeDefinition(range))


    @property
    def strengths(self):
        return Strengths(self._jmadModel.getStrengthsAndVars())

    @property
    def elements(self):
        return Elements(self._jmadModel.getActiveRange())

    def __str__(self):
        return self.name + ' - ' + str(self.optic) + ' - ' + str(self.sequence) + ' - ' + str(self.range)

    def __repr__(self):
        return self.__str__()

class ModelDefinition(object):
    def __init__(self, jmadModelDefinition):
        self._jmadModelDefinition = jmadModelDefinition

    @property
    def name(self):
        return self._jmadModelDefinition.getName()

    @property
    def optics(self):
        return [o.getName() for o in self._jmadModelDefinition.getOpticsDefinitions()]

    @property
    def sequences(self):
        return [SequenceDefinition(o) for o in self._jmadModelDefinition.getSequenceDefinitions()]

    def _jmad_opticDefinition(self, optic):
        if isinstance(optic, str):
            return self._jmadModelDefinition.getOpticsDefinition(optic)
        else:
            return optic

    def _jmad_sequenceDefinition(self, sequence):
        if isinstance(sequence, str):
            return self._jmadModelDefinition.getSequenceDefinition(sequence)
        elif isinstance(sequence, SequenceDefinition):
            return sequence._jmadSequenceDefinition
        else:
            return sequence

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name + ' (optics=' + str(self.optics) + ', sequences=' + str(self.sequences) + ')'

    def _repr_html_(self):
        html = '<table><thead>'
        html += '<tr><th colspan="2"><em>' + self.name + '</em></th></tr>'
        html += '<tr><th>Optics</th><th>Sequences</th></tr>'
        html += '</thead><tbody><tr>'
        html += '<td style="vertical-align:top"><ul>'
        for r in self.optics:
            html += '<li>'+r+'</li>'
        html += '</ul></td>'
        html += '<td style="vertical-align:top"><ul>'
        for s in self.sequences:
            html += '<li>'+s._repr_html_()+'</li>'
        html += '</ul></td>'
        html += '</tr></tbody></table>'
        return html
        


class SequenceDefinition(object):
    def __init__(self, jmadSequenceDefinition):
        self._jmadSequenceDefinition = jmadSequenceDefinition

    def _jmad_rangeDefinition(self, range):
        if isinstance(range, str):
            return self._jmadSequenceDefinition.getRangeDefinition(range)
        else:
            return range

    @property
    def name(self):
        return self._jmadSequenceDefinition.getName()

    @property
    def ranges(self):
        return [str(r) for r in self._jmadSequenceDefinition.getRangeDefinitions()]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name + str(self.ranges)

    def _repr_html_(self):
        html = '<em>' + self.name + '</em> with ranges:'
        html += '<ul style="margin-top:0">'
        for r in self.ranges:
            html += '<li>'+r+'</li>'
        html += '</ul>'
        return html


class Strengths(MutableMapping):
    def __init__(self, jmadStrengthVarSet):
        self._jmadStrengthVarSet = jmadStrengthVarSet

    def _jmadStrength(self, k):
        jmadStrength = self._jmadStrengthVarSet.getStrength(k)
        if jmadStrength is None:
            raise KeyError('Invalid Strength Name: ' + k)
        return jmadStrength

    def __getitem__(self, k):
        return self._jmadStrength(k).getValue()

    def __setitem__(self, k, v):
        return self._jmadStrength(k).setValue(float(v))

    def __delitem__(self, k):
        raise NotImplementedError('Deletion of Strengths is not supported')

    def __iter__(self):
        for s in self._jmadStrengthVarSet.getStrengths():
            yield s.getName()

    def __len__(self):
        return self._jmadStrengthVarSet.getStrengths().size()

    def _ipython_key_completions_(self):
        return [s.getName() for s in self._jmadStrengthVarSet.getStrengths()]

    def __repr__(self):
        s = 'Strengths(\n'
        for k, v in self.items():
            s += '   ' + k + ': ' + str(v) + '\n'
        s += ')'
        return s

    def __str__(self):
        return self.__repr__()

    def _repr_html_(self):
        s = '<table>'
        for k, v in self.items():
            s += '<tr><td><strong>' + k + '</strong></td><td>' + str(v) + '</td>'
        s += '</table>'
        return s

class Elements(Mapping):
    def __init__(self, jmadRange):
        from .element import from_jmad
        self._jmadRange = jmadRange
        self._elementList = [from_jmad(e) for e in jmadRange.getElements()]
        self._nameDict = {}
        for i,e in enumerate(self._elementList):
            self._nameDict.setdefault(e.name, []).append(i)

    def __getitem__(self, k):
        if type(k) is int:
            return self._elementList[k]
        matchingElements = [self._elementList[i] for i in self._nameDict[k]]
        if len(matchingElements) == 1:
            return matchingElements[0]
        else:
            return matchingElements

    def __iter__(self):
        return list(self._nameDict.keys())

    def items(self):
        for e in self._elementList:
            yield (e.name, e)

    def __len__(self):
        return len(self._elementList)

    def _ipython_key_completions_(self):
        return list(self._nameDict.keys())

    def __repr__(self):
        s = 'Elements(\n'
        for k, v in self.items():
            s += '   ' + k + ' :: ' + str(v) + '\n'
        s += ')'
        return s

    def __str__(self):
        return self.__repr__()

    def _repr_html_(self):
        html = '<table><thead>'
        html += '<tr><th>Element</th><th>Type</th><th>S</th><th>L</th></tr>'
        html += '</thead><tbody><tr>'
        for n,e in self.items():
            html += '<tr><td><strong>' + n + '</strong></td><td>' + e.type + '</td>'
            html += '<td>' + str(e.position) + '</td><td>' + str(e.length) + '</td>'
        html += '</table>'
        return html


class _JMadVariableRepository(object):
    def __init__(self, variable_class):
        self._jmadClass = variable_class
        self._jmadVars = {v.getName().upper(): v for v in variable_class.values()}

    def _jmad_variable(self, var):
        if isinstance(var, str):
            return self._jmadVars[var.upper()]
        else:
            return var

    def __getattr__(self, name):
        if name == '_jmadVars':
            return self._jmadVars
        if name.upper() in self._jmadVars:
            return name.upper()

    def __dir__(self):
        return self._jmadVars.keys()


MadxTwissVariable = _JMadVariableRepository(cern.accsoft.steering.jmad.domain.var.enums.MadxTwissVariable)

TfsResult = namedtuple('TfsResult', ['summary', 'data'])


def _jmad_TfsResult_to_pandas(tfs_result):
    summ = tfs_result.getSummary()
    summ_dict = {}
    for var in summ.getKeys():
        vt = str(summ.getVarType(var))
        if vt == 'STRING':
            val = summ.getStringValue(var)
        elif vt == 'DOUBLE':
            val = summ.getDoubleValue(var).doubleValue()
        else:
            val = None
        summ_dict[var] = val
    result_df = pd.DataFrame()
    for var in tfs_result.getKeys():
        vt = str(tfs_result.getVarType(var))
        if vt == 'STRING':
            col = np.array(Iterables.toArray(tfs_result.getStringData(var), java.lang.String().getClass())[:])
        elif vt == 'DOUBLE':
            col = np.array(Doubles.toArray(tfs_result.getDoubleData(var))[:])
        else:
            col = None
        result_df[var] = col
    return TfsResult(summary=summ_dict, data=result_df)
