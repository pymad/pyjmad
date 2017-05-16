# -*- coding: utf-8 -*-

class GlobalConstraint(object):
    def __init__(self, Q1=None, Q2=None, DQ1=None, DQ2=None):
        self.Q1 = Q1
        self.Q2 = Q2
        self.DQ1 = DQ1
        self.DQ2 = DQ2

    @property
    def constraints(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def __repr__(self):
        return repr(self.constraints)


class LocalConstraint(object):
    def __init__(self, at,
                 ALFX=None, ALFY=None,
                 BETX=None, BETY=None,
                 DDPX=None, DDPY=None,
                 DDX=None, DDY=None,
                 DPX=None, DPY=None,
                 DX=None, DY=None,
                 MUX=None, MUY=None,
                 PX=None, PY=None,
                 X=None, Y=None):
        self.element = at
        self.ALFX = ALFX
        self.ALFY = ALFY
        self.BETX = BETX
        self.BETY = BETY
        self.DDPX = DDPX
        self.DDPY = DDPY
        self.DDX = DDX
        self.DDY = DDY
        self.DPX = DPX
        self.DPY = DPY
        self.DX = DX
        self.DY = DY
        self.MUX = MUX
        self.MUY = MUY
        self.PX = PX
        self.PY = PY
        self.X = X
        self.Y = Y

    @property
    def constraints(self):
        return {k: v for k, v in self.__dict__.items() if k != 'element' and v is not None}

    def __repr__(self):
        return self.element + ' -> ' + repr(self.constraints)


class Vary(object):
    def __init__(self, strength, lower_bound=None, upper_bound=None, step=None):
        self.strength = strength
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.step = step

    def __repr__(self):
        return 'Vary(' + self.strength + ' -> ' + str(self.lower_bound) + ':' + str(self.upper_bound) + ':' + str(
            self.step) + ')'
