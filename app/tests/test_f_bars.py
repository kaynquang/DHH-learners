from learner import result


def test_f_bars_follow_the_scoring_cue():
    green, yellow, red = result.bars_html(-24.0), result.bars_html(-16.5), result.bars_html(-8.0)
    assert "#3E8E3A" in green and "#E0A100" in yellow and "#D9363E" in red      # below -18 dB, -18 to -15 dB, above -15 dB
    assert result.bars_html(None) == ""


def test_the_f_panel_shows_the_bars_and_nothing_for_s():
    res = result.Result("green", "Good", "✓", "m", "t", relamp_db=-22.0, closeness=0.9)
    assert "smile" in result.panel(res, "f") and "The f sound should be softer" in result.panel(res, "f")
    assert "The f sound should be softer" not in result.panel(res, "s")
