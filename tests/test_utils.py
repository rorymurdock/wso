"""Automated testing for WSO Utils"""
from wso.utilities import Utils

UTILS = Utils()


def test_timezone():
    """Tests verifying timezone"""
    assert UTILS.check_timezone(57) is True
    assert UTILS.check_timezone(9999) is False
    assert UTILS.check_timezone("BAD") is False
    assert UTILS.check_timezone("") is False


def test_locales():
    """Tests verifying locales"""
    assert UTILS.check_locale("de") is True
    assert UTILS.check_locale("sv-FI") is True
    assert UTILS.check_locale("bad") is False
    assert UTILS.check_locale(123) is False
    assert UTILS.check_locale("") is False
