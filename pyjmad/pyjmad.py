# -*- coding: utf-8 -*-
from collections import namedtuple

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
        return [self.model_definition(m) for m in self._jmadModelDefinitionManager.getAllModelDefinitions()]

    def model_definition(self, model):
        if type(model) is str:
            return ModelDefinition(self._jmadModelDefinitionManager.getModelDefinition(model))
        elif type(model) is ModelDefinition:
            return model
        return ModelDefinition(model)

    def create_model(self, model):
        return Model(self._jmadService.createModel(self.model_definition(model)._jmadModelDefinition))

    def open_jmad_gui(self):
        prefs = JMadGuiPreferencesImpl()
        prefs.setExitOnClose(False)
        prefs.setCleanupOnClose(False)
        prefs.setMainFrame(False)
        jmad_gui = JMadGui(self._jmadService, prefs, None)
        jmad_gui.show()
        return jmad_gui


class Model(object):
    def __init__(self, jmadModel):
        self._jmadModel = jmadModel
        self.definition = ModelDefinition(jmadModel.getModelDefinition())

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
            return jmadRange.getRangeDefinition().getSequenceDefinition().getName()

    @sequence.setter
    def sequence(self, sequence):
        jmadSequence = self.definition._jmad_sequenceDefinition(sequence)
        if jmadSequence is None:
            raise ValueError('Invalid sequence: ' + sequence)
        self._jmadModel.setActiveRangeDefinition(jmadSequence.getDefaultRangeDefinition())

    def __str__(self):
        return self.name + " - " + str(self.optic) + " - " + str(self.sequence)

    def __repr__(self):
        return "Model(" + self.name + ", optic=" + str(self.optic) + ", sequence=" + str(self.sequence) + ")"


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
        return [o.getName() for o in self._jmadModelDefinition.getSequenceDefinitions()]

    def _jmad_opticDefinition(self, optic):
        if isinstance(optic, str):
            return self._jmadModelDefinition.getOpticsDefinition(optic)
        else:
            return optic

    def _jmad_sequenceDefinition(self, sequence):
        if isinstance(sequence, str):
            return self._jmadModelDefinition.getSequenceDefinition(sequence)
        else:
            return sequence

    def __str__(self):
        return self.name

    def __repr__(self):
        return "ModelDefinition(" + self.name + ", optics=" + str(self.optics) + ", sequences=" + str(
            self.sequences) + ")"


class _JMadVariableRepository(object):
    def __init__(self, variable_class):
        self._jmadClass = variable_class
        self._jmadVars = {v.getName(): v for v in variable_class.values()}

    def _jmad_variable(self, var):
        if isinstance(var, str):
            return self._jmadVars[var.lower()]
        else:
            return var

    def __getattr__(self, name):
        if name == '_jmadVars':
            return self._jmadVars
        if name.lower() in self._jmadVars:
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
