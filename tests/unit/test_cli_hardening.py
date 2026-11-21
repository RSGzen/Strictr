from __future__ import annotations

import pytest

import strictr.cli as cli

pytestmark = pytest.mark.spec("003")


@pytest.mark.ac("AC-1")
def test_keyboard_interrupt_exits_130(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupt(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_configure_stdio", lambda: None)
    monkeypatch.setattr(cli, "run_check", interrupt)

    code = cli.main(["check"])

    captured = capsys.readouterr()
    assert code == 130
    assert "interrupted" in captured.err
    assert captured.out == ""
