# This file is part of ts_report_generator.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = [
    "get_updated_report",
    "get_enum_type",
    "split_text_to_match",
]

import typing
from enum import Enum
from importlib import import_module


def get_enum_type(import_path: str, enum_name: str) -> typing.Type[Enum]:
    r"""Get the enum type.

    This method is used when parsing the command line arguments to generate
    the enumeration types from strings.

    >>> from lsst.ts.report.generator import get_enum_type
    >>> get_enum_type("lsst.ts.idl.enums.Script", "ScriptState")
    <enum 'ScriptState'>

    Parameters
    ----------
    import_path : `str`
        Import path to the enumeration.
    enum_name : `str`
        Name of the enumeration.

    Returns
    -------
    `typing.Type`[ `Enum` ]
        Enumeration type.
    """
    try:
        enum_module = import_module(import_path)
    except Exception:
        raise RuntimeError(f"Failed to import {enum_name} from {import_path}.")
    enum_type = getattr(enum_module, enum_name)
    assert issubclass(enum_type, Enum)
    return enum_type


def get_updated_report(
    report_data: dict[typing.Any, typing.Any],
    new_report_data: dict[typing.Any, typing.Any],
) -> dict[typing.Any, typing.Any]:
    r"""Generate an update report based on an existing report and new report
    entries.

    The method checks if new data keys is already in the report, if so
    append the new text to the existing one.

    Use this method alongside dict().update to insert the new values, e.g.

    >>> from lsst.ts.report.generator.utils import get_updated_report
    >>> report_data = dict(a="some text", b="some other text")
    >>> new_report_data = dict(b="some new text for b", c="new report entry")
    >>> report_data.update(get_updated_report(report_data, new_report_data))
    >>> report_data["a"]
    'some text'
    >>> report_data["b"]
    'some other text\nsome new text for b'
    >>> report_data["c"]
    'new report entry'

    Parameters
    ----------
    report_data : dict[Time, str]
        _description_
    new_report_data : dict[Time, str]
        _description_

    Returns
    -------
    dict[Time, str]
        _description_
    """

    updated_report = dict()

    for time, entry in new_report_data.items():
        if time in report_data:
            updated_report[time] = f"{report_data[time]}\n{entry}"
        else:
            updated_report[time] = entry

    return updated_report


def split_text_to_match(
    text: None | str, match: typing.Sized, sep: str, fill_value: typing.Any = ""
) -> list[str]:
    """Split input text to match list.

    Parameters
    ----------
    text : str
        _description_
    match : list[str]
        _description_

    Returns
    -------
    list[str]
        _description_
    """
    text_split = (
        text.split(sep)
        if text is not None and len(text) > 0
        else [fill_value] * len(match)
    )

    assert len(text_split) == len(match), (
        "Split text and match must have the same size. "
        f"Got {text_split}[{len(text_split)}] and "
        f"{match}[{len(match)}]."
    )

    return [
        text if text is not None and len(text) > 0 else fill_value
        for text in text_split
    ]
