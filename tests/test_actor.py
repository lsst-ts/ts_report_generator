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

import pandas
import pytest
from astropy.time import Time, TimeDelta
from lsst.ts.idl.enums.Script import ScriptState
from lsst.ts.report.generator import Actor


def test_generate_query_kwargs_with_event() -> None:
    actor = Actor(
        name="Script",
        index=123,
        event="logevent_state",
        attribute="state",
        enum=ScriptState,
    )

    time_start = Time.now()
    time_end = time_start + TimeDelta(val=120, format="sec")

    query_kwargs = actor.generate_query_kwargs(time_start=time_start, time_end=time_end)

    for key, value in [
        ("topic_name", "lsst.sal.Script.logevent_state"),
        ("index", 123),
        ("start", time_start),
        ("end", time_end),
        ("fields", "*"),
    ]:
        assert query_kwargs[key] == value


def test_generate_query_kwargs_no_event() -> None:
    actor = Actor(
        name="Script",
        index=123,
    )

    time_start = Time.now()
    time_end = time_start + TimeDelta(val=120, format="sec")

    assert actor.generate_query_kwargs(time_start=time_start, time_end=time_end) is None


def test_parse_data_no_event(sample_actor_data: pandas.DataFrame) -> None:
    actor = Actor(
        name="Script",
        index=123,
    )

    with pytest.raises(AssertionError):
        actor.parse_data(sample_actor_data)

    with pytest.raises(AssertionError):
        actor.actor_private_origin


def test_parse_data_with_event(sample_actor_data: pandas.DataFrame) -> None:
    actor = Actor(
        name="Script",
        index=123,
        event="logevent_state",
    )

    report, time_start, time_end = actor.parse_data(sample_actor_data)

    assert time_start in report
    assert time_end in report
    assert actor.actor_private_origin == 47370
    assert report[time_start] == "<-- Script : logevent_state"
    assert report[time_end] == "<-- Script : logevent_state"


def test_parse_data_with_event_attribute(sample_actor_data: pandas.DataFrame) -> None:
    actor = Actor(
        name="Script",
        index=123,
        event="logevent_state",
        attribute="state",
    )

    report, time_start, time_end = actor.parse_data(sample_actor_data)

    assert time_start in report
    assert time_end in report
    assert actor.actor_private_origin == 47370
    assert report[time_start] == f"<-- Script : {ScriptState.UNCONFIGURED}"
    assert report[time_end] == f"<-- Script : {ScriptState.FAILED}"


def test_parse_data_with_event_attribute_enum(
    sample_actor_data: pandas.DataFrame,
) -> None:
    actor = Actor(
        name="Script",
        index=123,
        event="logevent_state",
        attribute="state",
        enum=ScriptState,
    )
    report, time_start, time_end = actor.parse_data(sample_actor_data)

    assert time_start in report
    assert time_end in report
    assert actor.actor_private_origin == 47370
    assert report[time_start] == "<-- Script : UNCONFIGURED"
    assert report[time_end] == "<-- Script : FAILED"
