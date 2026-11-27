from __future__ import annotations

from pathlib import Path

import pytest

from strictr.core.discovery import discover
from strictr.core.models import CheckContext, DiscoveryResult
from strictr.tiers.ast_tier import AstTier

pytestmark = pytest.mark.spec("004")

SYNTAX_ERROR = "def broken(:\n    pass\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path.resolve()
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(root)
    return root


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available")


def diagnostic_paths(result: DiscoveryResult) -> list[str]:
    context = CheckContext(root=result.root, targets=result.targets, files=result.files)
    tier = AstTier().run(context)
    assert tier.status == "fail"
    return [diagnostic.path for diagnostic in tier.diagnostics]


@pytest.mark.ac("AC-2")
@pytest.mark.parametrize("suffix", [".py", ".pyi"])
def test_in_root_symlink_uses_link_path(project: Path, suffix: str) -> None:
    real = write(project / f"real{suffix}", SYNTAX_ERROR)
    link = project / f"link{suffix}"
    make_symlink(link, Path(real.name))

    result = discover()

    assert result.targets == (".",)
    assert result.files == (link, real)
    assert diagnostic_paths(result) == [f"link{suffix}", f"real{suffix}"]


@pytest.mark.ac("AC-2")
def test_explicit_symlink_target_uses_link_path(project: Path) -> None:
    real = write(project / "src" / "real.py", SYNTAX_ERROR)
    link = project / "src" / "link.py"
    make_symlink(link, Path(real.name))

    result = discover(("src/link.py",))

    assert result.targets == ("src/link.py",)
    assert result.files == (link,)
    assert diagnostic_paths(result) == ["src/link.py"]
