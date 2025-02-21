from ..dataclasses.event import Event, EventDatabase
from ..dataclasses.scope import Scope
from .cf import ControlFile
from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.command import EventCommand


class TEFBase(ControlFile):

    def event_database(self) -> EventDatabase:
        events = EventDatabase()
        # inputs are only collected for commands so empty scope blocks will be missing, but for events we need
        # to consider all events, even blank ones (rare, but I've seen "Define Event" blocks with nothing in them)
        events_ = []
        if self.path.exists():
            with self.path.open() as f:
                for line in f:
                    a = line.split('!')[0].split('#')[0].strip()
                    if '==' in a and 'Define Event' in a:
                        events_.append(a.split('==')[1].strip())

        for event in events_:
            input_ = self.find_input(tags=('_scope', lambda x: Scope('EVENT VARIABLE', event) in x))
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
