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

__all__ = ["Actor"]

import typing
from argparse import Namespace
from enum import Enum

import pandas
from astropy.time import Time
from lsst.ts.salobj import name_to_name_index

from .utils import get_enum_type

ActorType = typing.TypeVar("ActorType", bound="Actor")


class Actor:
    """Handles the actor logic of an operation.

    Parameters
    ----------
    name : `str`
        Name of the component.
    index : `int`, optional
        Index of the component.
    event : `str`, optional
        Name of the event that defines the start/end of the operation.
    attribute : `str`, optional
        Name of the event attribute with relevant information.
    enum : `Enum`, optional
        Enumeration that represents the event attribute.
    """

    def __init__(
        self,
        name: str,
        index: None | int = None,
        event: None | str = None,
        attribute: None | str = None,
        enum: None | typing.Type[Enum] = None,
    ) -> None:

        self.name = name
        self.index = index
        self.event = event
        self.attribute = attribute
        self.enum = enum

        self._private_origin: None | int = None

    @property
    def actor_private_origin(self) -> int:
        assert self._private_origin is not None
        return self._private_origin

    def generate_query_kwargs(self, time_start: Time, time_end: Time) -> None | dict:
        """Generate query to retrieve data for the actor.

        Parameters
        ----------
        time_start : `Time`
            Time when the activity starts.
        time_end : `Time`
            Time the activity ends.

        Returns
        -------
        None | `dict`
            EFD query to retrieve data.
        """
        if self.event is None:
            return None
        else:
            return dict(
                topic_name=f"lsst.sal.{self.name}.{self.event}",
                index=self.index,
                start=time_start,
                end=time_end,
                fields="*",
            )

    def parse_data(self, data: pandas.DataFrame) -> tuple[dict[Time, str], Time, Time]:
        """Parse data.

        Parameters
        ----------
        data : `pandas.DataFrame`
            _description_

        Returns
        -------
        `tuple`[ `dict`[`Time`, `str` ], `Time`, `Time` ]
            _description_
        """
        assert self.event is not None

        report: dict[Time, str] = dict()

        if self.attribute is None:
            for time in data.index:
                report[Time(time)] = f"<-- {self.name} : {self.event}"
        else:
            for time, attribute in zip(data.index, getattr(data, self.attribute)):
                report[
                    Time(time)
                ] = f"<-- {self.name} : {attribute if self.enum is None else self.enum(attribute).name}"

        self._private_origin = data.private_origin[0]

        return report, Time(data.index[0]), Time(data.index[-1])

    @classmethod
    def from_args(cls: typing.Type[ActorType], args: Namespace) -> ActorType:
        """Create an instance of actor from command line arguments.

        Parameters
        ----------
        args : `Namespace`
            Input arguments.

        Returns
        -------
        `Actor`
            New instance of Actor.
        """

        name, index = name_to_name_index(args.actor)

        return cls(
            name=name,
            index=index,
            event=args.actor_event,
            attribute=args.actor_event_attribute,
            enum=get_enum_type(
                import_path=args.actor_event_enum_path,
                enum_name=args.actor_event_enum,
            ),
        )
