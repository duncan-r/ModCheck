import re
from pathlib import Path

import numpy as np
from typing import Any

from ..dataclasses.file import PathType
from ..dataclasses.types import PathLike
# this import is not being used in this file, but it is used as a proxy for other imports elsewhere in the package to
# avoid excessive importing from the convert_tuflow_model_gis_format submodule
from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.file import globify, TuflowPath

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()

var_regex = re.compile(r'(<<\w{3,}>>|<<[A-DF-RT-df-rt-z]+.+>>|<<~s\D\w+~>>|<<~e\D\w+~>>|<<~s[A-z]+~>>|<<~e[A-z]+~>>)')
wildcard_regex = re.compile(r'<<.+>>')


def extract_names_from_pattern(string_with_var: str, extraction_string: str, pattern: str) -> dict[str, str]:
    """Given a string with variables in it (e.g. 2d_code_<<~s~>>_001.shp) and an input string to compare to
    (e.g. 2d_code_M01_001.shp) a variable value can be extracted for the variable name (<<~s~>> = 'M01').

    The return is a dictionary with the variable name/value pair e.g. {'<<~s~>>': 'M01'}

    The pattern should be a regex pattern. This routine will extract multiple variables if found in the template
    string (e.g. pattern '<<~s\d~>>' could extract <<~s1~>> and <<~s2~>> from the template string). The variable
    may appear multiple times in the name and that is ok.

    There are given situations where it is not possible to resolve what the variable name since it could be
    expanded in multiple ways (e.g. 2d_code_<<~e1~>><<~e2~>>_001.shp - 2d_code_100yr2hr_001.shp).
    Because the variables are not delimited, the values could be expanded in multiple ways. Where this happens
    the return name will be the same as the variable name (e.g. {'<<~e1~>>': '<<~e1~>>', '<<~e2~>>': '<<~e2~>>'}).

    Another example of when it may struggle to figure out the variable value is when event variable names are
    used. As event variables don't follow a specific pattern (aren't surrounded by <<>>) then it isn't possible
    to recognise them unless you have a list of them.

    Parameters
    ----------
    string_with_var : str
        The string with variables in it.
    extraction_string : str
        The string to compare to.
    pattern : str
        The regex pattern to use to extract the variable names.

    Returns
    -------
    dict[str, str]
        The variable name/value pair.
    """
    extracted_names = {}
    for var_name in re.findall(pattern, string_with_var, flags=re.IGNORECASE):
        if var_name in extracted_names:
            continue
        extracted_names[var_name] = None
        if re.findall(r'<<~[EeSs]1?~>>', var_name):  # <<~s~>> will be treated the same as <<~s1~>>
            var_name_ = re.sub(r'1?~>>', '1?~>>', var_name)
        else:
            var_name_ = var_name

        names = identify_expanded_name(string_with_var, extraction_string, var_name_)

        if len(set(names)) > 1:
            name_ = [x for x in names if x][0]
        elif not names[0]:
            name_ = var_name
        else:
            name_ = names[0]

        extracted_names[var_name] = name_

    return extracted_names


def identify_expanded_name(string_with_var: str, extraction_string: str, var_name: str) -> list[str]:
    """Given a string with variables in it, an extraction string to compare to, and a variable name, this
    routine will identify what the variable name has expanded to.

    Unlike :func:`extract_names_from_pattern`, the pattern should be specific, not a regex pattern
    (e.g. should be '<<~s1~>>' not <<~[se]\d.~>>). This routine is used by :func:`extract_names_from_pattern`
    to do most of the heavy lifting in terms of identifying the name for a specific variable.

    The return type is a list of found variable values (as the variable name could appear multiple times e.g.
    2d_code_<<~s1~>>_<<~s1~>>_001.shp). It is up to the calling routine to check if the return names are consistent.

    If it isn't possible to determine the variable value, the return will be a list of empty strings for each
    time the variable appears in the string.

    Parameters
    ----------
    string_with_var : str
        The string with variables in it.
    extraction_string : str
        The string to compare to.
    var_name : str
        The variable name to identify.

    Returns
    -------
    list[str]
        The variable values.
    """

    # check to see if the variable name is 'isolated' (i.e. not directly next to another variable name)
    # if it is not isolated, don't try and expand as it's not possible to figure out the variable value is
    # trying to expand it could lead to incorrect results which is worse than not finding anything
    if re.findall(f'(<<.+?>>){var_name}', string_with_var, flags=re.IGNORECASE) or \
            re.findall(f'{var_name}(<<.+?>>)', string_with_var, flags=re.IGNORECASE):
        isolated_scenario_name = False
        for match in re.finditer(var_name, string_with_var, flags=re.IGNORECASE):
            span = match.span()
            if span[0] > 1:
                if string_with_var[span[0] - 2:span[0]] == '>>':
                    continue
            if span[1] < len(string_with_var) - 1:
                if string_with_var[span[1]:span[1] + 2] == '<<':
                    continue
            isolated_scenario_name = True
        if not isolated_scenario_name:
            return ['' for _ in range(len(re.findall(var_name, string_with_var, flags=re.IGNORECASE)))]

    # break the input string into parts around the variable name(s)
    # (e.g. 2d_code_<<~s1~>>_001.shp -> ['2d_code_', '_001.shp'])
    # check for other possible variable names that could appear in the string and replace with globbing
    # build regex patterns for each part then index where they appear in the extraction string
    # any part that has not been found will be the missing variable value(s)
    # the tricky part can be knowing when to use a greedy match or lazy match and when to insert additional globbing
    s_parts = re.split(var_name, string_with_var, flags=re.IGNORECASE)
    names = []
    i2_prev = -1
    for k in range(len(s_parts) - 1):
        s1 = '.+?'.join([re.escape(x) for x in s_parts[:k+1]])
        if len(s_parts) > k + 1:
            if len(s_parts) > k + 2:
                if s1[-2:] == '>>':
                    s1 = f'{s1}(?={".+".join([re.escape(x) for x in s_parts[k+1:]])})'
                else:
                    s1 = f'{s1}(?=.+{".+".join([re.escape(x) for x in s_parts[k + 1:]])})'
            else:
                s1 = f'{s1}(?=.+{re.escape(s_parts[k + 1])})'
        s2 = '.+?'.join([re.escape(x) for x in s_parts[k+1:]])
        s1_ = re.sub('<<.+?>>', '.+?', s1, flags=re.IGNORECASE)
        s2_ = re.sub('<<.+?>>', '.+?', s2, flags=re.IGNORECASE)
        i2 = -2
        i3 = 0
        found_match = True
        input_string_ = extraction_string
        while i2 < i2_prev and found_match:
            found_match = False
            for m in re.finditer(s1_, input_string_, flags=re.IGNORECASE):
                found_match = True
                _, i2 = m.span()
                break
            i2 += i3
            i3 = i2 + 1
            input_string_ = extraction_string[i2 + 1:]

        if not found_match:
            names.append('')
            continue

        i2_prev = i2

        found_match = True
        j2 = -1
        j3 = 0
        input_string_ = extraction_string
        while j2 < i2 and found_match:
            found_match = False
            for m in re.finditer(s2_, input_string_, flags=re.IGNORECASE):
                found_match = True
                j2, _ = m.span()
                j2 += j3
                j3 = j2 + 1
                input_string_ = extraction_string[j2 + 1:]
                break

        names.append(extraction_string[i2:j2])

    return names


def replace_exact_names(pattern: str, map: dict[str, Any], input_string: str) -> str:
    """Use regex substitution to replace variable names with their values.

    The pattern is a regex pattern or if the 'pattern' argument == 'variable pattern' it will
    use the precompiled regex pattern that is specifically for TUFLOW variable names that won't
    select event or scenario names e.g. <<~s1~>> or <<~e1~>>  or even <<s>> or <<e>>.

    The map is a dictionary of variable names and their values. The map is assumed to not include the <> or ~.
    The keys should also be capitalised e.g. <<~s1~>> would be 'S1' in the map.

    The input string is the string to be modified.

    The routine is not case sensitive and treat variable names <<~e~>> and <<~s~>> as <<~e1~>> and <<~s1~>>.
    The routine will also maintain the variable value type i.e. if the value is an integer, the return value
    will be an integer.

    Parameters
    ----------
    pattern : str
        The regex pattern to use to find the variable names. Or 'variable pattern' to use the precompiled
        regex pattern for TUFLOW variable names.
    map : dict[str, Any]
        The variable name/value pair.
    input_string : str
        The string to modify.

    Returns
    -------
    str
        The modified string.
    """

    if not isinstance(input_string, str):
        return input_string

    if pattern == 'variable pattern':
        regex = var_regex
    else:
        regex = re.compile(pattern, flags=re.IGNORECASE)

    output_string = input_string
    for item in regex.findall(input_string):
        if re.findall(r'<<~[SsEe]~>>', item):
            key = re.sub(r'~>>', '1~>>', item)
        else:
            key = item
        if re.findall(r'<<~[SsEe]', item):
            key = key.strip('<~>').upper()
        else:
            key = key.strip('<>').upper()
        if key not in map:
            continue
        type_ = type(map[key])
        output_string = output_string.replace(item, str(map[key]))
        if type_ == float or type_ == np.float64 or type_ == np.float32:
            output_string = float(output_string)
        elif type_ == int or type_ == np.int64 or type_ == np.int32:
            output_string = int(output_string)

    return output_string


def get_geom_ext(in_name: str) -> str:
    """Identify and return the geometry extension if it exists within the input name. It is assumed any file extensions
    are removed before calling this routine.

    Examples
    --------
    >>> get_geom_ext('2d_code_001_R')
    '_R'
    >>> get_geom_ext('2d_code_001')
    ''

    Parameters
    ----------
    in_name : str
        The input name.

    Returns
    -------
    str
        The geometry extension.
    """
    geom_ext = re.findall(r'_[PLR]$', in_name, flags=re.IGNORECASE)
    if geom_ext:
        return geom_ext[0]
    return ''


def get_iter_number(in_name: str, geom_ext: str) -> str:
    """Identify and return the iteration number if it exists within the input name. It is assumed any file extensions
    are removed before calling this routine.

    Examples
    --------
    >>> get_iter_number('2d_code_001_R', '_R')
    '001'

    Parameters
    ----------
    in_name : str
        The input name.
    geom_ext : str
        The geometry extension (e.g. '_R').

    Returns
    -------
    str
        The iteration number.
    """
    iter_number = re.findall(r'\d+(?={0}$)'.format(geom_ext), in_name)
    if iter_number:
        return iter_number[0]


def name_without_number_part(name_: str) -> str:
    """Return the input name without the iteration number. It is assumed any file extensions are removed before calling
    this routine.

    Examples
    --------
    >>> name_without_number_part('2d_code_001_R')
    '2d_code_R'

    Parameters
    ----------
    name_ : str
        The input name.

    Returns
    -------
    str
        The name without the iteration number.
    """
    number_part = re.findall(r'_\d+(?:_[PLR])?$', name_, flags=re.IGNORECASE)
    if number_part:
        return re.sub(re.escape(number_part[0]), '', name_)
    return name_


def auto_increment_name(in_name: str) -> str:
    """Automatically increment the input name by one. The zero padding should be respected based on the input.
    If a number does not exist in the name, one is added. It is assumed any file extensions are removed
    before calling this routine.

    Examples
    --------
    >>> auto_increment_name('2d_code_001_R')
    '2d_code_002_R'
    >>> auto_increment_name('2d_code_R')
    '2d_code_001_R'

    Parameters
    ----------
    in_name : str
        The input name.

    Returns
    -------
    str
        The incremented name.
    """
    ext = ''
    if TuflowPath(in_name).suffix:
        ext = TuflowPath(in_name).suffix
        in_name = TuflowPath(in_name).stem

    number_part = re.findall(r'_\d+(?:_[PLR])?$', in_name, flags=re.IGNORECASE)
    geom_ext = get_geom_ext(in_name)

    if not number_part:
        if geom_ext:
            out_number_part = f'_001{geom_ext}'
            return re.sub(re.escape(geom_ext), re.escape(out_number_part), in_name) + ext
        else:
            return f'{in_name}_001{ext}'

    out_name = re.sub(re.escape(number_part[0]), '', in_name)
    iter_number = get_iter_number(number_part[0], geom_ext)
    pad = len(iter_number)
    iter_number = f'{int(iter_number) + 1:0{pad}d}'
    return f'{out_name}_{iter_number}{geom_ext}{ext}'


def increment_new_name(name_: str, inc: str) -> str:
    """Increment the name with the given increment. The increment should be a string representing a number, or 'auto' or
    'inplace'. If 'auto' is given, the name will be automatically incremented. If 'inplace' is given, the name will not
    be changed.

    Examples
    --------
    >>> increment_new_name('2d_code_001_R', 'auto')
    '2d_code_002_R'
    >>> increment_new_name('2d_code_001_R', 'inplace')
    '2d_code_001_R'
    >>> increment_new_name('2d_code_001_R', '005')
    '2d_code_005_R'

    Parameters
    ----------
    name_ : str
        The input name.
    inc : str
        The increment number (as a string), or 'auto' or 'inplace'.

    Returns
    -------
    str
        The incremented name.
    """
    if inc.lower() == 'inplace':
        return name_
    elif inc.lower() == 'auto':
        return auto_increment_name(name_)
    else:
        return f'{name_without_number_part(TuflowPath(name_).stem)}_{inc}{TuflowPath(name_).suffix}'


def increment_fpath(fpath: PathLike, inc: str) -> TuflowPath:
    """Increment the file path with the given increment. The increment should be a string representing a number, or
    'auto', or 'inplace'. If 'auto' is given, the name will be automatically incremented. If 'inplace' is given, the
    name will not be changed.

    See :func:`increment_new_name` for more information.

    Parameters
    ----------
    fpath : PathLike
        The input file path.
    inc : str
        The increment number (as a string), or 'auto' or 'inplace'.

    Returns
    -------
    TuflowPath
        The incremented file path.
    """
    p = TuflowPath(fpath)
    return TuflowPath(f'{p.parent}/{increment_new_name(p.name, inc)}')


def contains_variable(string: str) -> bool:
    """Check if the string contains a variable.

    Examples
    --------
    >>> contains_variable('2d_code_<<~s~>>_001.shp')
    True

    Parameters
    ----------
    string : str
        The input string.

    Returns
    -------
    bool
        True if the string contains a variable, False otherwise.
    """
    return bool(wildcard_regex.findall(string))


def expand_and_get_files(parent: PathLike, relpath: str, patterns: list[str] = ()) -> list[Path]:
    """Expand pattern and return list of files. The parent should not contain any variables. The relpath may contain
    variables. If :code:`patterns` is included, the relpath will be expanded based on the patterns. If no patterns are
    included, the relpath will be expanded based on standard TUFLOW variable convention (i.e. <<>>).

    Parameters
    ----------
    parent : PathLike
        The parent directory.
    relpath : str
        The relative path.
    patterns : list[str], optional
        The patterns to use for expanding the relpath, by default ().

    Returns
    -------
    list[Path]
        The list of files.
    """
    parent = Path(parent)
    req_expanding = False
    if patterns:
        for pattern in patterns:
            if re.findall(relpath, pattern):
                req_expanding = True
                break
        relpath_glob = globify(relpath, patterns)
    else:
        if contains_variable(relpath):
            req_expanding = True
        relpath_glob = globify(relpath, ['<<.+>>'])

    if not req_expanding:
        return [(parent / relpath).resolve()]

    try:
        return [x.resolve() for x in parent.glob(relpath_glob) if x.is_file()]
    except NotImplementedError:  # this is thrown in relpath is not in-fact a relative path, but an absolute path
        fpath = Path(relpath)
        i = -1
        for i, part in enumerate(fpath.parts):
            if contains_variable(part):
                break
        if i == -1:
            return [fpath]  # shouldn't get here
        parent = Path().joinpath(*fpath.parts[:i])
        relpath = str(Path().joinpath(*fpath.parts[i:]))
        return [x.resolve() for x in parent.glob(relpath) if x.is_file()]
