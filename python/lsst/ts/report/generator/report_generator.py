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
    "ReportGenerator",
    "generate_report",
]

import asyncio
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas
from astropy.time import Time
from lsst_efd_client import EfdClient

from .actor import Actor
from .participant import Participant
from .utils import get_updated_report


class ReportGenerator:
    """Generate report from EFD data.

    Parameters
    ----------
    actor : `Actor`
        Name of the component that acts as the actor of the operation.
    efd_name : `str`
        Name of the EFD instance for which to retrieve credentials.
    """

    def __init__(self, actor: Actor, efd_name: str) -> None:

        self.log = logging.getLogger(__name__)

        self.actor = actor
        self.efd_client = EfdClient(efd_name=efd_name)

        self._topics: list[str] = []

    async def generate_report(
        self, participants: list[Participant], time_start: Time, time_end: Time
    ) -> str:
        """Generate report for an action involving a list of participants at a
        particular time window.

        Parameters
        ----------
        participants : `list`[ `Participant` ]
            List of participants.
        time_start : `Time`
            Time when the activity starts.
        time_end : `Time`
            Time the activity ends.

        Returns
        -------
        report : `str`
            UML-like report string.
        """

        self.log.info("Generating actor report.")
        (
            report_data,
            action_start_time,
            action_end_time,
        ) = await self.get_actor_report(time_start=time_start, time_end=time_end)

        for participant in participants:
            self.log.info(f"Generating participant report: {participant.name}")
            participant_report_data = await self.get_participant_report(
                participant=participant,
                time_start=action_start_time,
                time_end=action_end_time,
            )
            report_data.update(get_updated_report(report_data, participant_report_data))

        times = list(report_data.keys())
        times.sort()

        report = ""
        for time in times:
            report += f"{report_data[time]}\n"

        return report

    async def get_actor_report(
        self, time_start: Time, time_end: Time
    ) -> tuple[dict[Time, str], Time, Time]:
        """Get actor report.

        Parameters
        ----------
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.

        Returns
        -------
        actor_report_data : `dict`[ `Time`, `str` ]
            Dictionary with the actor report data.
        action_start_time : `Time`
            Time when the activity starts.
        action_end_time : `Time`
            Time when the activity ends.
        """
        select_time_series_kwargs = self.actor.generate_query_kwargs(
            time_start=time_start, time_end=time_end
        )

        if select_time_series_kwargs is not None:
            actor_data = await self.efd_client.select_time_series(
                **select_time_series_kwargs
            )
            return self.actor.parse_data(data=actor_data)

        return dict(), time_start, time_end

    async def get_participant_report(
        self, participant: Participant, time_start: Time, time_end: Time
    ) -> dict[Time, str]:
        """Get participant report.

        Parameters
        ----------
        participant : `Participant`
            Participant.
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.

        Returns
        -------
        dict[Time, str]
            _description_
        """

        participant_topics = await self.get_topics_for(participant.name)

        participant_commands = [
            topic
            for topic in participant_topics
            if f"{participant.name}.command_" in topic
        ]

        participant_report: dict[Time, str] = dict()

        for command in participant_commands:
            command_seq_num, command_data = await self.get_command_data(
                command=command, time_start=time_start, time_end=time_end
            )
            if command_seq_num is not None:
                ackcmd_data = await self.get_ackcmd_data(
                    component_name=participant.name,
                    command_seq_num=command_seq_num,
                    time_start=time_start,
                    time_end=time_end,
                )

                command_report = participant.parse_command_data(
                    actor=self.actor.name,
                    command=command,
                    command_data=command_data,
                    ackcmd_data=ackcmd_data,
                )

                participant_report.update(
                    get_updated_report(participant_report, command_report)
                )

        topic_queries = participant.get_topics_queries(
            time_start=time_start, time_end=time_end
        )

        self.log.debug(f"topic_queries: {topic_queries}")

        for topic, topic_query_kwargs in topic_queries.items():
            assert (
                topic in self._topics
            ), f"Topic {topic} does not exists. Must be one of {self._topics}"
            topic_data = await self.efd_client.select_time_series(**topic_query_kwargs)
            topic_report = participant.parse_topic_data(
                topic_name=topic, topic_data=topic_data
            )
            participant_report.update(
                get_updated_report(participant_report, topic_report)
            )

        return participant_report

    async def get_command_data(
        self, command: str, time_start: Time, time_end: Time
    ) -> tuple[None | int, pandas.DataFrame]:
        """Get data from a command in the time window.

        Parameters
        ----------
        command : `str`
            Name of the command.
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.

        Returns
        -------
        command_seq_num : `int`
            Command sequence number.
        command_data : `pandas.DataFrame`
            Command data.
        """
        command_query = self._make_command_query(
            command=command,
            time_start=time_start,
            time_end=time_end,
        )
        command_data = await self.efd_client.influx_client.query(command_query)

        command_seq_num = (
            command_data.private_seqNum[0] if len(command_data) > 0 else None
        )

        return command_seq_num, command_data

    async def get_ackcmd_data(
        self,
        component_name: str,
        time_start: Time,
        time_end: Time,
        command_seq_num: int,
    ) -> pandas.DataFrame:
        """Get acknowledgements for a command in the time window.

        Parameters
        ----------
        command : `str`
            Name of the command.
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.
        command_seq_num : `int`
            Command sequence number.

        Returns
        -------
        `pandas.DataFrame`
            Acknowledgements data.
        """
        ackcmd_query = self._make_ackcmd_query(
            component_name=component_name,
            time_start=time_start,
            time_end=time_end,
            command_seq_num=command_seq_num,
        )

        return await self.efd_client.influx_client.query(ackcmd_query)

    def _make_command_query(
        self, command: str, time_start: Time, time_end: Time
    ) -> str:
        """Make an EFD query for a command that was sent between start and end
        time by the actor.

        Parameters
        ----------
        command : `str`
            Command name.
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.

        Returns
        -------
        `str`
            Query for the command.
        """
        return (
            f'SELECT * FROM "efd"."autogen"."{command}" '
            f"where time >= '{time_start.isot}Z' AND "
            f"time <= '{time_end.isot}Z' AND "
            f"private_origin = {self.actor.actor_private_origin}"
        )

    def _make_ackcmd_query(
        self,
        component_name: str,
        time_start: Time,
        time_end: Time,
        command_seq_num: int,
    ) -> str:
        """Make an EFD query for a command acknowledgement that was published
        by a component for a particular command (defined by command_seq_num)
        in a particular time window.

        Parameters
        ----------
        component_name : `str`
            Name of the component
        time_start : `Time`
            Time when activity evaluation starts.
        time_end : `Time`
            Time when activity evaluation ends.
        command_seq_num : `int`
            Command sequence number.

        Returns
        -------
        `str`
            Query for the acknowledgement.
        """
        return (
            f'SELECT * FROM "efd"."autogen"."lsst.sal.{component_name}.ackcmd" '
            f"where time >= '{time_start.isot}Z' AND "
            f"time <= '{time_end.isot}Z' AND "
            f"private_seqNum = {command_seq_num}"
        )

    async def get_topics_for(self, component: str) -> list[str]:
        """Get topics for a component from the list of topics.

        Parameters
        ----------
        component : `str`
            Name of the component.

        Returns
        -------
        `list`[ `str` ]
            List of topics for this component.
        """
        if not self._topics:
            self.log.debug("Topics not retrieved, retrieving...")
            await self._retrieve_all_topics()

        return [topic for topic in self._topics if f"lsst.sal.{component}." in topic]

    async def _retrieve_all_topics(self) -> None:
        """Retrieve all topics from the EFD instance and stores them in a local
        variable.
        """
        if self._topics:
            self.log.info("Topics already retrieved, overwriting.")
        self._topics = await self.efd_client.get_topics()

    @classmethod
    async def amain(cls) -> None:
        """Parse command line arguments and generate report."""

        log = logging.getLogger(__name__)
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.DEBUG)

        parser = cls.make_argument_parser()
        args = parser.parse_args()

        log.info(f"Actor: {args.actor} -> Participants: {args.participants}")

        report_generator = cls(actor=Actor.from_args(args), efd_name=args.efd_name)

        participants = Participant.from_args(args)

        time_start = Time(args.time_start)
        time_end = Time(args.time_end)

        report = await report_generator.generate_report(
            participants=participants,
            time_start=time_start,
            time_end=time_end,
        )

        if args.output is not None:
            log.info(f"Writing report to {args.output}")
            with open(args.output, "w") as fp:
                fp.write(report)
        else:
            print(report)

    @staticmethod
    def make_argument_parser() -> ArgumentParser:
        """Make command-line argument parser.

        Returns
        -------
        parser : `ArgumentParser`
            Argument parser.
        """

        parser = ArgumentParser(
            description="Generate UML diagrams from operations showing communications between components.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=r"""
            This script is intended to create UMl sequence diagrams showing the communication
            between components. The assumption is that there is an 'actor' component that is driving
            the operation and that there are a number of 'participant' components involved in the operation.

            The operation can be defined as a timestamp start/end:

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --participants ATAOS

            It is also possible to provide an event from the actor that tracks the start/end of the operation
            in that same time window.

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --participants ATAOS

            If the first mode, the diagram is generated for the entire time window. In the second mode, it
            will use the time from the first and last event sample in that time window.

            If an actor event is provided, the name of the event appears in the activity diagram. It is
            possible to provide an event attribute to be displayed as well:

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --actor-event-attribute state \
                --participants ATAOS

            And since some of these event attributes are enumerations, it is possible to provide the name of
            the enumeration and the import path:

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --actor-event-attribute state \
                --a-event-enum ScriptState \
                --actor-event-enum-import-path lsst.ts.idl.enums.Script \
                --participants ATAOS

            In this basic mode of operation it will generate a report with the commands sent from the actor
            to the participants and the acknowledgements received.

            Furthermore, it is also possible to provide a list of event names from the participants to
            include in the activity diagram.

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --actor-event-attribute state \
                --a-event-enum ScriptState \
                --actor-event-enum-import-path lsst.ts.idl.enums.Script \
                --participants ATAOS \
                --participants-events logevent_summaryState,logevent_configurationApplied

            Note we provided 2 events from the participant, separated by a comma. In this mode the name of
            the event is used to indicate the event was published. As with the actor we can specify an event
            attribute to display alongside the name:

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --actor-event-attribute state \
                --a-event-enum ScriptState \
                --actor-event-enum-import-path lsst.ts.idl.enums.Script \
                --participants ATAOS \
                --participants-events logevent_summaryState,logevent_configurationApplied \
                --participants-events-attributes summaryState:configurations,version

            Note that we use a colon to separate attributes from different events and comma to separate
            attributes from the individual events. It is also possible to add enumerations to translate the
            value of an event.

            $ generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --a-event logevent_state \
                --actor-event-attribute state \
                --a-event-enum ScriptState \
                --actor-event-enum-import-path lsst.ts.idl.enums.Script \
                --participants ATAOS \
                --participants-events logevent_summaryState,logevent_configurationApplied \
                --participants-events-attributes summaryState:configurations,version \
                --participants-events-attributes-enum State: \
                --participants-events-enum-import-path lsst.ts.salobj:

            Providing the enumeration follow the same format as that of the attributes, comma separates
            values for each attribute and colon separate values from events.
            """,
        )

        parser.add_argument(
            "--efd-name",
            required=True,
            help="Name of the EFD instance to query data from.",
        )

        parser.add_argument(
            "--time_start",
            required=True,
            help='Time when activity started. Format is "YYYY-MM-DDThh:mm:ss" (in UT).',
        )

        parser.add_argument(
            "--time_end",
            required=True,
            help="Time when activity ended. Same format as time_start.",
        )

        parser.add_argument(
            "-o",
            "--output",
            dest="output",
            help="File to write the results to. This is a text file with the UML sequence diagram. "
            "The file can be processed with plantuml to generate a png file.",
        )
        actor = parser.add_argument_group("actor")

        actor.add_argument(
            "--actor",
            dest="actor",
            required=True,
            help="Name of the component that is the main actor of the operation. "
            "This component will be used the reference to inspect which commands "
            "were sent to the participant components. "
            "If an indexed component, use the Name:index notation. "
            'You may have to wrap it with quotes, e.g. "Name:index".',
        )

        actor.add_argument(
            "--a-event",
            "--actor-event",
            dest="actor_event",
            help="Optional name of an event that defines the start/end of the operation.",
        )

        actor.add_argument(
            "--a-event-attribute",
            "--actor-event-attribute",
            dest="actor_event_attribute",
            help="Optional name of the event attribute to be displayed in the report.",
        )

        actor.add_argument(
            "--a-event-enum",
            "--actor-event-enum",
            dest="actor_event_enum",
            help="Name of the enumeration that represents the event attribute.",
        )

        actor.add_argument(
            "--actor-event-enum-import-path",
            dest="actor_event_enum_path",
            help="Import path of the enumeration that represents the event attribute, "
            'e.g.; "lsst.ts.idl.enums.Script".',
        )

        participants = parser.add_argument_group("participants")
        participants.add_argument(
            "--participants",
            nargs="*",
            required=True,
            help="Names of participants. If an indexed component, use the Name:index notation. "
            'You may have to wrap it with quotes, e.g. "Name:index".',
        )

        participants.add_argument(
            "--p-event",
            "--participants-events",
            dest="participants_events",
            help="Optional events from participants to test for."
            'Add events for each participant separated by colon ":" and multiple '
            'events separated by coma. For example: "logevent_summaryState,'
            'logevent_heartbeat:logevent_summaryState" adds summaryState and '
            "heartbeat for the first participant and only summaryState for the "
            "second.",
        )

        participants.add_argument(
            "--participants-events-attributes",
            dest="participants_events_attributes",
            help="Optional events attributes from participants events to display."
            'Add events attributes for each participant separated by colon ":", '
            'separate each event by semicolon ";" and multiple '
            'attributes separated by coma ",". For example: "summaryState,'
            'private_origin;:summaryState" adds summaryState and '
            "private_origin for logevent_summaryState and no attribute for logevent_heartbeat "
            "on the the first participant and add summaryState for logevent_summaryState "
            "on the second participant.",
        )

        participants.add_argument(
            "--participants-events-attributes-enum",
            dest="participants_events_attributes_enum",
            help="Name of the enumeration that represents the event attribute. "
            "Follow the same convention of participants-events-attributes.",
        )

        participants.add_argument(
            "--participants-events-enum-import-path",
            dest="participants_events_enum_path",
            help="Import path of the enumeration that represents the event attribute, "
            'e.g.; "lsst.ts.idl.enums.Script". '
            "Follow the same convention of participants-events-attributes.",
        )
        return parser


def generate_report() -> None:
    """Run report generator."""

    asyncio.run(ReportGenerator.amain())
