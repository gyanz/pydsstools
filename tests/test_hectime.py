import pytest
from pydsstools.core import HecTime

@pytest.mark.parametrize(
        "datetime_input,datetime_parsed",
        [
            ("1JUN1985 23:00:00", ("1JUN1985", "23:00:00")),
            ("1JUN1985 23:00:00 PM", ("1JUN1985", "23:00:00 PM")),
            ("2JUN85 10:00 P.M.", ("2JUN85", "10:00 P.M.")),
            ("JUN 1, 1985:24:00:00", ("JUN 1, 1985", "24:00:00")),
            ("JUN 1, 1985;23:00:00", ("JUN 1, 1985", "23:00:00")),
            ("JUN 1, 1985;23:00:10", ("JUN 1, 1985", "23:00:10")),
            ("JUN 1, 1985;23:59", ("JUN 1, 1985", "23:59")),
            ("1JUN1985 2300", ("1JUN1985", "2300")),
            ("2003-03-05T21:45:12Z", ("2003-03-05", "21:45:12Z")),
            ("  Undefined  ", ("", "")),
            ("JUN 1, 1985 9:30am", ("JUN 1, 1985", "9:30am")),
            ("JUN 1, 1985 930 AM", ("JUN 1, 1985", "930 AM")),
            ("JUN 1, 1985", ("JUN 1, 1985", "")),
            ("JUN 1, 1985:01:00", ("JUN 1, 1985", "01:00")),
            ("JUN 1, 1985:010000", ("JUN 1, 1985", "010000")),
            ("JUN 1, 1985.", ("JUN 1, 1985", "")),
            ("23JAN2003:0100", ("23JAN2003", "0100")),
            ("23JAN2003:010000", ("23JAN2003", "010000")),
            ("23JAN2003;010000", ("23JAN2003", "010000")),
        ],
)

def test_datetime_parser(datetime_input,datetime_parsed):
    assert HecTime.split_datetime(datetime_input) == datetime_parsed