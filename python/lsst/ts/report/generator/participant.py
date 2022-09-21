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

__all__ = ["Participant"]

import typing
from argparse import Namespace
from enum import Enum

import pandas
from astropy.time import Time
from lsst.ts.salobj import SalRetCode, name_to_name_index

from .topic_definition import TopicDefinition
from .utils import get_enum_type, split_text_to_match

ParticipantType = typing.TypeVar("ParticipantType", bound="Participant")


class Participant:
    """Defines basic information about participants of an activity.

    Parameters
    ----------
    name : `str`
        Name of the component.
    includes : `list` [ `TopicDefinition` ]
        Events and telemetry to include in report generation.
    """

    def __init__(
        self,
        name: str,
        index: None | int = None,
        includes: dict[str, TopicDefinition] = dict(),
    ) -> None:
        self.name = name
        self.index = index
        self.includes = includes

        self.done_ack_codes = frozenset(
            (
                SalRetCode.CMD_ABORTED,
                SalRetCode.CMD_COMPLETE,
                SalRetCode.CMD_FAILED,
                SalRetCode.CMD_NOACK,
                SalRetCode.CMD_NOPERM,
                SalRetCode.CMD_STALLED,
                SalRetCode.CMD_TIMEOUT,
            )
        )
        self.failed_ack_codes = frozenset(
            (
                SalRetCode.CMD_ABORTED,
                SalRetCode.CMD_FAILED,
                SalRetCode.CMD_NOACK,
                SalRetCode.CMD_NOPERM,
                SalRetCode.CMD_STALLED,
                SalRetCode.CMD_TIMEOUT,
            )
        )
        self.good_ack_codes = frozenset(
            (
                SalRetCode.CMD_ACK,
                SalRetCode.CMD_INPROGRESS,
                SalRetCode.CMD_COMPLETE,
            )
        )

    def parse_command_data(
        self,
        actor: str,
        command: str,
        command_data: pandas.DataFrame,
        ackcmd_data: pandas.DataFrame,
    ) -> dict[Time, str]:
        """Parse command and acknowledgement data to generate a report.

        Parameters
        ----------
        actor : `str`
            Name of the actor that issued the command.
        command_data : `pandas.DataFrame`
            Command data.
        ackcmd_data : `pandas.DataFrame`
            Acknowledgment data.

        Returns
        -------
        report : `dict`[ `Time`, `str` ]
            Report data.
        """

        report: dict[Time, str] = dict()

        for time in command_data.index:
            report[
                Time(time)
            ] = f"{actor} -> {self.name} : {command.split('.')[-1]}\nactivate {self.name}"

        for time, ack, result in zip(
            ackcmd_data.index, ackcmd_data.ack, ackcmd_data.result
        ):
            report[
                Time(time)
            ] = f"{actor} <- {self.name}: [{SalRetCode(ack).name}]::\\n{result}" + (
                f"\ndeactivate {self.name}" if ack in self.done_ack_codes else ""
            )

        return report

    def parse_topic_data(
        self, topic_name: str, topic_data: pandas.DataFrame
    ) -> dict[Time, str]:
        """Parse topic data to generate report.

        Parameters
        ----------
        topic_data : `pandas.DataFrame`
            Topic data

        Returns
        -------
        dict[Time, str]
            Report data.
        """

        report: dict[Time, str] = dict()

        topic_display_name = topic_name.split(".")[-1]

        for time in topic_data.index:
            report[Time(time)] = f"<-- {self.name} : {topic_display_name}" + (
                f"[{self.includes[topic_display_name].generate_report(topic_data.at_time(time))}]"
                if topic_display_name in self.includes
                else ""
            )

        return report

    def get_topics_queries(self, time_start: Time, time_end: Time) -> dict[str, dict]:
        """Generate queries for the included topics.

        Parameters
        ----------
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.

        Returns
        -------
        dict[str, dict]
            _description_
        """

        topics_queries = dict()

        for topic in self.includes:
            topics_queries[f"lsst.sal.{self.name}.{topic}"] = dict(
                topic_name=f"lsst.sal.{self.name}.{topic}",
                index=self.index,
                start=time_start,
                end=time_end,
                fields="*",
            )

        return topics_queries

    @classmethod
    def from_args(
        cls: typing.Type[ParticipantType], args: Namespace
    ) -> list[ParticipantType]:
        """Create a list of of participant from command line arguments.

        Parameters
        ----------
        args : `Namespace`
            Input arguments.

        Returns
        -------
        participants : `list`[ `Participant` ]
            List of participants.
        """

        participants: list[ParticipantType] = list()

        participants_events = cls.parse_participants_events(
            participants_events=args.participants_events,
            participants=args.participants,
        )

        participants_events_attributes = cls.parse_participants_events_attributes(
            participants_events_attributes=args.participants_events_attributes,
            participants_events_attributes_enum=args.participants_events_attributes_enum,
            participants_events_enum_import_path=args.participants_events_enum_path,
            participant_events=participants_events,
        )

        for participant in args.participants:
            name, index = name_to_name_index(participant)
            includes = dict(
                [
                    (
                        event,
                        TopicDefinition(
                            name=event,
                            attributes=participants_events_attributes[participant][
                                event
                            ],
                        ),
                    )
                    for event in participants_events[participant]
                ]
            )
            print(participant, includes)
            participants.append(
                cls(
                    name=name,
                    index=index,
                    includes=includes,
                )
            )

        return participants

    @staticmethod
    def parse_participants_events(
        participants_events: None | str, participants: list[str]
    ) -> dict[str, list[str]]:
        """Parse participant events from command line arguments.

        The method basically splits participants_events in semicolon and verify
        that the result matches the expected size, e.g.:

        >>> from lsst.ts.report.generator import Participant
        >>> part_evts = "evt1,evt2;;evt1"
        >>> part = ["P1", "P2", "P3"]
        >>> Participant.parse_participants_events(part_evts, part)
        {'P1': ['evt1', 'evt2'], 'P2': [''], 'P3': ['evt1']}

        If no input is provided, return a list of empty arrays:

        >>> Participant.parse_participants_events(None, part)
        {'P1': [''], 'P2': [''], 'P3': ['']}

        Parameters
        ----------
        participants_events : `str` or None
            Comma-separated string with the name of the participant events.
        participants : `list` [ `str` ]
            List of participants.

        Returns
        -------
        participants_events_data : `dict` [ `str`, `list`[ `str` ] ]
            List of participant events.
        """

        participants_events_list = (
            participants_events.split(";")
            if participants_events is not None
            else [""] * len(participants)
        )

        assert len(participants_events_list) == len(participants), (
            "List of participants and list of participant events must have the same size. "
            f"Got {participants_events}[{len(participants_events_list)}] and "
            f"{participants}[{len(participants)}]."
        )

        participants_events_data: dict[str, list[str]] = dict()

        for participant, events_data in zip(participants, participants_events_list):
            participants_events_data[participant] = events_data.split(",")

        return participants_events_data

    @staticmethod
    def parse_participants_events_attributes(
        participants_events_attributes: None | str,
        participants_events_attributes_enum: None | str,
        participants_events_enum_import_path: None | str,
        participant_events: dict[str, list[str]],
    ) -> dict[str, dict[str, dict[str, None | typing.Type[Enum]]]]:
        """Parse participants_events_attributes into a list of dictionaries
        with the attributes for each participant event.

        Parameters
        ----------
        participants_events_attributes : `str` or None
            Participants events attributes string to parse.
        participant_events : `list`[ `str` ]
            List of participant events.

        Returns
        -------
        `dict` [ `str`, `dict`[ `str`, `list`[`str`] ] ]
            Participants events attributes.
        """

        participants_events_attributes_list = split_text_to_match(
            participants_events_attributes, participant_events, ";"
        )

        participants_events_attributes_enum_list = split_text_to_match(
            participants_events_attributes_enum, participant_events, ";"
        )

        participants_events_enum_import_path_list = split_text_to_match(
            participants_events_enum_import_path, participant_events, ";"
        )

        participants_events_attributes_data: dict[
            str, dict[str, dict[str, None | typing.Type[Enum]]]
        ] = dict()

        for (
            participant,
            events_attributes,
            events_attributes_enum,
            events_attributes_enum_import_path,
        ) in zip(
            participant_events,
            participants_events_attributes_list,
            participants_events_attributes_enum_list,
            participants_events_enum_import_path_list,
        ):
            events_attributes_data: dict[
                str, dict[str, None | typing.Type[Enum]]
            ] = dict()

            events_attributes_list = split_text_to_match(
                events_attributes, participant_events[participant], ":"
            )

            events_attributes_enum_list = split_text_to_match(
                events_attributes_enum, participant_events[participant], ":"
            )
            events_attributes_enum_import_path_list = split_text_to_match(
                events_attributes_enum_import_path, participant_events[participant], ":"
            )

            for event, attributes, enums, enums_import_path in zip(
                participant_events[participant],
                events_attributes_list,
                events_attributes_enum_list,
                events_attributes_enum_import_path_list,
            ):
                if event:
                    attributes_names = attributes.split(",") if attributes else []
                    enums_name_list = split_text_to_match(
                        enums, attributes_names, sep=",", fill_value=None
                    )
                    enums_import_path_list = split_text_to_match(
                        enums_import_path, attributes_names, sep=",", fill_value=None
                    )
                    attribute_values = [
                        get_enum_type(import_path=path, enum_name=enum)
                        if enum is not None
                        else None
                        for enum, path in zip(enums_name_list, enums_import_path_list)
                    ]

                    events_attributes_data[event] = dict(
                        [
                            (name, value)
                            for name, value in zip(attributes_names, attribute_values)
                        ]
                        if attributes
                        else []
                    )

            participants_events_attributes_data[participant] = events_attributes_data

        return participants_events_attributes_data
