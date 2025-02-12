from .command import Command, EventCommand
from .database_entry import DatabaseEntry


class DefineBlock:

    def __init__(self, type_, name_):
        self.type = type_
        self.name = name_
        self.first_if_written = True
        self.any_if_written = False

    def __eq__(self, other):
        if isinstance(other, DefineBlock):
            return self.type == other.type and self.name == other.name
        return False


def get_commands(control_file, settings):
    """Iterate through a control file and yield parsed Command."""

    if control_file.exists():
        with control_file.open(errors='surrogateescape') as f:
            define_blocks = []
            block_names = []
            block_types = []
            neg_blocks = []
            was_end_define = False
            was_else_if = False
            was_else = False
            was_start_define = False
            for line in f:
                command = Command(line, settings)
                if was_end_define and define_blocks:
                    define_blocks.pop()
                    if neg_blocks:
                        for _ in range(len(set(neg_blocks[-1])) - 1):
                            define_blocks.pop()
                    was_end_define = False
                    if was_else or not was_else_if:
                        block_names.pop()
                        block_types.pop()
                        neg_blocks.pop()
                        was_else = False
                        was_else_if = False
                if command.is_end_define():
                    was_end_define = True
                    if command.is_else_if():
                        was_else_if = True
                    else:
                        was_else_if = False
                if command.is_start_define():
                    if was_start_define:  # if consecutive define blocks with no lines in-between - insert dummy command
                        command_ = Command('', settings)
                        command_.define_blocks = define_blocks
                        yield command_
                    was_start_define = True
                    define_block_name = command.value
                    define_block_type = command.define_start_type()
                    define_blocks.append(DefineBlock(define_block_type, define_block_name))
                    if define_block_name is not None:
                        neg_block_names = ' | '.join([f'!{x.strip()}' for x in define_block_name.split('|')])
                    else:
                        neg_block_names = ''
                    if command.is_else_if():
                        block_names[-1].append(neg_block_names)
                        block_types[-1].append(define_block_type)
                        neg_blocks[-1].append(neg_block_names)
                    else:
                        block_names.append([neg_block_names])
                        block_types.append([define_block_type])
                        neg_blocks.append([neg_block_names])
                    if was_end_define:
                        define_block = define_blocks.pop(-2)
                        define_blocks[-1].first_if_written = define_block.first_if_written
                        define_blocks[-1].any_if_written = define_block.any_if_written
                        was_end_define = False
                else:
                    was_start_define = False
                if define_blocks:
                    command.in_define_block = True
                    if command.is_else():
                        was_else = True
                        block = define_blocks.pop()
                        db = [DefineBlock(f'{type_} (ELSE)', name_) for type_, name_ in zip(block_types[-1], block_names[-1])]
                        for x in db:
                            x.any_if_written = block.any_if_written
                            x.first_if_written = block.first_if_written
                        define_blocks.extend(db)
                    elif command.is_else_if():
                        block = define_blocks.pop()
                        define_blocks.extend([DefineBlock(type_, name_) for type_, name_ in zip(block_types[-1][:-1], block_names[-1][:-1])])
                        define_blocks.append(block)
                        block_types[-1].pop(0)
                        block_names[-1].pop(0)

                command.define_blocks = define_blocks

                yield command


def get_event_commands(control_file, settings):
    """Iterate through event file and yield parsed event Command."""

    in_event = False
    if control_file.exists():
        with control_file.open(errors='surrogateescape') as f:
            for line in f:
                command = EventCommand(line, settings)
                if command.is_end_define():
                    in_event = False
                elif in_event:
                    yield command
                elif command.is_start_define():
                    in_event = True


def parse_database(database, settings):
    if not database.exists():
        return
    with database.open(errors='surrogateescape') as f:
        header = True
        for i, line in enumerate(f):
            if i > 0 and header and not entry.empty_line:
                header = False
            entry = DatabaseEntry(line, settings)
            if not line.strip():
                entry.empty_line = True
            elif line.strip()[0] in ['#', '!'] and not header:
                entry.comment = True
            elif i == 0:
                try:
                    float(line.split(',')[0])
                    header = False
                except ValueError:
                    pass
            entry.header = header
            yield entry


def get_bc_dbase_sources(bc_dbase, check_if_file=False):
    """Iterate through bc_dbase.csv and yield source files."""

    if bc_dbase.exists():
        with bc_dbase.open(errors='surrogateescape') as f:
            for i, line in enumerate(f):
                try:
                    float(line.split(',')[0])  # rainfall grid csv can just start at first line
                except Exception:
                    if i == 0:  # assume first row (and only first row) is header
                        continue
                inflow = line.split(',')
                if len(inflow) < 2:
                    continue
                if not inflow[1]:
                    continue
                file = inflow[1].strip()
                if check_if_file:
                    try:
                        float(file.strip('\'"'))
                        continue  # is number not file
                    except ValueError:
                        pass
                yield file
