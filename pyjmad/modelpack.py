import itertools
import logging

from .pyjmad import org, java
from .util import *


def _repo_to_uri(javaRepo):
    GitlabModelPackageRepository = org.jmad.modelpack.service.gitlab.GitlabModelPackageRepository
    InternalRepository = org.jmad.modelpack.service.internal.domain.InternalRepository
    if type(javaRepo) is InternalRepository:
        return 'jmad:internal'
    elif type(javaRepo) is GitlabModelPackageRepository:
        return javaRepo.baseUrl() + '/' + javaRepo.groupName()
    else:
        raise ValueError('unknown repository type: ' + str(javaRepo))


def _repo_from_uri(uri):
    GitlabModelPackageRepository = org.jmad.modelpack.service.gitlab.GitlabModelPackageRepository
    InternalRepository = org.jmad.modelpack.service.internal.domain.InternalRepository
    schema = uri.split(':')[0]
    if schema == 'jmad':
        if uri == 'jmad:internal':
            return InternalRepository.INTERNAL
        else:
            raise ValueError('invalid "jmad:" uri "{0}" - expected = jmad:internal'.format(uri))
    elif schema == 'http' or schema == 'https':
        base_url, group_name = uri.rsplit('/', 1)
        return GitlabModelPackageRepository(base_url, group_name)
    else:
        raise ValueError('invalid repository URI: ' + uri)


jmad_default_repositories = {}
for method in org.jmad.modelpack.JMadModelRepositories.__javaclass__.getDeclaredMethods():
    if method.getModifiers() & java.lang.reflect.Modifier.PUBLIC:
        repo = method.getName()
        jmad_default_repositories[repo] = _repo_to_uri(getattr(org.jmad.modelpack.JMadModelRepositories, repo)())


class JMadModelPackService(object):
    def __init__(self, applicationContext):
        self._javaService = applicationContext['jmadModelPackageService']
        self._javaRepositoryManager = applicationContext['packageRepositoryManager']
        self._modelpacks = {}
        self._reload()

    def _reload(self):
        def modelpack_name(pkg):
            return str(pkg.modelPackage().name())

        logging.info('Fetching available ModelPacks from ' + str(self.repositories))
        self._modelpacks = {}
        modelpacks = list(self._javaService.availablePackages().collectList().block())
        modelpacks.sort(key=modelpack_name)
        for name, variants in itertools.groupby(modelpacks, modelpack_name):
            self._modelpacks[name] = ModelPackType(self, name, variants)

    @property
    def repositories(self):
        return [_repo_to_uri(r) for r in self._javaRepositoryManager.enabledRepositories().collectList().block()]

    def add_repository(self, repo_uri):
        self._javaRepositoryManager.enable(_repo_from_uri(repo_uri))
        self._reload()

    def remove_repository(self, repo_uri):
        self._javaRepositoryManager.disable(_repo_from_uri(repo_uri))
        self._reload()

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
               ' -> Enabled Repos: \n    - ' + '\n    - '.join(self.repositories) + '\n' + \
               ' -> Available ModelPacks: \n    - ' + '\n    - '.join(self._modelpacks.keys()) + '\n' + \
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
