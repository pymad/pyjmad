__version__ = "0.0.4"

__cmmnbuild_deps__ = [
    "accmodel-jmad-core",
    "accmodel-jmad-models-lhc",
    "accmodel-jmad-models-gsi",
    "accmodel-jmad-models-lhctransfer",
    "accsoft-steering-commons",
    "accmodel-jmad-gui",
    "slf4j-log4j12",
    "slf4j-api",
    "log4j"
]

__gradle_deps__ = [
    "jmad:jmad-core:0.1.3+",
    {'repository': 'maven { url "https://dl.bintray.com/jmad/jmad-repo" }',
     'groupId': 'jmad', 'artifactId': 'jmad-modelpack-service', 'version': '0.2.1+'},
    "org.slf4j:slf4j-api:+",
    "org.slf4j:slf4j-log4j12:+",
    "log4j:log4j:1.2.17",
]

# When running setuptools without required dependencies installed
# we need to be able to access __version__, so print a warning but
# continue
try:
    from .pyjmad import *
    from . import element, matching
except:
    import logging

    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.exception("required dependencies are not installed")
