import re
from datetime import datetime

import pytest
import pytz
from testil import assert_raises

from slycache.exceptions import KeyFormatException
from slycache.key_generator import (StringFormatKeyGenerator, StringFormatter)

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
        ("{arg}", None, "None"),
        ("{arg}", [1, 2, 3], "wGbQFovqHUXHDnWT5Gj1LkQdoEk"),
        ("{arg}", {"a": [{"1", "2"}]}, "rRzL3lu24Aw9yPWB2lN52NOF3WQ"),
        ("{arg}", {"a", 1, 3.1459}, "Q_L5025a8laXSaZRviVAlsd-j84"),
    ]
)
def test_string_formatter(template, arg, result):
    assert StringFormatter().format(template, arg=arg) == result


def something_to_cache(arg1, arg2=None, *args, kw_arg, kw_arg2=[], **kwargs):
    pass


@pytest.mark.parametrize(
    "template,message", [
        (None, None),
        (1, ".*must be None or a string.*"),
        ("", ".*must not be empty.*"),
        ("{0}", "Field numbering not supported. Use field names."),
        ("{}", ".*Blank field in key.*"),
        ("{kw_arg2}", "Mutable argument.*"),
        ("{other_kwarg}", ".*not present in function.*"),
    ]
)
def test_key_validation(template, message):
    if message is not None:
        with assert_raises(KeyFormatException, msg=re.compile(message)):
            StringFormatKeyGenerator.validate(template, something_to_cache)
    else:
        StringFormatKeyGenerator.validate(template, something_to_cache)


@pytest.mark.parametrize(
    "template,call_args,expected", [
        ("{arg1}{arg2}", {"arg1": 1, "arg2": 2}, "ns:12"),
        ("{arg1}{arg2}", {"arg1": "a" * 100, "arg2": "b" * 200}, "ns:sQLZhus_7FcO9A_VTGuH5oFjV7g"),
    ]
)
def test_key_formatting(template, call_args, expected):
    key = StringFormatKeyGenerator.generate("ns", template, something_to_cache, call_args)
    assert key == expected
