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
from lsst.ts.report.generator.topic_definition import TopicDefinition
from lsst.ts.salobj import State


def test_topic_definition_generate_report(topic_data: pandas.DataFrame) -> None:

    topic_def = TopicDefinition(name="logevent_summaryState")

    report = topic_def.generate_report(topic_data)

    assert report == ""


def test_topic_definition_generate_report_attributes(
    topic_data: pandas.DataFrame,
) -> None:

    topic_def = TopicDefinition(
        name="logevent_summaryState", attributes={"summaryState": None}
    )

    report = topic_def.generate_report(topic_data)

    assert report == "3"


def test_topic_definition_generate_report_attributes_enum(
    topic_data: pandas.DataFrame,
) -> None:

    topic_def = TopicDefinition(
        name="logevent_summaryState", attributes={"summaryState": State}
    )

    report = topic_def.generate_report(topic_data)

    assert report == "FAULT"
