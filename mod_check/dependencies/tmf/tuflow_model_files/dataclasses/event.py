class EventDatabase(dict):
    """
    Event database class for storing all event variable information.

    This does not include custom TCF commands.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._keys_lower = {key.lower(): key for key in self.keys()}

    def __getitem__(self, item):
        """Case insensitive key lookup."""
        return dict.__getitem__(self, self._keys_lower[item.lower()])

    def __setitem__(self, key, value):
        """Record the original key case for case insensitive lookup."""
        self._keys_lower[key.lower()] = key
        dict.__setitem__(self, key, value)

    def __contains__(self, item):
        """Case insensitive key check."""
        return item.lower() in self._keys_lower

    def get(self, __key: any) -> any:
        """Case insensitive key lookup."""
        if __key in self:
            return self[__key]


class Event:
    """
    Class for storing individual event variable and name information
    collected from a TUFLOW Event File.
    """

    __slots__ = ('name', 'variable', 'value')

    def __init__(self, name: str, variable: str, value: str):
        self.name = name
        self.variable = variable
        self.value = value

    def __repr__(self):
        return f'<Event> {str(self)}'

    def __str__(self):
        return f'{self.name}: {self.variable} | {self.value}'

    def __eq__(self, other):
        """Event objects are considered equal if their name, variable name and variable value are equal."""
        if isinstance(other, type(self)):
            return self.name.lower() == other.name.lower() and \
                self.variable.lower() == other.variable.lower() and \
                self.value.lower() == other.value.lower()
        return False
