import pandas as pd

from ..abc.run_state import RunState
from ..abc.db import Database


class CrossSectionRunState(RunState, Database):
    """Run state class for cross-sections database."""

    def __repr__(self):
        if self.path:
            if self.path.exists():
                return '<{0}Context> {1}'.format(self.bs.__class__.__name__, self.path.name)
            return '<{0}Context> {1} (not found)'.format(self.bs.__class__.__name__, self.path.name)
        else:
            return '<DatabaseContext> (empty)'

    def _init(self) -> None:
        self.path = self.bs.path
        self._loaded = self.bs._loaded
        self._driver = self.bs._driver.copy()

    def _resolve_scope_in_context(self) -> None:
        if not self._driver.unresolved_xs:
            self._df = self.bs._df.copy()
            return

        # cross-section attributes need some resolving
        self._df = pd.DataFrame()
        for xsid in self._driver.unresolved_xs.copy():
            xs = self._driver.cross_sections[xsid]
            for key, value in xs.attrs.copy().items():
                new_val = self.ctx.translate(value)
                if not self.ctx.is_resolved(new_val):
                    raise AttributeError('Input has not been completely resolved - {0}'.format(value))
                xs.attrs[key] = new_val
            try:
                xs.load()
                self._driver.unresolved_xs.remove(xsid)
            except Exception:
                # log something went wrong
                pass

        self._df = self._driver.generate_df()

        self._index_to_file = {x.id: x.fpath for x in self._driver.cross_sections.values()}

