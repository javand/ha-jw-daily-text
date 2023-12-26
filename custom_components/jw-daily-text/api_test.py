import pytest

from api import JWDailyTextApiClient

def test_ok():
    api = JWDailyTextApiClient().async_get_data()