__version__ = "0.0.2"

__cmmnbuild_deps__ = [
    "accmodel-jmad-core",
    "accmodel-jmad-models-lhc",
    "accmodel-jmad-models-lhctransfer",
    "accsoft-steering-commons",
    "accmodel-jmad-gui",
    "slf4j-log4j12",
    "slf4j-api",
    "log4j"
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
    log.warning("required dependencies are not installed")