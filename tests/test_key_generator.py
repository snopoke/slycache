import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_UP

import pytest
import pytz
from testil import assert_raises

from slycache.exceptions import KeyFormatException
from slycache.key_generator import StringFormatKeyGenerator, StringFormatter

now = datetime.utcnow()
now_utc = now.replace(tzinfo=pytz.utc)
now_za = now_utc.astimezone(pytz.timezone("Africa/Johannesburg"))

uuid_ = uuid.uuid4()

fixed_now = datetime.strptime("2021-03-05T22:09:00", "%Y-%m-%dT%H:%M:%S")
fixed_za = fixed_now.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Africa/Johannesburg"))


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
        ("{arg}", timedelta(days=1), "86400.0"),
        ("{arg}", now_utc.date(), now.date().isoformat()),
        ("{arg}", now.time(), now.time().isoformat()),
        ("{arg}", None, "None"),
        ("{arg}", Decimal(1.3245), str(Decimal(1.3245))),
        ("{arg}", 1.3245, "1.3245"),
        ("{arg}", uuid_, str(uuid_)),
        ("{arg}", [1, 2, 3], "oB7aMuTgsTkydOkdGz6ez8XquoU"),
        ("{arg}", {
            "a": [{"1", "2"}]
        }, "ADlpGhBMmmSh_aHiL0uUPSqdcUU"),
        ("{arg}", {4, 1, 3.1459}, "r0-avm04sP26OTBMUPiQMwPgyjs"),
        (
            "{arg}", {
                "uuid": uuid.UUID(hex="829b1eedacfd48c1b7ace88da1e1f895"),
                "decimal mole": Decimal(6.02214076).quantize(Decimal('0.00000000'), rounding=ROUND_UP),
                "set": {1, 2, 3},
                "naive_datetime": fixed_now,
                "datetime": fixed_za,
                "float root 2": 1.41421,
                "None": None,
                "timedelta": timedelta.max
            }, "FH6LoXCXF_CWnVnntvy7XWV142E"
        ),
    ]
)
def test_string_formatter(template, arg, result):
    assert StringFormatter().format(template, arg=arg) == result


@pytest.mark.parametrize("arg", [object(), StringFormatter()])
def test_string_errors(arg):
    with assert_raises(ValueError):
        assert StringFormatter().format("{arg}", arg=arg)


def something_to_cache(arg1, arg2=None, *args, kw_arg, kw_arg2=[], **kwargs):  # pylint: disable=all
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
            StringFormatKeyGenerator().validate(template, something_to_cache)
    else:
        StringFormatKeyGenerator().validate(template, something_to_cache)


@pytest.mark.parametrize(
    "template,call_args,expected", [
        ("{arg1}{arg2}", {
            "arg1": 1,
            "arg2": 2
        }, "ns:12"),
        ("{arg1}{arg2}", {
            "arg1": "a" * 100,
            "arg2": "b" * 200
        }, "ns:sQLZhus_7FcO9A_VTGuH5oFjV7g"),
    ]
)
def test_key_formatting(template, call_args, expected):
    key = StringFormatKeyGenerator().generate("ns", template, something_to_cache, call_args)
    assert key == expected
