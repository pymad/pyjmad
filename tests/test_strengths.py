# -*- coding: utf-8 -*-

import pyjmad
import numpy as np

jmad = pyjmad.JMad()


def test_strength_list():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    assert len(lhcModel.strengths) > 500
    assert 'on_x1' in lhcModel.strengths
    assert 'on_x5' in lhcModel.strengths
    assert 'dQx.b1' in lhcModel.strengths
    assert 'dQy.b1' in lhcModel.strengths
    assert 'dQx.b2' in lhcModel.strengths
    assert 'dQy.b2' in lhcModel.strengths


def fit_crossing_angle_ip5(lhcModel):
    res = lhcModel.twiss(variables=('S', 'X', 'Y'))
    ip5_xing_x = np.polyfit(res.data.S['BPMSW.1L5.B1':'BPMSW.1R5.B1'],
                            res.data.X['BPMSW.1L5.B1':'BPMSW.1R5.B1'], 1)[0]*1e6
    ip5_xing_y = np.polyfit(res.data.S['BPMSW.1L5.B1':'BPMSW.1R5.B1'],
                            res.data.Y['BPMSW.1L5.B1':'BPMSW.1R5.B1'], 1)[0]*1e6
    return (ip5_xing_x, ip5_xing_y)


def test_strength_manipulation_crossing_angle():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    ip5_xing_x, ip5_xing_y = fit_crossing_angle_ip5(lhcModel)
    assert abs(ip5_xing_x) < 0.01
    assert abs(ip5_xing_y) < 0.01

    crossing_angle = 145 # urad
    lhcModel.strengths['on_x5'] = crossing_angle
    ip5_xing_x, ip5_xing_y = fit_crossing_angle_ip5(lhcModel)
    assert abs(ip5_xing_x-crossing_angle) < 0.01
    assert abs(ip5_xing_y) < 0.01
    
    lhcModel.strengths['on_x5'] = -crossing_angle
    ip5_xing_x, ip5_xing_y = fit_crossing_angle_ip5(lhcModel)
    assert abs(ip5_xing_x+crossing_angle) < 0.01
    assert abs(ip5_xing_y) < 0.01

def test_strength_manipulation_tune():
    lhcModel = jmad.create_model('LHC 2017')
    lhcModel.sequence = 'lhcb1'
    lhcModel.optic = 'R2017a_A40C40A10mL300_CTPPS2'
    lhcModel.range = 'ALL'
    summary = lhcModel.twiss(variables=()).summary
    assert abs(summary['Q1']-62.31) < 0.005
    assert abs(summary['Q2']-60.32) < 0.005

    lhcModel.strengths['dQx.b1'] = -0.03
    lhcModel.strengths['dQy.b1'] = -0.01
    summary = lhcModel.twiss(variables=()).summary
    assert abs(summary['Q1']-62.28) < 0.005
    assert abs(summary['Q2']-60.31) < 0.005
	