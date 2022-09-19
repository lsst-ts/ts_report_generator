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

from lsst.ts.report.generator.utils import get_updated_report


def test_get_updated_report() -> None:

    report_data = dict(a="some text", b="some other text")

    new_report_data = dict(b="some new text for b", c="new report entry")

    updated_report = get_updated_report(report_data, new_report_data)

    assert "a" not in updated_report
    assert updated_report["b"] == f"{report_data['b']}\n{new_report_data['b']}"
    assert updated_report["c"] == new_report_data["c"]
