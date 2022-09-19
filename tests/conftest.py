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
from lsst.ts.salobj import SalRetCode, State


@pytest.fixture
def sample_actor_data() -> pandas.DataFrame:
    index = [
        pandas.Timestamp("2022-09-14 08:00:36.090136+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:00:41.184647+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:04:07.507687+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:07:36.313930+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:07:36.314226+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:09:06.464684+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:09:06.468719+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:09:06.470368+0000", tz="UTC"),
    ]

    state = [1, 2, 2, 3, 3, 3, 7, 10]
    private_origin = [47370] * len(state)

    return pandas.DataFrame(
        index=index,
        data=zip(state, private_origin),
        columns=["state", "private_origin"],
    )


@pytest.fixture
def command() -> str:
    return "lsst.sal.ATAOS.command_offset"


@pytest.fixture
def command_data() -> pandas.DataFrame:

    index = [
        pandas.Timestamp("2022-09-14 08:09:06.000000+0000", tz="UTC"),
    ]

    data = range(len(index))

    return pandas.DataFrame(index=index, data=data, columns=["payload"])


@pytest.fixture
def ackcmd_data() -> pandas.DataFrame:

    index = [
        pandas.Timestamp("2022-09-14 08:09:07.000000+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:09:08.000000+0000", tz="UTC"),
        pandas.Timestamp("2022-09-14 08:09:10.000000+0000", tz="UTC"),
    ]

    ack = [
        SalRetCode.CMD_ACK.value,
        SalRetCode.CMD_INPROGRESS.value,
        SalRetCode.CMD_COMPLETE.value,
    ]

    result = ["", "command in progress", "command done"]

    return pandas.DataFrame(
        index=index, data=zip(ack, result), columns=["ack", "result"]
    )


@pytest.fixture
def expected_command_report() -> dict[Time, str]:
    return {
        Time(
            pandas.Timestamp("2022-09-14 08:09:06.000000+0000", tz="UTC")
        ): "Script -> ATAOS : command_offset\nactivate ATAOS",
        Time(
            pandas.Timestamp("2022-09-14 08:09:07.000000+0000", tz="UTC")
        ): "Script <- ATAOS: [CMD_ACK]::\\n",
        Time(
            pandas.Timestamp("2022-09-14 08:09:08.000000+0000", tz="UTC")
        ): "Script <- ATAOS: [CMD_INPROGRESS]::\\ncommand in progress",
        Time(
            pandas.Timestamp("2022-09-14 08:09:10.000000+0000", tz="UTC")
        ): "Script <- ATAOS: [CMD_COMPLETE]::\\ncommand done\ndeactivate ATAOS",
    }


@pytest.fixture
def topic_name() -> str:
    return "logevent_summaryState"


@pytest.fixture
def topic_data() -> pandas.DataFrame:

    index = [
        pandas.Timestamp("2022-09-14 08:09:09.000000+0000", tz="UTC"),
    ]

    summary_state = [
        State.FAULT.value,
    ]

    return pandas.DataFrame(index=index, data=summary_state, columns=["summaryState"])
