# -*- coding: utf-8 -*-
from collections import namedtuple, MutableMapping, Mapping, OrderedDict

import numpy as np
import pandas as pd
import re, site, logging

import cmmnbuild_dep_manager

mgr = cmmnbuild_dep_manager.Manager('pyjmad')

jpype = mgr.start_jpype_jvm()

cern = jpype.JPackage('cern')
org = jpype.JPackage('org')
java = jpype.JPackage('java')
com = jpype.JPackage('com')

org.apache.log4j.BasicConfigurator.configure()
org.apache.log4j.Logger.getRootLogger().setLevel(org.apache.log4j.Level.INFO)
from .spring import SpringApplicationContext

from .modelpack import JMadModelPackService
from .util import *

JMadServiceFactory = cern.accsoft.steering.jmad.service.JMadServiceFactory
Doubles = com.google.common.primitives.Doubles
JMadGui = cern.accsoft.steering.jmad.gui.JMad
JMadGuiPreferencesImpl = cern.accsoft.steering.jmad.gui.manage.impl.JMadGuiPreferencesImpl
TfsResultRequestImpl = cern.accsoft.steering.jmad.domain.result.tfs.TfsResultRequestImpl
Iterables = com.google.common.collect.Iterables


class JMad(object):
    def __init__(self):
        try:
            try:
                self._springContext = SpringApplicationContext(
                    cern.accsoft.steering.jmad.gui.config.JMadGuiStandaloneConfiguration)
            except:
                logging.info("Could not instantiate GUI context, trying headless context")
                self._springContext = SpringApplicationContext(
                    org.jmad.modelpack.service.conf.JMadModelPackageServiceStandaloneConfiguration)

            self._jmadService = self._springContext['jmadService']
            self.model_packs = JMadModelPackService(self._springContext)
        except:
            logging.exception("JMad Model Pack Service not available, falling back")
            self._jmadService = JMadServiceFactory.createJMadService()
        self._jmadModelDefinitionManager = self._jmadService.getModelDefinitionManager()
        self._jmadModelManager = self._jmadService.getModelManager()

    @property
    def model_definitions(self):
        return HtmlDict({m.getName(): ModelDefinition(m) for m in
                         self._jmadModelDefinitionManager.getAllModelDefinitions()})

    def create_model(self, model):
        if type(model) is str:
            model = self.model_definitions[model]
        elif type(model) is not ModelDefinition:
            model = ModelDefinition(model)
        return Model(self._jmadService.createModel(model._jmadModelDefinition))

    def open_jmad_gui(self):
        gui = self._springContext['jmadGui']
        gui.getJmadGuiPreferences().setCleanupOnClose(False)
        gui.getJmadGuiPreferences().setExitOnClose(False)
        gui.getJmadGuiPreferences().setMainFrame(False)
        jpype.setupGuiEnvironment(lambda: gui.show())


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

    @property
    def beam(self):
        return Beam(self._jmadModel.getActiveRange().getRangeDefinition().getSequenceDefinition().getBeam())

    def reset(self):
        self._jmadModel.reset()

    def match(self, *args):
        MatchResultRequestImpl = cern.accsoft.steering.jmad.domain.result.match.MatchResultRequestImpl
        MadxVaryParameterImpl = cern.accsoft.steering.jmad.domain.result.match.input.MadxVaryParameterImpl
        MatchConstraintGlobal = cern.accsoft.steering.jmad.domain.result.match.input.MatchConstraintGlobal
        MatchConstraintLocal = cern.accsoft.steering.jmad.domain.result.match.input.MatchConstraintLocal
        MadxParameterImpl = cern.accsoft.steering.jmad.domain.knob.MadxParameterImpl
        MadxRange = cern.accsoft.steering.jmad.domain.machine.MadxRange
        from .matching import LocalConstraint, GlobalConstraint, Vary
        jmadRequest = MatchResultRequestImpl()
        for arg in args:
            if isinstance(arg, LocalConstraint):
                jmadConstraint = MatchConstraintLocal(MadxRange(arg.element))
                for c, v in arg.constraints.items():
                    jmadConstraint.__getattribute__('set' + (c.capitalize()))(java.lang.Double(float(v)))
                jmadRequest.addMatchConstraint(jmadConstraint)
            elif isinstance(arg, GlobalConstraint):
                jmadConstraint = MatchConstraintGlobal()
                for c, v in arg.constraints.items():
                    jmadConstraint.__getattribute__('set' + (c.capitalize()))(java.lang.Double(float(v)))
                jmadRequest.addMatchConstraint(jmadConstraint)
            elif isinstance(arg, Vary):
                jmadVary = MadxVaryParameterImpl(MadxParameterImpl(arg.strength))
                if arg.lower_bound is not None:
                    jmadVary.setLower(java.lang.Double(float(arg.lower_bound)))
                if arg.upper_bound is not None:
                    jmadVary.setUpper(java.lang.Double(float(arg.upper_bound)))
                if arg.step is not None:
                    jmadVary.setStep(java.lang.Double(float(arg.step)))
                jmadRequest.addMadxVaryParameter(jmadVary)
            else:
                raise ValueError('Expecting LocalConstraint, GlobalConstraint, Vary - but got ' + str(type(arg)))

        return MatchResult(self._jmadModel.match(jmadRequest))

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
            html += '<li>' + r + '</li>'
        html += '</ul></td>'
        html += '<td style="vertical-align:top"><ul>'
        for s in self.sequences:
            html += '<li>' + s._repr_html_() + '</li>'
        html += '</ul></td>'
        html += '</tr></tbody></table>'
        return html


class Beam(object):
    def __init__(self, jmadBeam):
        self._jmadBeam = jmadBeam

    @property
    def bunch_current(self):
        return _unbox_double(self._jmadBeam.getBunchCurrent())

    @property
    def bunch_length(self):
        return _unbox_double(self._jmadBeam.getBunchLength())

    @property
    def bunch_number(self):
        return _unbox_integer(self._jmadBeam.getBunchNumber())

    @property
    def is_bunched(self):
        return _unbox_boolean(self._jmadBeam.getBunched())

    @property
    def charge(self):
        return _unbox_double(self._jmadBeam.getCharge())

    @property
    def direction(self):
        v = self._jmadBeam.getDirection()
        if str(v) == 'PLUS':
            return +1
        elif str(v) == 'MINUS':
            return -1
        else:
            return None

    @property
    def energy(self):
        return _unbox_double(self._jmadBeam.getEnergy())

    @property
    def gamma(self):
        return _unbox_double(self._jmadBeam.getGamma())

    @property
    def emittance_pysical_h(self):
        return _unbox_double(self._jmadBeam.getHorizontalEmittance())

    @property
    def emittance_pysical_v(self):
        return _unbox_double(self._jmadBeam.getVerticalEmittance())

    @property
    def mass(self):
        return _unbox_double(self._jmadBeam.getMass())

    @property
    def momentum(self):
        return _unbox_double(self._jmadBeam.getMomentum())

    @property
    def emittance_normalized_h(self):
        return _unbox_double(self._jmadBeam.getNormalisedHorizontalEmittance())

    @property
    def emittance_normalized_v(self):
        return _unbox_double(self._jmadBeam.getNormalisedVerticalEmittance())

    @property
    def particle(self):
        v = self._jmadBeam.getParticle()
        if v is None:
            return None
        else:
            return str(v)

    @property
    def radiate(self):
        return _unbox_boolean(self._jmadBeam.getRadiate())

    @property
    def relative_energy_spread(self):
        return _unbox_double(self._jmadBeam.getRelativeEnergySpread())

    def __str__(self):
        return self.particle + ' beam @ ' + str(self.energy) + ' GeV'

    def __repr__(self):
        s = self.__str__() + '\n'
        for f in dir(self):
            if not f.startswith('_') and self.__getattribute__(f) is not None:
                s += '   ' + f + ' = ' + str(self.__getattribute__(f)) + '\n'
        return s


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
            html += '<li>' + r + '</li>'
        html += '</ul>'
        return html


class MatchResult(object):
    def __init__(self, jmadMatchResult):
        self._jmadMatchResult = jmadMatchResult

    @property
    def final_penalty(self):
        return self._jmadMatchResult.getFinalPenalty()

    @property
    def vary_results(self):
        return {p.getName(): p.getFinalValue() for p in self._jmadMatchResult.getVaryParameterResults()}

    @property
    def constraint_results(self):
        return {re.sub('=\{.*?\}', '', str(p.getConstraint())): p.getFinalValue()
                for p in self._jmadMatchResult.getConstraintParameterResults()}

    def __str__(self):
        return 'Match Result ->> final penalty: ' + str(self.final_penalty)

    def __repr__(self):
        return 'Match Result ->> final penalty: ' + str(self.final_penalty) + '\n' + \
               '   Vary Results: ' + repr(self.vary_results) + '\n' + \
               '   Constraint Results: ' + repr(self.constraint_results) + '\n'


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
    def __init__(self, elements):
        from .element import from_jmad
        if type(elements) is cern.accsoft.steering.jmad.domain.machine.Range:
            self._elementList = [from_jmad(e) for e in elements.getElements()]
        elif type(elements) is list:
            self._elementList = elements
        else:
            raise ValueError('Expecting either a list of elements or a JMad Range')
        self._nameDict = {}
        for i, e in enumerate(self._elementList):
            self._nameDict.setdefault(e.name, []).append(i)

    def __getitem__(self, k):
        if type(k) is int:
            return self._elementList[k]
        if type(k) is slice:
            if type(k.start) in (int, type(None)) and type(k.stop) in (int, type(None)) \
                    and type(k.step) in (int, type(None)):
                return self._elementList[k]
            else:
                first_name = k.start if k.start is not None else self._elementList[0]
                last_name = k.stop if k.stop is not None else self._elementList[-1]
                first_idx = self._nameDict[first_name]
                if type(first_idx) is list:
                    first_idx = first_idx[0]
                last_idx = self._nameDict[last_name]
                if type(last_idx) is list:
                    last_idx = last_idx[-1]
                if first_idx > last_idx:
                    elements = self._elementList[first_idx:] + self._elementList[:(last_idx + 1)]
                else:
                    elements = self._elementList[first_idx:(last_idx + 1)]
                return Elements(elements)
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

    def values(self):
        for e in self._elementList:
            yield e

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
        for n, e in self.items():
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
MadxGlobalVariable = _JMadVariableRepository(cern.accsoft.steering.jmad.domain.var.enums.MadxGlobalVariable)

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
    names = np.array(Iterables.toArray(tfs_result.getStringData('NAME'), java.lang.String().getClass())[:])
    result_df = pd.DataFrame(index=names)
    for var in tfs_result.getKeys():
        if var == 'NAME':
            continue
        vt = str(tfs_result.getVarType(var))
        if vt == 'STRING':
            col = np.array(Iterables.toArray(tfs_result.getStringData(var), java.lang.String().getClass())[:])
        elif vt == 'DOUBLE':
            col = np.array(Doubles.toArray(tfs_result.getDoubleData(var))[:])
        else:
            col = None
        result_df[var] = col
    return TfsResult(summary=summ_dict, data=result_df)


def _unbox_double(v):
    if v is None:
        return None
    else:
        return v.doubleValue()


def _unbox_integer(v):
    if v is None:
        return None
    else:
        return v.intValue()


def _unbox_boolean(v):
    if v is None:
        return None
    else:
        return True if v.booleanValue() == 1 else False
