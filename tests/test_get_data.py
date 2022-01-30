import pytest
from src.get_data import get_data, get_player_hist
import asyncio

#%% Get data function
def test_broken_url():
    try :
        get_data(url='http://this-is-a-fake-url.com')
    except Exception:
        pass


def test_type():
    assert type(get_data(save_to_file=False)) is dict


def test__id_type():
   for id in get_data(save_to_file=False).keys():
        assert type(id) is int


def test_returned_cols():
    data = get_data(save_to_file=False)
    for id in data.keys():
        assert len(data[id].keys()) is 66


#%% get Player hist (GPH) function
@pytest.mark.asyncio
async def test_gph_no_inp():
    try:
        await asyncio.run(get_player_hist(save_to_file=False))
        assert False
    except TypeError:
        pass

@pytest.mark.skip
@pytest.mark.asyncio
async def test_gph_id_type():
    try:
        await asyncio.run(get_player_hist(save_to_file=False))
        assert False
    except TypeError:
        pass
