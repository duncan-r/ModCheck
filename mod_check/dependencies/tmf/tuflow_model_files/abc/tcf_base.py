from .cf import ControlFile
from tmf.tuflow_model_files.utils.context import Context
from tmf.tuflow_model_files.dataclasses.event import EventDatabase
from tmf.tuflow_model_files.db.mat import MatDatabase
from tmf.tuflow_model_files.db.bc_dbase import BCDatabase
from tmf.tuflow_model_files.dataclasses.scope import Scope
from tmf.tuflow_model_files.dataclasses.file import TuflowPath

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class TCFBase(ControlFile):

    def tgc(self, context: Context = None) -> 'ControlFile':
        """Returns the TGC ControlFile object.

        If more than one TGC control file object exists, a Context object must be provided to resolve to the correct
        TGC.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct TGC control file object. Not required unless more than one
            TGC control file object exists.

        Returns
        -------
        ControlFile
            The TGC control file object.
        """
        return self._find_control_file('geometry control file', context)

    def tbc(self, context: Context = None) -> 'ControlFile':
        """Returns the TBC ControlFile object.

        If more than one TBC control file object exists, a Context object must be provided to resolve to the correct
        TBC.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct TBC control file object. Not required unless more than one
            TBC control file object exists.

        Returns
        -------
        ControlFile
            The TBC control file object.
        """
        return self._find_control_file('bc control file', context)

    def ecf(self, context: Context = None) -> 'ControlFile':
        """Returns the ECF ControlFile object.

        If more than one ECF control file object exists, a Context object must be provided to resolve to the correct
        ECF.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct ECF control file object. Not required unless more than one
            ECF control file object exists.

        Returns
        -------
        ControlFile
            The ECF control file object.
        """
        return self._find_control_file('estry control file', context)

    def tscf(self, context: Context = None) -> 'ControlFile':
        """Returns the TSCF ControlFile object.

        If more than one TSCF control file object exists, a Context object must be provided to resolve to the correct
        TSCF.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct TSCF control file object. Not required unless more than one
            TSCF control file object exists.

        Returns
        -------
        ControlFile
            The TSCF control file object.
        """
        return self._find_control_file('swmm control file', context)

    def bc_dbase(self, context: Context = None) -> BCDatabase:
        """Returns the BcDatabase Database object.

        If more than one BcDatabase object exists, a Context object must be provided to resolve to the correct
        BcDatabase.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct BCDatabase object. Not required unless more than one
            BCDatabase file object exists.

        Returns
        -------
        BCDatabase
            The BCDatabase object.
        """
        return self._find_control_file('bc database', context)

    def mat_file(self, context: Context = None) -> MatDatabase:
        """Returns the Materials Database object.

        If more than one Materials Database object exists, a Context object must be provided to resolve to the correct
        Materials Database.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct MatDatabase object. Not required unless more than one
            MatDatabase file object exists.

        Returns
        -------
        MatDatabase
            The MatDatabase object.
        """
        return self._find_control_file('read materials? file', context, regex=True)

    def tef(self, context: Context = None) -> 'ControlFile':
        """Returns the TEF ControlFile object.

        If more than one TEF control file object exists, a Context object must be provided to resolve to the correct
        TEF.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct TEF control file object. Not required unless more than one
            TEF control file object exists.

        Returns
        -------
        ControlFile
            The TEF control file object.
        """
        return self._find_control_file('event file', context)

    def event_database(self, context: Context = None) -> EventDatabase:
        """Returns the EventDatabase object.

        If more than one EventDatabase object exists, a Context object must be provided to resolve to the correct
        EventDatabase.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct EventDatabase object. Not required unless more than one
            EventDatabase file object exists.

        Returns
        -------
        EventDatabase
            The EventDatabase object.
        """
        tef = self._find_control_file('event file', context)
        if tef is None:
            return EventDatabase()
        return self._event_cf_to_db(tef)

    def output_folder_1d(self, context: Context = None) -> TuflowPath:
        """Returns the 1D output folder.

        Returns the last instance of the command. If more than one Output Folder exists and some exist in
        IF logic blocks an exception will be raised.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct 1D output directory. Not required unless more than one
            1D output directory exists.

        Returns
        -------
        TuflowPath
            The 1D output directory.
        """
        output_folders = []
        inputs = self.find_input(command='output folder', recursive=True)
        for inp in inputs:
            if '1D' in inp.command.upper():
                output_folders.append(inp)
            if hasattr(self, 'scope') and Scope('1D Domain') in inp.scope():
                output_folders.append(inp)
            if hasattr(self, 'bs') and Scope('1D Domain') in inp.bs.scope():
                output_folders.append(inp)
            if '<EstryControlFile>' in repr(inp.parent) or '<ECFContext>' in repr(inp.parent):
                output_folders.append(inp)

        if len(output_folders) > 1 and hasattr(self, 'scope') and [x for x in output_folders if Scope('GLOBAL') not in x.scope()]:
            if not context:
                raise ValueError('{0} requires context to resolve'.format('Output Folder'))
            else:  # context has been provided, can try and resolve
                for i, inp in enumerate(output_folders[:]):
                    if context.in_context_by_scope(inp._scope):
                        output_folders[i] = inp

        if output_folders:
            return TuflowPath(output_folders[-1].expanded_value)
        else:
            return self.path.parent

    def output_folder_2d(self, context: Context = None) -> TuflowPath:
        """Returns the 2D output folder.

        Returns the last instance of the command. If more than one Output Folder exists and some exist in
        IF logic blocks an exception will be raised.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct 2D output directory. Not required unless more than one
            1D output directory exists.

        Returns
        -------
        TuflowPath
            The 2D output directory.
        """
        output_folders = []
        inputs = self.find_input(command='output folder', recursive=True)
        for inp in inputs:
            if '1D' in inp.command.upper():
                continue
            if hasattr(self, 'scope') and Scope('1D Domain') in inp.scope():
                continue
            if hasattr(self, 'bs') and Scope('1D Domain') in inp.bs.scope():
                continue
            if '<EstryControlFile>' in repr(inp.parent) or '<ECFContext>' in repr(inp.parent):
                continue
            if '<TuflowSWMMControl>' in repr(inp.parent) or '<TSCFContext>' in repr(inp.parent):
                continue
            output_folders.append(inp)

        if len(output_folders) > 1 and hasattr(self, 'scope') and [x for x in output_folders if Scope('GLOBAL') not in x.scope()]:
            if not context:
                raise ValueError('{0} requires context to resolve'.format('Output Folder'))
            else:  # context has been provided, can try and resolve
                for i, inp in enumerate(output_folders[:]):
                    if context.in_context_by_scope(inp._scope):
                        output_folders[i] = inp

        if output_folders:
            return TuflowPath(output_folders[-1].expanded_value)

    def log_folder_path(self, context: Context = None) -> TuflowPath:
        """Returns the 2D output folder.

        Returns the last instance of the command. If more than one Log Folder exists and some exist in
        IF logic blocks an exception will be raised.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct 2D output directory. Not required unless more than one
            1D output directory exists.

        Returns
        -------
        TuflowPath
            The log folder.
        """
        log_folders = []
        inputs = self.find_input(command='log folder', recursive=True)
        if len(inputs) > 1 and hasattr(self, 'scope') and [x for x in inputs if Scope('GLOBAL') not in x.scope()]:
            if not context:
                logger.error('{0} requires context to resolve'.format('Log Folder'))
                raise ValueError('{0} requires context to resolve'.format('Log Folder'))
            else:  # context has been provided, can try and resolve
                for i, inp in enumerate(inputs):
                    if context.in_context_by_scope(inp._scope):
                        log_folders.append(inp)
        elif inputs:
            log_folders.append(inputs[-1])

        if log_folders:
            return TuflowPath(log_folders[-1].expanded_value)
