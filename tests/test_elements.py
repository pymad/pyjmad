# -*- coding: utf-8 -*-

import pyjmad
import numpy as np

def test_slice_elements():
    jmad = pyjmad.JMad()
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    assert len(lhcModel.elements['BPM.10L1.B1':'BPM.10R1.B1']) > 300
    assert len(lhcModel.elements['BPM.10L5.B1':'BPM.10R5.B1']) > 300

def test_set_quatrupole():
    jmad = pyjmad.JMad()
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    res_before = lhcModel.twiss(variables=('S', 'BETX', 'BETY'))

    quad = lhcModel.elements['MQ.10L3.B1']
    assert abs(quad.k1-0.00874) < 0.00001
    quad.k1 = 0.01
    res_after = lhcModel.twiss(variables=('S', 'BETX', 'BETY'))
    # assert beta-beating
    assert np.sqrt(np.mean((res_before.data.BETX/res_after.data.BETX-1)**2)) > 0.3
    assert np.sqrt(np.mean((res_before.data.BETY/res_after.data.BETY-1)**2)) < 0.05
