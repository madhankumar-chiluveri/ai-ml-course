"""
0.4 — Git and GitHub: the parts that matter for a portfolio.

Runnable: `python 04_git_and_github.py`
Requires: git on PATH.

SAFE: everything happens in a throwaway directory under the system temp
folder. This script never touches your real repositories.

What this proves practically:
  1. merge produces a diamond history; rebase produces a straight line.
  2. Deleting a secret and committing does NOT remove it from history —
     the old blob is still fetchable. Demonstrated, not asserted.
  3. git-filter-repo style rewriting changes every downstream commit hash.
  4. `git log --oneline --graph` is how you actually read history.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SEP = "=" * 70
FAKE_SECRET = "sk-live-DEMO0000NOTAREALKEY0000"


def git(*args: str, cwd: Path, check: bool = True) -> str:
    """Run a git command and return stdout."""
    r = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip()


def write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def init_repo(root: Path) -> None:
    git("init", "-q", "-b", "main", cwd=root)
    # Identity is repo-local, so this cannot affect your global config.
    git("config", "user.email", "demo@example.com", cwd=root)
    git("config", "user.name", "Demo", cwd=root)


# ====================================================================== 1
def demo_merge_vs_rebase(base: Path) -> None:
    print(SEP)
    print("DEMO 1 — merge vs rebase: the SAME work, two different histories")
    print(SEP)

    for mode in ("merge", "rebase"):
        root = base / f"demo-{mode}"
        root.mkdir()
        init_repo(root)

        write(root / "app.py", "print('v1')\n")
        git("add", ".", cwd=root)
        git("commit", "-q", "-m", "feat: initial app", cwd=root)

        # Branch off, then let main move on — this is what creates the
        # divergence that merge and rebase resolve differently.
        git("checkout", "-q", "-b", "feature", cwd=root)
        write(root / "feature.py", "print('feature')\n")
        git("add", ".", cwd=root)
        git("commit", "-q", "-m", "feat: add feature", cwd=root)

        git("checkout", "-q", "main", cwd=root)
        write(root / "README.md", "# Demo\n")
        git("add", ".", cwd=root)
        git("commit", "-q", "-m", "docs: add readme", cwd=root)

        if mode == "merge":
            # --no-ff forces a merge commit so the diamond is visible.
            git("merge", "--no-ff", "-q", "feature", "-m", "merge: feature", cwd=root)
        else:
            git("checkout", "-q", "feature", cwd=root)
            git("rebase", "-q", "main", cwd=root)
            git("checkout", "-q", "main", cwd=root)
            git("merge", "-q", "--ff-only", "feature", cwd=root)

        graph = git("log", "--oneline", "--graph", "--all", cwd=root)
        n_commits = len(git("log", "--oneline", cwd=root).splitlines())
        print(f"\n  --- {mode.upper()} ({n_commits} commits on main) ---")
        for line in graph.splitlines():
            print(f"    {line}")

    print("\n  merge  : preserves the true shape, adds a merge commit (diamond)")
    print("  rebase : replays commits onto main -> linear, readable, but the")
    print("           commit HASHES change. Never rebase a branch others pulled.")


# ====================================================================== 2
def demo_secret_persists(base: Path) -> None:
    print(SEP)
    print("DEMO 2 — deleting a secret does NOT remove it from history")
    print(SEP)

    root = base / "demo-secret"
    root.mkdir()
    init_repo(root)

    # Commit 1: the mistake.
    write(root / "config.py", f'API_KEY = "{FAKE_SECRET}"\n')
    git("add", ".", cwd=root)
    git("commit", "-q", "-m", "feat: add config", cwd=root)
    leak_sha = git("rev-parse", "HEAD", cwd=root)

    # Commits 2-3: normal work on top.
    write(root / "app.py", "print('hello')\n")
    git("add", ".", cwd=root)
    git("commit", "-q", "-m", "feat: app", cwd=root)

    # Commit 4: "fixing" it the way most people first try.
    write(root / "config.py", 'import os\nAPI_KEY = os.environ["API_KEY"]\n')
    git("add", ".", cwd=root)
    git("commit", "-q", "-m", "fix: read key from env", cwd=root)

    print(f"  working tree now clean? secret in config.py: "
          f"{FAKE_SECRET in (root / 'config.py').read_text()}")

    # THE POINT: search all of history, not just the working tree.
    found = git("log", "--all", "-S", FAKE_SECRET, "--oneline", cwd=root)
    print(f"  commits still containing the secret (git log -S):")
    for line in found.splitlines():
        print(f"    {line}")

    # And it is directly retrievable from the old blob.
    old = git("show", f"{leak_sha}:config.py", cwd=root)
    print(f"\n  git show {leak_sha[:8]}:config.py")
    print(f"    -> {old.strip()}")
    print(f"  SECRET STILL FETCHABLE: {FAKE_SECRET in old}")
    print("\n  ^ The file looks clean. The key is one command away for anyone")
    print("    who clones the repo. Step 1 is ROTATE THE KEY; rewriting")
    print("    history afterwards is cleanup, not remediation.")


# ====================================================================== 3
def demo_rewrite_changes_hashes(base: Path) -> None:
    print(SEP)
    print("DEMO 3 — rewriting history changes every downstream hash")
    print(SEP)

    root = base / "demo-rewrite"
    root.mkdir()
    init_repo(root)

    for i, msg in enumerate(["feat: one", "feat: two", "feat: three"], 1):
        write(root / f"f{i}.txt", f"file {i}\n")
        git("add", ".", cwd=root)
        git("commit", "-q", "-m", msg, cwd=root)

    before = git("log", "--format=%h %s", cwd=root).splitlines()

    # Amend the OLDEST commit's message via a soft reset + recommit. This is
    # what an interactive rebase or filter-repo does under the hood.
    root_sha = git("rev-list", "--max-parents=0", "HEAD", cwd=root)
    git("checkout", "-q", root_sha, cwd=root)
    git("commit", "-q", "--amend", "-m", "feat: one (reworded)", cwd=root)
    new_root = git("rev-parse", "HEAD", cwd=root)
    git("rebase", "-q", "--onto", new_root, root_sha, "main", cwd=root)
    git("checkout", "-q", "-B", "main", cwd=root)

    after = git("log", "--format=%h %s", cwd=root).splitlines()

    print("  BEFORE                        AFTER")
    for b, a in zip(reversed(before), reversed(after)):
        mark = "  <- changed" if b.split()[0] != a.split()[0] else ""
        print(f"    {b:<28} {a}{mark}")
    print("\n  ^ Editing the OLDEST commit changed the hash of EVERY commit")
    print("    after it. That is why force-push is required, and why")
    print("    --force-with-lease (not --force) is the safe form.")


def main() -> None:
    if shutil.which("git") is None:
        print("git is not on PATH. Install git and re-run.")
        sys.exit(1)

    print(f"git version: {subprocess.run(['git','--version'],capture_output=True,text=True).stdout.strip()}")

    base = Path(tempfile.mkdtemp(prefix="git-demo-"))
    print(f"scratch dir: {base}  (safe — nothing here is yours)")
    try:
        demo_merge_vs_rebase(base)
        demo_secret_persists(base)
        demo_rewrite_changes_hashes(base)
        print(SEP)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        print(f"cleaned up {base}")


if __name__ == "__main__":
    main()
