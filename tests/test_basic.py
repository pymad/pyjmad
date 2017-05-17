# -*- coding: utf-8 -*-

import pyjmad
import numpy as np

jmad = pyjmad.JMad()

def test_model_definition_loading():
    assert len(jmad.model_definitions) > 10
    assert jmad.model_definitions['LHC 2017'] is not None


def test_model_creation():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    assert lhcModel.sequence.name == 'lhcb1'
    assert len(lhcModel.sequence.ranges) > 1
    assert lhcModel.optic == 'R2017a_A40C40A10mL300_CTPPS2'
    assert lhcModel.range == 'ALL'

 
def test_twiss():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    res = lhcModel.twiss(variables=('S', 'BETX', 'BETY', 'X', 'Y'))
    assert abs(res.summary['Q1']-62.31) < 0.005
    assert abs(res.summary['Q2']-60.32) < 0.005
    assert abs(res.data.BETX['IP1']-0.4) < 0.005
    assert abs(res.data.BETY['IP1']-0.4) < 0.005
    assert abs(res.data.BETX['IP5']-0.4) < 0.005
    assert abs(res.data.BETY['IP5']-0.4) < 0.005
    assert np.all(np.abs(res.data.X) < 0.01)
    assert np.all(np.abs(res.data.Y) < 0.01)
