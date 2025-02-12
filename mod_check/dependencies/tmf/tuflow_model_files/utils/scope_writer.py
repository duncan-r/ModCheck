import re

from ..dataclasses.scope import Scope, ScopeList

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class ScopeWriter:
    """Class to help manage scope blocks and indentation when writing to a file."""

    def __init__(self):
        #: ScopeList: List of active scopes
        self.active_scope = ScopeList([Scope('Global')])

    def write_scope(self, inc_scope: ScopeList) -> str:
        """Returns the required write scope for the input.

        ::


            e.g. Scope('Scenario', 'DEV')
            =
            If Scenario == DEV

        Parameters
        ----------
        inc_scope : ScopeList
            The scope to write to the file.

        Returns
        -------
        str
            The text to write to the file.
        """
        if not inc_scope:
            inc_scope = ScopeList([Scope('Global')])

        if inc_scope[-1].is_else():
            return f'{self.indent(1)}Else\n'

        if inc_scope[0] != Scope('Global'):
            inc_scope = ScopeList([Scope('Global')]) + inc_scope

        if inc_scope[-1] != self.active_scope[-1] and len(inc_scope) < len(self.active_scope):  # end of scope block
            if len(self.active_scope) == 1:  # we're in global scope - don't pop and doesn't require an end if
                return ''
            text = ''
            for _ in range(len(self.active_scope) - len(inc_scope)):
                scope = self.active_scope.pop()
                text = f'{text}{self.write(scope.to_string_end(), False)}\n'
            return text

        if inc_scope[-1] != self.active_scope[-1] and len(inc_scope) > len(self.active_scope):  # start of new scope
            text = ''
            i = len(inc_scope) - len(self.active_scope)
            while i:
                self.active_scope.append(inc_scope[-i])
                text = f'{text}{self.write(inc_scope[-i].to_string_start(), True)}\n'
                i -= 1
            return text

        if inc_scope[-1] != self.active_scope[-1]:  # continuation of scope with Else If
            active_scope = self.active_scope.pop()
            self.active_scope.append(inc_scope[-1])
            if active_scope.supports_else_if():
                text = f'Else {inc_scope[-1].to_string_start()}\n'
                return self.write(text, True)
            text1 = self.write(active_scope.to_string_end(), True)
            text2 = self.write(inc_scope[-1].to_string_start(), True)
            return f'{text1}\n{text2}\n'

        return ''

    def write(self, text: str, header: bool = False) -> str:
        """Writes the text with the correct indentation. Try and leave as is if the current indent level
        is correct i.e. don't start replacing tabs with spaces.

        :code:`header` indicates whether the text is a header for a scope block (therefore should be indented less).

        Parameters
        ----------
        text : str
            The text to write.
        header : bool, optional
            Whether the text is a header for a scope block, by default False

        Returns
        -------
        str
            The text with the correct indentation.
        """
        if not text:  # only indent if at least '\n' is present
            return text

        i = 1 if header else 0
        curr_width = self.calc_existing_width(text)
        reqd_width = len(self.indent(i))
        if curr_width == reqd_width:
            return text
        else:
            return self.indent(i) + text.lstrip(' \t')

    def indent(self, i: int = 0) -> str:
        """Returns the current scope indentation.

        :code:`i` can be used to modify the indentation level (removes indent level by i)
        e.g. :code:`If Scenario == ..`
        will be considered inside a scope, but should not be indented because it is the header of that scope,
        so :code:`i = 1` to remove one level of indentation.
        """
        return '    ' * (max(0, len(self.active_scope) - 1 - i))

    def calc_existing_width(self, text: str) -> int:
        """Calculates the width of the current indentation.

        Parameters
        ----------
        text : str
            The text to calculate the width of.

        Returns
        -------
        int
            The width of the current indentation.
        """
        i = re.search(r'\w', text)
        if not i:
            return 0
        indent = text[:i.start()]
        return indent.count(' ') + indent.count('\t') * 4

