import re
from datetime import datetime

import pytest
import pytz
from testil import assert_raises

from slycache.key_generator import (KeyFormatException,
                                    StringFormatKeyGenerator, StringFormatter)

now = datetime.utcnow()
now_utc = now.astimezone(pytz.utc)
now_za = now.astimezone(pytz.timezone("Africa/Johannesburg"))


@pytest.mark.parametrize(
    "template,arg,result", [
        ("{arg}", "1", "1"),
        ("{arg}", 1, "1"),
        ("{arg}", now, now.isoformat()),
        ("{arg}", now_utc, now_utc.isoformat()),
        ("{arg}", now_za, now_utc.isoformat()),
        ("{arg}", now_za, now_utc.isoformat()),
        ("{arg:%Y-%m-%d}", now, now.strftime("%Y-%m-%d")),
        ("{arg!s}", now, str(now)),
    ]
)
def test_string_formatter(template, arg, result):
    assert StringFormatter().format(template, arg=arg) == result


def something_to_cache(arg1, arg2=None, *, kw_arg, kw_arg2=[]):
    pass


@pytest.mark.parametrize(
    "template,message", [
        (None, None),
        (1, ".*must be None or a string.*"),
        ("", ".*must not be empty.*"),
        ("{0}", "Automatic field numbering not supported. Use field names."),
        ("{}", ".*Blank field in key.*"),
        ("{kw_arg2}", "Mutable argument.*"),
    ]
)
def test_key_validation(template, message):
    if message is not None:
        with assert_raises(KeyFormatException, msg=re.compile(message)):
            StringFormatKeyGenerator.validate(template, something_to_cache)
    else:
        StringFormatKeyGenerator.validate(template, something_to_cache)
