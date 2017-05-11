# -*- coding: utf-8 -*-

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
        return self._jmadElement.getLength(float(len))

    @property
    def position(self):
        return self._jmadElement.getPosition()

    @position.setter
    def position(self, position):
        return self._jmadElement.setPosition(position)

    @property
    def attributes(self):
        return {a:self._jmadElement.getAttribute(a).doubleValue() for a in self._jmadElement.getAttributeNames()}
        
    def __str__(self):
        return str(self.__class__.__name__)+'('+', '.join(['%s=%s'%(k,str(v)) for k,v in self.attributes.items()])+')'

    def __repr__(self):
        return self.__str__()

def _specific_element(name, attributes):
    attr_dict = {}
    for attr in attributes:
        java_name = ''.join([s.capitalize() for s in attr.split('_')])
        p = property(lambda self: self._jmadElement.__getattribute__('get'+java_name)())
        try:
            p = p.setter(lambda self, v: self._jmadElement.__getattribute__('set'+java_name)(float(v))) 
        except:
            pass
        attr_dict[attr] = p
    return type(name, (Element,), attr_dict)

BeamBeam = _specific_element('BeamBeam', ['charge', 'direction', 'displacement_x', 'displacement_y', 'shape', 'sig_x', 'sig_y', 'width'])
Bend = _specific_element('Bend', ['angle', 'e1', 'e2', 'fint', 'fint_x', 'h1', 'h2', 'h_gap', 'k0', 'k1', 'k2', 'k3', 'tilt'])
Corrector = _specific_element('Corrector', ['h_kick', 'tilt', 'v_kick'])
Marker = _specific_element('Marker', [])
Monitor = _specific_element('Monitor', [])
Quadrupole = _specific_element('Quadrupole', ['k1', 'tilt'])
Sextupole = _specific_element('Sextupole', ['k2', 'tilt'])
Octupole = _specific_element('Octupole', ['k3', 'tilt'])


def from_jmad(jmadElement):
    from pyjmad import cern
    _jmadElementMap = {
        cern.accsoft.steering.jmad.domain.elem.impl.BeamBeam: BeamBeam,
        cern.accsoft.steering.jmad.domain.elem.impl.Bend: Bend,
        cern.accsoft.steering.jmad.domain.elem.impl.Corrector: Corrector,
        cern.accsoft.steering.jmad.domain.elem.impl.Marker: Marker,
        cern.accsoft.steering.jmad.domain.elem.impl.Monitor: Monitor,
        cern.accsoft.steering.jmad.domain.elem.impl.Octupole: Octupole,
        cern.accsoft.steering.jmad.domain.elem.impl.Quadrupole: Quadrupole,
        cern.accsoft.steering.jmad.domain.elem.impl.Sextupole: Sextupole,
        cern.accsoft.steering.jmad.domain.elem.impl.UnknownElement: Element
    }
    return _jmadElementMap[jmadElement.getClass()](jmadElement)
