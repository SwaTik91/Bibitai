from bibitai.cli import main, run_offline_paper
from bibitai.config import load_default_config


def test_help_exits_cleanly() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse help should exit")


def test_offline_paper_fills_without_an_exchange() -> None:
    ticks = run_offline_paper(load_default_config(), bars=180)
    assert len(ticks) == 180
    assert ticks[-1]["fills"] > 0
    assert ticks[-1]["real_orders"] is False
