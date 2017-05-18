#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from setuptools.command.install import install as _install

import pyjmad
import os, site

class install(_install):
    def run(self):
        print('registering cmmnbuild_dep_manager')
        if not hasattr(site, 'getusersitepackages'):
            print('running in VirtualEnv, monkey-patching site module')
            site.getusersitepackages = lamda: '/home/travis/virtualenv/python3.5.2/lib/python3.5/site-packages/'
            print(os.environ['VIRTUAL_ENV'])
            print(os.environ['PYTHONPATH'])
        import cmmnbuild_dep_manager
        mgr = cmmnbuild_dep_manager.Manager()
        mgr.install('pyjmad')
        print('registered pylsa with cmmnbuild_dep_manager')
        _install.run(self)

setuptools.setup(
    name='pyjmad',
    version=pyjmad.__version__,
    description='A Python wrapping of JMad',
    author='Michi Hostettler',
    author_email='michi.hostettler@cern.ch',
    url='https://github.com/michi42/pyjmad',
    packages=['pyjmad'],
    install_requires=['JPype1>=0.6.1',
                      'cmmnbuild-dep-manager>=2.1.0' ],
    cmdclass={ 'install': install },
)