__version__ = "0.0.7"

__cmmnbuild_deps__ = [
    "jmad-core-pro",
    "jmad-gui-pro",
    "slf4j-log4j12",
    "slf4j-api",
    "log4j"
]

__gradle_deps__ = [
    "jmad:jmad-core:0.2.2+",
    'jmad:jmad-modelpack-service:0.2.6+',
    'jmad:jmad-modelpack-fx:0.2.4+',
    "jmad:jmad-gui:0.3.22+",
    "org.slf4j:slf4j-api:+",
    "org.slf4j:slf4j-log4j12:+",
    "log4j:log4j:1.2.17",
    # for jdataviewer
    {'repository': 'ivy { url "http://jmad.web.cern.ch/jmad/static/ws/lib/"\n' +
                   'layout "pattern", { artifact "[artifact].[ext]" } \n' +
                   'metadataSources { artifact() } }',
     'groupId': 'cern', 'artifactId': 'jdataviewer', 'version': '1.4.7'},
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
