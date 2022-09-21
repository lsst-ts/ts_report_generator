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

__all__ = ["TopicDefinition"]

import typing
from dataclasses import dataclass
from enum import Enum

import pandas


@dataclass
class TopicDefinition:
    name: str
    attributes: None | dict[str, None | typing.Type[Enum]] = None

    def generate_report(self, data: pandas.DataFrame) -> str:
        """Generate report for input data.

        Parameters
        ----------
        data : `pandas.DataFrame`
            Input data

        Returns
        -------
        `str`
            Report
        """
        attributes = self.attributes if self.attributes is not None else dict()

        return ", ".join(
            [
                str(getattr(data, attribute)[0])
                if descriptor is None
                else descriptor(getattr(data, attribute)[0]).name
                for attribute, descriptor in attributes.items()
            ]
        )
