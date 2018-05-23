# -*- coding: utf-8 -*-
from collections import MutableMapping

from .pyjmad import cern, java


class Element(object):
    def __init__(self, jmadElement):
        self._jmadElement = jmadElement

    @property
    def name(self):
        return self._jmadElement.getName()

    @property
    def type(self):
        return str(self._jmadElement.getMadxElementType())

    @property
    def length(self):
        return self._jmadElement.getLength()

    @length.setter
    def length(self, len):
        self._jmadElement.getLength(float(len))

    @property
    def position(self):
        return self._jmadElement.getPosition().getValue()

    @position.setter
    def position(self, position):
        self._jmadElement.setPosition(float(position))

    @property
    def attributes(self):
        return Attributes(self._jmadElement)

    def __str__(self):
        return self.name + ' (' + self.type + ')'

    def __repr__(self):
        return self.name + ' (' + self.type + ': ' + str(self.attributes) + ')'


def _specific_element(name, attributes):
    attr_dict = {}
    for attr in attributes:
        java_name = ''.join([s.capitalize() for s in attr.split('_')])
        p = property(lambda self, java_name=java_name: self._jmadElement.__getattribute__('get' + java_name)()) \
            .setter(
            lambda self, v, java_name=java_name: self._jmadElement.__getattribute__('set' + java_name)(float(v)))
        attr_dict[attr] = p
    return type(name, (Element,), attr_dict)


BeamBeam = _specific_element('BeamBeam',
                             ['charge', 'direction', 'displacement_x', 'displacement_y', 'shape', 'sig_x', 'sig_y',
                              'width'])
Bend = _specific_element('Bend',
                         ['angle', 'e1', 'e2', 'fint', 'fint_x', 'h1', 'h2', 'h_gap', 'k0', 'k1', 'k2', 'k3', 'tilt'])
Corrector = _specific_element('Corrector', ['h_kick', 'tilt', 'v_kick'])
Marker = _specific_element('Marker', [])
Monitor = _specific_element('Monitor', [])
Quadrupole = _specific_element('Quadrupole', ['k1', 'tilt'])
Sextupole = _specific_element('Sextupole', ['k2', 'tilt'])
Octupole = _specific_element('Octupole', ['k3', 'tilt'])


def from_jmad(jmadElement):
    _jmadElementMap = {
        'BeamBeam': BeamBeam,
        'Bend': Bend,
        'Corrector': Corrector,
        'Marker': Marker,
        'Monitor': Monitor,
        'Octupole': Octupole,
        'Quadrupole': Quadrupole,
        'Sextupole': Sextupole,
        'UnknownElement': Element
    }
    return _jmadElementMap[jmadElement.getClass().getSimpleName()](jmadElement)


class Attributes(MutableMapping):
    def __init__(self, jmadElement):
        self._jmadElement = jmadElement

    def __getitem__(self, k):
        return self._jmadElement.getAttribute(k).doubleValue()

    def __setitem__(self, k, v):
        return self._jmadElement.setAttribute(k, java.lang.Double(float(v)))

    def __delitem__(self, k):
        raise NotImplementedError("Deletion of Attributes is not supported")

    def __iter__(self):
        for s in self._jmadElement.getAttributeNames():
            yield s

    def __len__(self):
        return self._jmadElement.getAttributeNames().size()

    def _ipython_key_completions_(self):
        return [s for s in self._jmadElement.getAttributeNames()]

    def __repr__(self):
        return '{' + ', '.join([k + '=' + str(v) for k, v in self.items()]) + '}'

    def __str__(self):
        return self.__repr__()
