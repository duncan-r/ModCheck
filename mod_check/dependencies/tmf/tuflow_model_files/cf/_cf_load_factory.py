
from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()

class ControlFileLoadMixin:
    """Mixin to handle any load hooks and behaviour.
    
    Handles instance creation requirements on ControlFileBuildState creation (TCF,
    TGC, TBC, etc). Should only receive args/kwargs in the constructor to allow
    MRO to resolve properly.
    
    Behaviour that is required prior to fully initialising and loading the
    ControlFileBuildState objects goes here. 
    """
    
    def __init__(self, *args, **kwargs):
        """Configure the default logging level. 

        Level will be set to WARNING if no log_level kwarg is found or it is set to None. No
        logging filehandler is created by default, but it can be configured by passing a
        valid filepath to the log_to_file kwarg.

        Parameters
        ----------
        kwargs : dict
            options for configuring the logging level and filehandler
            ::

                {
                    log_level: Union['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'WARNING',
                    log_to_file: PathLike = None
                }
        """
        log_level = kwargs.pop('log_level', None)
        log_to_file = kwargs.pop('log_to_file', None)

        # If one of the logging kwargs has been provided call the setup function
        if log_level is not None or log_to_file is not None:
            log_level = 'WARNING' if log_level is None else log_level
            tmf_logging.set_logging_level(log_level, log_to_file)

        super().__init__(*args, **kwargs)
