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
from astropy.time import Time
from lsst.ts.report.generator import Participant, TopicDefinition
from lsst.ts.salobj import State


def test_parse_command_data(
    command: str,
    command_data: pandas.DataFrame,
    ackcmd_data: pandas.DataFrame,
    expected_command_report: dict[Time, str],
) -> None:

    participant = Participant(name="ATAOS")

    report = participant.parse_command_data(
        actor="Script",
        command=command,
        command_data=command_data,
        ackcmd_data=ackcmd_data,
    )

    for time in report:
        assert report[time] == expected_command_report[time]


def test_topic_data_simple(topic_name: str, topic_data: pandas.DataFrame) -> None:

    participant = Participant(name="ATAOS")

    report = participant.parse_topic_data(topic_name=topic_name, topic_data=topic_data)

    expected_report: dict[Time, str] = {
        Time(
            pandas.Timestamp("2022-09-14 08:09:09.000000+0000", tz="UTC")
        ): "<-- ATAOS : logevent_summaryState"
    }

    for time in report:
        assert report[time] == expected_report[time]


def test_topic_data_with_topic_info(
    topic_name: str, topic_data: pandas.DataFrame
) -> None:

    participant = Participant(
        name="ATAOS",
        includes={
            "logevent_summaryState": TopicDefinition(
                name="logevent_summaryState",
                attributes=dict(summaryState=None),
            ),
        },
    )

    report = participant.parse_topic_data(topic_name=topic_name, topic_data=topic_data)

    expected_report: dict[Time, str] = {
        Time(
            pandas.Timestamp("2022-09-14 08:09:09.000000+0000", tz="UTC")
        ): f"<-- ATAOS : logevent_summaryState[{State.FAULT.value}]"
    }

    for time in report:
        assert report[time] == expected_report[time]


def test_topic_data_with_topic_info_and_enum(
    topic_name: str, topic_data: pandas.DataFrame
) -> None:

    participant = Participant(
        name="ATAOS",
        includes={
            "logevent_summaryState": TopicDefinition(
                name="logevent_summaryState",
                attributes=dict(summaryState=State),
            ),
        },
    )

    report = participant.parse_topic_data(topic_name=topic_name, topic_data=topic_data)

    expected_report: dict[Time, str] = {
        Time(
            pandas.Timestamp("2022-09-14 08:09:09.000000+0000", tz="UTC")
        ): "<-- ATAOS : logevent_summaryState[FAULT]"
    }

    for time in report:
        assert report[time] == expected_report[time]


def test_parse_participants_events() -> None:

    participants_events = "evt1,evt2;;evt1"
    participants = ["P1", "P2", "P3"]

    participants_events_data = Participant.parse_participants_events(
        participants_events, participants
    )

    assert len(participants_events_data) == len(participants)
    assert participants_events_data["P1"][0] == "evt1"
    assert participants_events_data["P1"][1] == "evt2"
    assert participants_events_data["P2"][0] == ""
    assert participants_events_data["P3"][0] == "evt1"


def test_parse_participants_events_none() -> None:

    participants = ["P1", "P2", "P3"]

    participants_events_data = Participant.parse_participants_events(None, participants)

    assert len(participants_events_data) == len(participants)
    assert participants_events_data["P1"][0] == ""
    assert participants_events_data["P2"][0] == ""
    assert participants_events_data["P3"][0] == ""


def test_parse_participants_events_wrong_size() -> None:

    participants_events = "evt1,evt2;"
    participants = ["P1", "P2", "P3"]

    with pytest.raises(AssertionError):
        Participant.parse_participants_events(participants_events, participants)


def test_parse_participants_events_attributes_no_attributes() -> None:

    participants_events = "evt1,evt2;;evt1"
    participants = ["P1", "P2", "P3"]

    part_evts_dict = Participant.parse_participants_events(
        participants_events, participants
    )
    articipants_events_attributes = Participant.parse_participants_events_attributes(
        None, None, None, part_evts_dict
    )

    assert len(articipants_events_attributes) == 3

    assert len(articipants_events_attributes["P1"]) == 2
    assert len(articipants_events_attributes["P2"]) == 0
    assert len(articipants_events_attributes["P3"]) == 1

    assert len(articipants_events_attributes["P1"]["evt1"]) == 0
    assert len(articipants_events_attributes["P1"]["evt2"]) == 0
    assert len(articipants_events_attributes["P3"]["evt1"]) == 0


def test_parse_participants_events_attributes_attributes() -> None:

    participants_events = "evt1,evt2;;evt1"
    participants_events_attributes = "attr1_1_1,attr1_1_2:attr1_2_1;;attr3_1_1"
    participants = ["P1", "P2", "P3"]

    part_evts_dict = Participant.parse_participants_events(
        participants_events, participants
    )
    articipants_events_attributes = Participant.parse_participants_events_attributes(
        participants_events_attributes, None, None, part_evts_dict
    )

    assert len(articipants_events_attributes) == 3

    assert len(articipants_events_attributes["P1"]) == 2
    assert len(articipants_events_attributes["P2"]) == 0
    assert len(articipants_events_attributes["P3"]) == 1

    assert len(articipants_events_attributes["P1"]["evt1"]) == 2
    assert len(articipants_events_attributes["P1"]["evt2"]) == 1
    assert len(articipants_events_attributes["P3"]["evt1"]) == 1

    assert articipants_events_attributes["P1"]["evt1"]["attr1_1_1"] is None
    assert articipants_events_attributes["P1"]["evt1"]["attr1_1_2"] is None
    assert articipants_events_attributes["P1"]["evt2"]["attr1_2_1"] is None
    assert articipants_events_attributes["P3"]["evt1"]["attr3_1_1"] is None


def test_parse_participants_events_attributes_attributes_enums() -> None:

    participants_events = "evt1,evt2;;evt1"
    participants_events_attributes = "attr1_1_1,attr1_1_2:attr1_2_1;;attr3_1_1"
    participants_events_attributes_enum = "State,:State;;State"
    participants_events_enum_import_path = (
        "lsst.ts.salobj,:lsst.ts.salobj;;lsst.ts.salobj"
    )

    participants = ["P1", "P2", "P3"]

    part_evts_dict = Participant.parse_participants_events(
        participants_events, participants
    )
    articipants_events_attributes = Participant.parse_participants_events_attributes(
        participants_events_attributes,
        participants_events_attributes_enum,
        participants_events_enum_import_path,
        part_evts_dict,
    )

    assert len(articipants_events_attributes) == 3

    assert len(articipants_events_attributes["P1"]) == 2
    assert len(articipants_events_attributes["P2"]) == 0
    assert len(articipants_events_attributes["P3"]) == 1

    assert len(articipants_events_attributes["P1"]["evt1"]) == 2
    assert len(articipants_events_attributes["P1"]["evt2"]) == 1
    assert len(articipants_events_attributes["P3"]["evt1"]) == 1

    assert articipants_events_attributes["P1"]["evt1"]["attr1_1_1"] is State
    assert articipants_events_attributes["P1"]["evt1"]["attr1_1_2"] is None
    assert articipants_events_attributes["P1"]["evt2"]["attr1_2_1"] is State
    assert articipants_events_attributes["P3"]["evt1"]["attr3_1_1"] is State
