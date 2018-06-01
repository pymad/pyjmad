import itertools
import logging

from .pyjmad import org, java
from .util import *


def _repo_to_uri(javaRepo):
    if str(javaRepo.connectorId()) == 'internal-classpath':
        return 'jmad:internal'
    elif str(javaRepo.connectorId()) == 'gitlab-group-api-v4':
        return javaRepo.baseUrl() + '/' + javaRepo.repoName()
    else:
        raise ValueError('unknown repository type: ' + str(javaRepo))


def _repo_from_uri(uri):
    JMadModelPackageRepository = org.jmad.modelpack.domain.JMadModelPackageRepository
    InternalRepository = org.jmad.modelpack.connect.embedded.domain.InternalRepository
    schema = uri.split(':')[0]
    if schema == 'jmad':
        if uri == 'jmad:internal':
            return InternalRepository.INTERNAL
        else:
            raise ValueError('invalid "jmad:" uri "{0}" - expected = jmad:internal'.format(uri))
    elif schema == 'http' or schema == 'https':
        base_url, group_name = uri.rsplit('/', 1)
        return JMadModelPackageRepository(base_url, group_name, 'gitlab-group-api-v4')
    elif '+' in schema:
        connector, repo_uri = uri.split('+', 1)
        base_url, group_name = repo_uri.rsplit('/', 1)
        return JMadModelPackageRepository(base_url, group_name, connector)
    else:
        raise ValueError('invalid repository URI: ' + uri)


jmad_default_repositories = {}
try:
    _JMadModelRepositories = org.jmad.modelpack.domain.JMadModelRepositories
    for method in _JMadModelRepositories.__javaclass__.getDeclaredMethods():
        if method.getModifiers() & java.lang.reflect.Modifier.PUBLIC:
            repo = method.getName()
            jmad_default_repositories[repo] = _repo_to_uri(getattr(_JMadModelRepositories, repo)())
except Exception:
    logging.exception("can not fetch default models from jmad-modelpack-service")

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
        for modpack in variants:
            if str(modpack.variant().type()) == 'RELEASE':
                variant = 'releases'
            elif str(modpack.variant().type()) == 'BRANCH':
                variant = 'branches'
            elif str(modpack.variant().type()) == 'TAG':
                variant = 'tags'
            elif type(modpack.variant()) is org.jmad.modelpack.connect.embedded.domain.InternalPackageVariant:
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
