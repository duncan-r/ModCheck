import typing
from abc import abstractmethod
import re

from ..dataclasses.types import SearchTagLike
from ..utils.commands import Command
from ..dataclasses.types import PathLike


class Input:
    """Abstract class for holding an input. An input class holds information on the input command, value, lists
    the associated files, and any other useful information.
    """

    def __str__(self):
        """Returns in the format of 'Command == Value' or simply 'Command' if a value does not exist."""
        if (hasattr(self, 'is_start_block') and self.is_start_block()) or (hasattr(self, 'is_end_block') and self.is_end_block()):
            return ''
        if self.command and self.value is not None:
            return '{0} == {1}'.format(self.command, self.value)
        elif self.command:
            return self.command
        return ''

    def __bool__(self):
        """Returns true if a command exists."""
        return bool(str(self))

    def __eq__(self, other):
        """Returns true if the compared commands are the same type (i.e. both GIS inputs) and the
        command and values are the same (case insensitive).
        """
        if isinstance(other, type(self)):
            return str(self).lower() == str(other).lower()

    def __hash__(self):
        """Allows inputs to be used as a key within a dictionary. Hash based on the string value of itself and an index
        value that is generated when the input class is initialised based on the time of creation. This allows inputs
        using the same syntax to both be used as keys without any conflict.
        """
        return hash(self.uuid)

    def __repr__(self):
        """Returns the class name and string value of itself. Overriden in child classes."""
        return '<{0}> {1}'.format(self.__class__.__name__, str(self))

    @property
    def command(self) -> str:
        """Property holding the command string part of :code:`Command == Value`

        Returns
        -------
        str
            The command string part of :code:`Command == Value`
        """
        if self.raw_command_obj() is not None and isinstance(self.raw_command_obj().command_orig, str):
            return self.raw_command_obj().command_orig.strip()
        elif self._input is not None:
            return self.raw_command_obj().command_orig

    @property
    def value(self) -> typing.Any:
        """Property holding the value part of :code:`Command == Value`. Value can be any type, and
        should be returned as its intended type e.g. :code:`Set Code == 0` should return an integer.

        Path values will return a string. Use expanded_value for the expanded path.

        .. note::

            ES Note - this is maybe a little inconsistent - could change

        Returns
        -------
        typing.Any
            The value part of :code:`Command == Value`
        """
        if self.raw_command_obj() is not None and isinstance(self._value_orig, str):
            if self.raw_command_obj().is_value_a_folder() or self.raw_command_obj().is_value_a_file():
                return self._value_orig
            elif self.raw_command_obj().is_value_a_number(self._value_orig):
                return self.raw_command_obj().return_number(self._value_orig)
            elif self.raw_command_obj().is_value_a_number_tuple(self._value_orig):
                return self.raw_command_obj().return_number_tuple(self._value_orig)
            else:
                return self._value_orig

    @property
    def comment(self) -> str:
        #: str: The comment associated with the input.
        return self.raw_command_obj().comment

    @property
    def expanded_value(self) -> PathLike:
        """Property holding the expanded value of 'Command == Value'. This only affects values that are a file/folder path.
        e.g. :code:`Read GIS Code == gis/2d_code.shp` will be expanded to
        :code:`Read GIS Code == C:/path/to/model/gis/2d_code.shp`

        The value should be expanded regardless of whether the file/folder exists or not.

        Returns
        -------
        PathLike
            The expanded value of :code:`Command == Value`
        """

        return self._expanded_value

    @abstractmethod
    def raw_command_obj(self) -> Command:
        """Get a list of files referenced in this object. Files should be absolute paths
        and can return multiple files even if only one input is referenced.

        At least one file per file reference should be returned even if the file does not exist.

        Returns
        -------
        Command
            The raw command object (defined in :code:`convert_tuflow_model_gis_format` module)
        """
        pass

    def is_match(self, filter: str = None, command: str = None,
                 value: str = None, regex: bool = False, regex_flags: int = 0, tags: SearchTagLike = (),
                 callback: typing.Callable = None, comments: bool = False) -> bool:
        """Returns True if the input matches the search parameters, which is made of multiple parameters.

        See :meth:`find_input() <pytuflow.tmf.ControlFile.find_input>` for details on the input filters.

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
            If set to True, will also search through comments.

        Returns
        -------
        bool
            True if the input matches the search parameters.
        """
        if callback is not None and not callback(self):
            return False
        if not self._tag_match(tags):
            return False
        if regex:
            return self._regex_match(filter, command, value, regex_flags, comments)
        return self._str_match(filter, command, value, comments)

    def _tag_match(self, tags: SearchTagLike) -> bool:
        if not tags:
            return True

        # try and get tags into a consistent format - list[tuple[key, value]]
        if isinstance(tags, str):
            tags = [tags]
        elif isinstance(tags, tuple):
            tags = list(tags)
        if len(tags) == 2 and isinstance(tags[0], str):
            tags = [tags]
        for i, tag in enumerate(tags.copy()):
            if isinstance(tag, str):
                tag = (tag, True)
                tags[i] = tag
            elif (isinstance(tag, tuple) and len(tag) == 1) or (isinstance(tag, list) and len(tag) == 1):
                tag = (tag[0], True)
                tags[i] = tag
            elif isinstance(tag, tuple) and len(tag) > 2 or isinstance(tag, list) and len(tag) > 2:
                tag = tag[:2]
                tags[i] = tag

        # loop through tags and check against value
        for tag in tags:
            if not hasattr(self, tag[0]):
                return False
            if isinstance(tag[1], bool):
                if not bool(getattr(self, tag[0])) == tag[1]:
                    return False
                continue
            if isinstance(tag[1], typing.Callable):
                if not tag[1](getattr(self, tag[0])):
                    return False
                continue
            if getattr(self, tag[0]) != tag[1]:
                return False

        return True

    def _regex_match(self, filter: str, command: str, value: str, flags: int, comments: bool) -> bool:
        if filter is not None and not re.findall(filter, str(self), flags=flags) and (not comments or not self.raw_command_obj().comment or
                not re.findall(filter, self.raw_command_obj().comment, flags=flags)):
            return False
        if command is not None and not re.findall(command, str(self.command), flags=flags):
            return False
        if value is not None and not re.findall(value, str(self.value), flags=flags):
            return False
        return True

    def _str_match(self, filter: str, command: str, value: str, comments: bool) -> bool:
        if (filter is not None and filter.lower() not in str(self).lower() and (not comments or not self.raw_command_obj().comment or
                filter.lower() not in self.raw_command_obj().comment.lower())):
            return False
        if command is not None and command.lower() not in self.command.lower():
            return False
        if value is not None and str(value).lower() not in str(self.value).lower():
            return False
        return True
