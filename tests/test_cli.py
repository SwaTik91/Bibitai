from bibitai.cli import main


def test_help_exits_cleanly() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse help should exit")
