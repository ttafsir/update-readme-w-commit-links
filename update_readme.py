import re
import sys
import typing
from pathlib import Path

import git  # pip install GitPython

ROOT = Path(__file__).parent.resolve()
SECTION_REGEX = re.compile(r"<!-- index starts -->")
URL_ROOT_FMT = "https://github.com/{user}/{repo}/tree/{commit_sha}"


def find_section(find_regex: re.Pattern[str], lines: typing.Iterable[str]) -> int:
    """
    Return the index of the first line matching passed regex.
    """
    return next((i for i, line in enumerate(lines) if find_regex.search(line)), -1)


def parse_commit_message(commit: git.Commit) -> str:
    """Parse commit message and return commit message"""
    return commit.message.replace("commit: ", "").replace("commit (initial): ", "")


def build_list_item(commit: git.Commit, user: str, repo_name: str) -> str:
    """
    Return the URL for the commit
    """
    url = URL_ROOT_FMT.format(user=user, repo=repo_name, commit_sha=commit.newhexsha)
    list_item_label = parse_commit_message(commit)
    return f"* [{list_item_label}]({url})"


def get_updated_commits(
    readme_lines: typing.Iterable[str], git_log: git.RefLog, user: str, repo: str
) -> typing.List[str]:
    """
    Parse commit log and build hyperlinks in README
    """
    updates = [
        build_list_item(commit, user, repo)
        for commit in git_log
        if "commit" in commit.message
        and "[doc]" not in commit.message
        and "clone" not in commit.message
        and commit.newhexsha not in readme_lines
    ]
    return "\n".join(updates)


def main(user: str, repo_name: str) -> None:
    """
    Parse commit log and build hyperlinks in README
    """
    repo = git.Repo(ROOT)
    ref_log = repo.head.reference.log()

    # Read our current README.md
    readme = ROOT / "README.md"
    readme_lines = readme.open().readlines()

    # parse commit log
    updated_commits = get_updated_commits(readme_lines, ref_log, user, repo_name)

    # find the index of the section to update based on the regex
    section_start = find_section(SECTION_REGEX, readme_lines)
    if section_start == -1:
        raise sys.exit("Could not find section to update")

    # update the section with the new commits
    updated_readme_lines = (
        "".join(readme_lines[: section_start + 1]) + updated_commits.strip()
    )
    readme.write_text(updated_readme_lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Usage: update_readme.py <username> <repo>")
    main(user=sys.argv[1], repo_name=sys.argv[2])
