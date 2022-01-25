import pytest
from src.get_data import get_data

def test_broken_url():
    try :
        get_data(url='http://this-is-a-fake-url.com')
    except Exception:
        pass

def test_url():
    assert type(get_data()) is dict