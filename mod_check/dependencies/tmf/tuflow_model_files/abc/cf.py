import re
import typing
from typing import TYPE_CHECKING, Union
from uuid import UUID

from ..dataclasses.event import Event, EventDatabase
from ..dataclasses.scope import Scope
from ..dataclasses.types import SearchTagLike
from ..utils.commands import EventCommand
from ..utils.context import Context
from ..dataclasses.file import TuflowPath
from ..dataclasses.inputs import Inputs

if TYPE_CHECKING:
    from ..dataclasses.inputs import Inputs
    from ..abc.input import Input
    from ..abc.db import Database
    from ..cf._cf_build_state import ControlFileBuildState


class ControlFile:
    """Abstract base class for all control file classes."""

    def __setattr__(self, key, value, private: bool = False, gate: int = 0):
        """Override this method to prevent users from changing property values.
        This is required as control file inputs are assigned as properties to the control file class, and
        we don't want users thinking that modifying these will change the control file inputs. Methods such as
        "update_value", "append_input", "insert_input", "remove_input" - should be used instead.

        This only prevents users from changing properties of the control file class if the property has already
        been set by the load method and added to the "_priv_prop" dictionary. If the property needs to actually be
        updated, just pass in a secret 'gate' value that is not equal to zero.
        """
        if hasattr(self, '_priv_prop') and key in self._priv_prop and not gate:
            raise AttributeError(f'Cannot set attribute {key} on {self.__class__.__name__}')
        super().__setattr__(key, value)
        if private and hasattr(self, '_priv_prop'):
            self._priv_prop[key] = True

    @property
    def tcf(self):
        #: ControlFile: The parent TCF control file object
        if not self.parent:
            return self
        else:
            tcf = self.parent
            while tcf.parent:
                tcf = tcf.parent
            return tcf

    def commands(self) -> list[str]:
        """Returns a list of all the commands in the current control file.

        .. note::
            ES Note - Will probably remove in a future release, not sure what it offers
            over just looking at the list of inputs.

        Returns
        -------
        list[str]
            A list of all the commands in the current control file.
        """
        return [input.command for input in self.inputs if input]

    def input(self, uuid: Union[str, UUID]) -> 'Input':
        """Returns the input with the given UUID. UUIDs remain constant across build and run state conversions.

        Parameters
        ----------
        uuid : Union[str, UUID]
            The UUID of the input to return either as a string or UUID object.

        Returns
        -------
        Input
            The input with the given UUID.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        for inp in self.inputs._inputs:
            if inp.uuid == uuid:
                return inp
            if 'ControlFileInput' in repr(inp):
                loaded_value = self.input_to_loaded_value(inp)
                if loaded_value is None:
                    continue
                if isinstance(loaded_value, Inputs):
                    for inp_ in loaded_value:
                        inp2 = inp_.input(uuid)
                        if inp2:
                            return inp2
                else:
                    inp_ = loaded_value.input(uuid)
                    if inp_:
                        return inp_

    def find_input(self, filter: str = None, command: str = None,
                   value: str = None, recursive: bool = True, regex: bool = False, regex_flags: int = 0,
                   tags: SearchTagLike = (), callback: typing.Callable = None, comments: bool = False) -> 'Inputs':
        """Find a particular input(s) by using a filter (:code:`filter=`). The filter can be for the entire input,
        or localised to the command or value side of the input (:code:`command=` and :code:`value=` respectively).
        The filter can be a string or a regular expression depending on the :code:`regex` parameter with regex flags
        passed in using the :code:`regex_flags` parameter.

        The parameters are not mutually exclusive, so if a filter can be provided for the command and the
        value parameters. By default (when not using regex), the filter is not case sensitive.

        ::


            # Find all inputs that contain the string 'read gis' on the command side
            inps = control_file.find_input(command='read gis')

            # Find all inputs that reference a shape file
            inps = control_file.find_input(value='.shp')

            # Find all inputs that reference a shape file or mif file using regular expressions
            inps = control_file.find_input(value=r'\.shp|\.mif', regex=True, regex_flags=re.IGNORECASE)

        More complex filtering can be done by using the :code:`tags` parameter. Tags can be used to filter the input
        by its property e.g. :code:`files` or :code:`multi_layer`. A tag can be passed in as a single value or as a
        tuple with the property name and the value to compare against e.g. :code:`('multi_layer', True)` will find
        inputs that contain multiple layers (i.e. GIS inputs that have multiple layers). If a value is not provided, it
        is assumed to be :code:`True` so :code:`('multi_layer')` is equivalent to :code:`('multi_layer', True)`.
        Multiple tags can be provided to assess multiple properties. If multiple tags are provided, the format must
        be a list of tuples e.g. :code:`[('multi_layer'), ('has_vector', True)]`. A callback can be provided as the
        tag value to filter the input by a custom function. The callback should take one argument which will be
        the property value associated with the tag and return a :code:`bool`.
        If the callback returns :code:`True`, the input will be included in the return list.

        ::


            # Find all inputs that are missing files (one or more referenced files do not exist)
            inps = control_file.find_input(tags='missing_files')

            # Find all GIS inputs that are referencing point layers
            inps = control_file.find_input(tags=('geoms', lambda x: ogr.wkbPoint in x))

        A callback can be passed outside the :code:`tag` parameter if the assessment doesn't relate to a property.
        The callback should take one argument which is :code:`Input` and return a boolean.
        If the callback returns :code:`True`, the input will be included in the
        return list.

        ::


            # Find all GIS inputs that contain a given scope
            inps = control_file.find_input(callback=lambda x: Scope('Scenario', 'DEV01') in x.scope())

        If :code:`comments` is set to :code:`True`, the search will also search through comments in the input, and inputs
        that are only comments. This can be useful for finding commands that have been commented out and re-adding
        them with :meth:`uncomment`. It can also be useful if you want to add keywords to the comments for a given
        input to make it easier to find.

        Parameters
        ----------
        filter : str, optional
            A string or regular expression to filter the input by.
            This will search through the entire input string (not comments).
        command : str, optional
            A string or regular expression to filter the input by.
            This will search through the command side of the input (i.e. LHS).
        value : str, optional
            A string or regular expression to filter the input by.
            This will search through the value side of the input (i.e. RHS).
        recursive : bool, optional
            If set to True, will also search through any child control files.
        regex : bool, optional
            If set to True, the filter, command, and value parameters will be treated as regular expressions.
        regex_flags : int, optional
            The regular expression flags to use when filtering by regular expressions.
        tags : SearchTagLike, optional
            A list of tags to filter the input by. This can be a string (single tag)
            or list/tuple of strings that will be used to filter the input by tag keys which
            correspond to properties contained in the input. Tags themselves can be tuples with a
            value to compare against (key, value) otherwise the value will be assumed as True.
        callback : typing.Callable, optional
            A function that will be called with the input as an argument.
        comments : bool, optional
            If set to True, will also search through the comments of the input, including lines that only contain
            comments.

        Returns
        -------
        Inputs
            A list of inputs that match the filter.
        """
        from ..dataclasses.inputs import Inputs

        if comments:
            inputs_ = self.inputs._inputs
        else:
            inputs_ = self.inputs

        inputs = Inputs(show_comment_lines=comments)
        for input_ in inputs_:
            if input_.is_match(filter, command, value, regex, regex_flags, tags, callback, comments):
                inputs.append(input_)
            if recursive and 'ControlFileInput' in repr(input_):
                loaded_value = self.input_to_loaded_value(input_)
                if loaded_value is None:
                    continue
                if isinstance(loaded_value, Inputs):
                    for inp in loaded_value:
                        inputs.extend(inp.find_input(filter, command, value, recursive, regex, regex_flags, tags,
                                                     callback, comments))
                else:
                    inputs.extend(loaded_value.find_input(filter, command, value, recursive, regex, regex_flags, tags,
                                                          callback, comments))

        return inputs

    def gis_inputs(self, recursive: bool = True) -> 'Inputs':
        """Returns all GIS inputs in the control file. If recursive is set to True, will also search through any
        child control files.

        Parameters
        ----------
        recursive : bool, optional
            If set to True, will also search through any child control files.

        Returns
        -------
        Inputs
            A list of GIS inputs in the control file.
        """
        from ..dataclasses.inputs import Inputs
        inputs = Inputs()
        for input_ in self.inputs:
            if input_.raw_command_obj().is_read_gis() or input_.raw_command_obj().is_read_projection():
                inputs.append(input_)
            loaded_value = self.input_to_loaded_value(input_)
            if loaded_value and recursive:
                if isinstance(loaded_value, Inputs):
                    for inp in loaded_value:
                        inputs.extend(inp.gis_inputs(recursive))
                else:
                    inputs.extend(loaded_value.gis_inputs(recursive))

        return inputs

    def grid_inputs(self, recursive: bool = True) -> 'Inputs':
        """Returns all grid inputs in the control file. If recursive is set to True, will also search through any
        child control files.


        Parameters
        ----------
        recursive : bool, optional
            If set to True, will also search through any child control files.

        Returns
        -------
        Inputs
            A list of Grid inputs in the control file.
        """
        from ..dataclasses.inputs import Inputs, ComplexInputs
        inputs = Inputs()
        for input_ in self.inputs:
            if input_.raw_command_obj().is_read_grid():
                inputs.append(input_)
            loaded_value = self.input_to_loaded_value(input_)
            if loaded_value and recursive:
                if isinstance(loaded_value, Inputs):
                    for inp in loaded_value:
                        inputs.extend(inp.grid_inputs(recursive))
                else:
                    inputs.extend(loaded_value.grid_inputs(recursive))

        return inputs

    def tin_inputs(self, recursive: bool = True) -> 'Inputs':
        """Returns all TIN inputs in the control file. If recursive is set to True, will also search through any
        child control files.

        Parameters
        ----------
        recursive : bool, optional
            If set to True, will also search through any child control files.

        Returns
        -------
        Inputs
            A list of TIN inputs in the control file.
        """
        from ..dataclasses.inputs import Inputs, ComplexInputs
        inputs = Inputs()
        for input_ in self.inputs:
            if input_.raw_command_obj().is_read_tin():
                inputs.append(input_)
            loaded_value = self.input_to_loaded_value(input_)
            if loaded_value and recursive:
                if isinstance(loaded_value, Inputs):
                    for inp in loaded_value:
                        inputs.extend(inp.tin_inputs(recursive))
                else:
                    inputs.extend(loaded_value.tin_inputs(recursive))

        return inputs

    def get_inputs(self, recursive: bool = True) -> 'Inputs':
        """Returns all inputs in the control file. If recursive is set to True, will also search through any
        child control files.

        Parameters
        ----------
        recursive : bool, optional
            If set to True, will also search through any child control files.

        Returns
        -------
        Inputs
            A list of all inputs in the control file.
        """
        from ..dataclasses.inputs import Inputs, ComplexInputs
        inputs = Inputs()
        for input_ in self.inputs:
            if input_ not in inputs:
                inputs.append(input_)
            loaded_value = self.input_to_loaded_value(input_)
            if loaded_value and recursive:
                if isinstance(loaded_value, Inputs):
                    for inp in loaded_value:
                        inputs.extend(inp.get_inputs(recursive))
                else:
                    inputs.extend(loaded_value.get_inputs(recursive))

        return inputs

    def input_to_loaded_value(self, inp: 'Input') -> any:
        """Returns the loaded class object for a given input.

        e.g. Given the input specifying the geometry control file, this method will return the TGC class object
        loaded from that given input.

        Currently only applicable for ControlFile objects and Database objects, otherwise will return None.

        .. note::

            ES Note - Will most likely remove this class in the future and simply attach the loaded class object to the
            input as a property.

        Parameters
        ----------
        inp : Input
            The input to get the loaded class object for.

        Returns
        -------
        typing.Any
            The loaded class object for the given input. Either a ControlFile or Database object.
        """
        return self._input_to_loaded_value.get(inp)

    def _input_as_attr(self, inp: 'Input') -> None:
        if not inp:
            return
        attr = re.sub(r'\s+', '_', inp.command.lower())
        attr = re.sub(r'\(.*\)', '', attr)
        attr = attr.rstrip('_')
        if hasattr(self, attr) and not isinstance(getattr(self, attr), Inputs):
            value = Inputs()
            value.append(getattr(self, attr))
            if inp.raw_command_obj().is_control_file() or inp.raw_command_obj().is_read_database():
                value.extend(self.input_to_loaded_value(inp))
            else:
                value.append(inp.value)
            self.__setattr__(attr, value, True, 1)
        elif not hasattr(self, attr):
            if inp.raw_command_obj().is_control_file() or inp.raw_command_obj().is_read_database():
                loaded_value = self.input_to_loaded_value(inp)
                if hasattr(loaded_value, '__len__') and len(loaded_value) == 1:
                    loaded_value = loaded_value[0]
                self.__setattr__(attr, loaded_value, True, 1)
            else:
                self.__setattr__(attr, inp.value, True, 1)
        else:
            if inp.raw_command_obj().is_control_file() or inp.raw_command_obj().is_read_database():
                getattr(self, attr).extend(self.input_to_loaded_value(inp))
            else:
                getattr(self, attr).append(inp.value)

    def _replace_attr(self, inp: 'Input', old_value: any) -> None:
        if not inp:
            return
        attr = re.sub(r'\s+', '_', inp.command.lower())
        attr = re.sub(r'\(.*\)', '', attr)
        attr = attr.rstrip('_')
        has_attr = hasattr(self, attr)
        if has_attr and isinstance(getattr(self, attr), Inputs):
            values = getattr(self, attr)
            if old_value in values:
                i = values.index(old_value)
                if inp.raw_command_obj().is_control_file() or inp.raw_command_obj().is_read_database():
                    values[i] = self.input_to_loaded_value(inp)
                else:
                    values[i] = inp.value
        else:
            if inp.raw_command_obj().is_control_file() or inp.raw_command_obj().is_read_database():
                self.__setattr__(attr, self.input_to_loaded_value(inp), True, 1)
            else:
                self.__setattr__(attr, inp.value, True, 1)

    def _remove_attr(self, inp: 'Input', old_value: any) -> None:
        if not inp:
            return
        attr = re.sub(r'\s+', '_', inp.command.lower())
        attr = re.sub(r'\(.*\)', '', attr)
        attr = attr.rstrip('_')
        has_attr = hasattr(self, attr)
        if has_attr and isinstance(getattr(self, attr), Inputs):
            values = getattr(self, attr)
            if old_value in values:
                values.remove(old_value)
                if len(values) == 1:
                    self.__setattr__(attr, values[0], True, 1)
        elif has_attr:
            delattr(self, attr)

    def _event_cf_to_db(self, event_cf: 'ControlFileBuildState') -> EventDatabase:
        events = EventDatabase()
        if event_cf is None:
            return events

        # inputs are only collected for commands so empty scope blocks will be missing, but for events we need
        # to consider all events, even blank ones (rare, but I've seen "Define Event" blocks with nothing in them)
        events_ = []
        if event_cf.path.exists():
            with event_cf.path.open() as f:
                for line in f:
                    a = line.split('!')[0].split('#')[0].strip()
                    if '==' in a and 'Define Event' in a:
                        events_.append(a.split('==')[1].strip())

        for event in events_:
            input_ = event_cf.find_input(tags=('_scope', lambda x: Scope('EVENT VARIABLE', event) in x))
            if input_:
                input_ = input_[0]
                cmd = EventCommand(input_.raw_command_obj().original_text, input_.raw_command_obj().settings)
                if not cmd.is_event_source():
                    continue
                var, val = cmd.get_event_source()
                name_ = [x for x in input_._scope if x == Scope('EVENT VARIABLE')][0].name
                if isinstance(name_, list):
                    name_ = name_[0]
            else:  # blank event
                name_ = event
                var = ''
                val = ''
            events[name_] = Event(name_, var, val)

        return events

    def _find_control_file(self, command: str, context: Context = None, regex: bool = False) -> Union['ControlFile', 'Database']:
        if command.lower() != 'read file' and 'TuflowControlFile' not in repr(self) and 'TCF' not in repr(self):
            raise NotImplementedError('Control file command only possible from TCF class')
        inputs = self.find_input(command=command, regex=regex)
        if len(inputs) > 1 or (hasattr(self, '_scope') and inputs and Scope('GLOBAL') not in inputs[0]._scope):
            if context is None:
                raise ValueError('{0} requires context to resolve'.format(command))
            else:
                input_ = None
                for inp in inputs:
                    if context.in_context_by_scope(inp._scope):
                        if input_ is not None:
                            raise ValueError('Multiple commands found in context')
                        input_ = inp
        elif inputs:
            input_ = inputs[0]
        else:
            input_ = None

        if input_ is None:
            return input_

        loaded_value = self.input_to_loaded_value(input_)
        if isinstance(loaded_value, Inputs):
            if len(loaded_value) > 1:
                if context is None:
                    raise ValueError('{0} requires context to resolve'.format(command))
                value_tr = context.translate(input_.expanded_value)
                if value_tr in [x.path for x in loaded_value]:
                    value = loaded_value[[x.path for x in loaded_value].index(value_tr)]
                else:
                    value = None
            value = loaded_value[0]
        elif not loaded_value:
            value = None
        else:
            value = loaded_value

        return value
