from app.engines.wallpaper_math import roll_count

def test_short_wall():
    assert roll_count(4.0, 2.5, 0.53, 10.0, 0)["rolls"] >= 1
