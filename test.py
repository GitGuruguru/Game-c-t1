import pytest
from utils.Game_shop import Game_ShopEvent
from utils.Game_init import Game

def test_shop_event():
    assert Game_ShopEvent.draw_fill_window_shop()
