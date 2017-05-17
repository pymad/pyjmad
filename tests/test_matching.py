# -*- coding: utf-8 -*-

import pyjmad
import numpy as np
from pyjmad.matching import *

jmad = pyjmad.JMad()

def test_match_global_tune():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    summary = lhcModel.twiss(variables=()).summary
    assert abs(summary['Q1']-62.31) < 0.005
    assert abs(summary['Q2']-60.32) < 0.005

    mr = lhcModel.match(GlobalConstraint(Q1=62.28, Q2=60.31),
                        Vary('KQT4.L3', step=0.000001),
                        Vary('KQT4.R3', step=0.000001))
    assert mr.final_penalty < 1e-5
    summary = lhcModel.twiss(variables=()).summary
    assert abs(summary['Q1']-62.28) < 0.005
    assert abs(summary['Q2']-60.31) < 0.005

def test_match_local_beta():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    res = lhcModel.twiss(variables=('S', 'BETX', 'BETY'))
    assert abs(res.data.BETX['IP1']-0.40) < 0.005
    assert abs(res.data.BETY['IP1']-0.40) < 0.005

    mr = lhcModel.match(LocalConstraint('IP1', BETX=0.45, BETY=0.45),
                        Vary('KQX.L1', step=0.000001),
                        Vary('KQX.R1', step=0.000001))
    assert mr.final_penalty < 0.005
    res = lhcModel.twiss(variables=('S', 'BETX', 'BETY'))
    assert abs(res.data.BETX['IP1']-0.45) < 0.005
    assert abs(res.data.BETY['IP1']-0.45) < 0.005
