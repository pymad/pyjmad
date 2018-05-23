import itertools
import logging

from .pyjmad import org
from .util import *


class JMadModelPackService(object):
    def __init__(self, applicationContext):
        self._javaService = applicationContext['jmadModelPackageService']
        self._javaRepositoryManager = applicationContext['packageRepositoryManager']
        self._modelpacks = {}
        self._reload()

    def _reload(self):
        logging.info('Fetching available ModelPacks from ' + str(self.repositories))
        self._modelpacks = {}
        modelpacks = self._javaService.availablePackages().collectList().block()
        for name, variants in itertools.groupby(modelpacks, lambda m: m.modelPackage().name()):
            self._modelpacks[name] = ModelPackType(self, name, variants)

    @property
    def repositories(self):
        return self._javaRepositoryManager.enabledRepositories().collectList().block()

    def __getitem__(self, modelpack):
        return self._modelpacks[modelpack]

    def __setitem__(self, k, v):
        raise NotImplementedError('Setting of ModelPacks is not supported')

    def __delitem__(self, k):
        raise NotImplementedError('Deletion of ModelPacks is not supported')

    def __iter__(self):
        return self._modelpacks.__iter__()

    def __len__(self):
        return self._modelpacks.__len__()

    def __repr__(self):
        return 'ModelPackService [ \n' \
               ' - Enabled Repos: ' + str(self.repositories) + '\n' + \
               ' - Available ModelPacks: ' + str(self._modelpacks) + '\n' + \
               ']'

    def __str__(self):
        return self.__repr__()

    def _ipython_key_completions_(self):
        return list(self._modelpacks.keys())


class ModelPackType(object):
    def __init__(self, service, name, variants):
        self._name = name
        self._all_variants = {}
        Branch = org.jmad.modelpack.service.gitlab.domain.Branch
        Release = org.jmad.modelpack.service.gitlab.domain.Release
        Tag = org.jmad.modelpack.service.gitlab.domain.Tag
        InternalPackageVariant = org.jmad.modelpack.service.internal.domain.InternalPackageVariant
        for modpack in variants:
            if type(modpack.variant()) is Release:
                variant = 'releases'
            elif type(modpack.variant()) is Branch:
                variant = 'branches'
            elif type(modpack.variant()) is Tag:
                variant = 'tags'
            elif type(modpack.variant()) is InternalPackageVariant:
                variant = 'internal_models'
            else:
                variant = 'others'
            if variant == 'internal_models':
                self._all_variants[variant] = modpack
            else:
                self._all_variants.setdefault(variant, {})[modpack.variant().name()] = ModelPack(service, modpack)

    def __dir__(self):
        return ['name'] + list(self._all_variants.keys())

    def __getattr__(self, name):
        if name == 'name':
            return self._name
        elif name in self._all_variants:
            return self._all_variants[name]
        else:
            raise AttributeError


class ModelPack(object):
    def __init__(self, service, javaModelPackVariant):
        self._javaModelPackVariant = javaModelPackVariant
        self._service = service

    @property
    def id(self):
        return str(self._javaModelPackVariant.fullName())

    @property
    def models(self):
        from .pyjmad import ModelDefinition
        modeldefs = self._service._javaService.modelDefinitionsFrom(self._javaModelPackVariant).collectList().block()
        return HtmlDict({mdef.getName(): ModelDefinition(mdef) for mdef in modeldefs})
