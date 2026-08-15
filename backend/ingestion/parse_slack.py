from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Message header patterns
#
# We support two real forms observed in EnterpriseRAG-Bench:
#
# 1. With team:
#
#    maria (Support): Hello
#    tess_acme (Customer): Hello
#    alex (eng-runtime): Looking into this
#
# 2. Without team:
#
#    carmen: Agree on DLQ approach.
#    sarah_sales: FYI Atlas Retail POC...
#    incident-bot: Pager: HIGH...
#
# Important:
# - Backticks are intentionally NOT allowed in the author portion.
# - This prevents:
#
#       `tess_acme (Customer):`
#
#   inside message content from becoming a new message.
# ---------------------------------------------------------------------------

AUTHOR_TOKEN = r"[A-Za-z0-9_.@-]+"

AUTHOR_WITH_OPTIONAL_SPACES = (
    rf"{AUTHOR_TOKEN}(?:\s+{AUTHOR_TOKEN})*"
)

PAREN_MESSAGE_PATTERN = re.compile(
    rf"^(?P<author>{AUTHOR_WITH_OPTIONAL_SPACES})\s+"
    rf"\((?P<team>[A-Za-z0-9_.@-]+)\):\s*"
    rf"(?P<text>.*)$"
)

PLAIN_MESSAGE_PATTERN = re.compile(
    rf"^(?P<author>{AUTHOR_TOKEN}):\s+"
    rf"(?P<text>.*)$"
)


# ---------------------------------------------------------------------------
# Some lines in the dataset can look like prose containing a colon.
#
# We use conservative heuristics for plain "author:" headers.
# Parenthesized "author (team):" headers are much stronger evidence.
# ---------------------------------------------------------------------------

PLAIN_AUTHOR_BLOCKLIST = {
    "http",
    "https",
    "curl",
    "note",
    "notes",
    "example",
    "status",
    "impact",
    "problem",
    "action",
    "actions",
    "steps",
    "plan",
    "plan-a",
    "plan-b",
    "result",
    "response",
}


@dataclass
class ParserStats:
    documents: int = 0
    messages: int = 0
    parenthesized_headers: int = 0
    plain_headers: int = 0
    continuation_lines: int = 0
    fenced_code_blocks: int = 0
    errors: int = 0


def clean_text(text: str) -> str:
    """
    Normalize trailing whitespace while preserving message content.
    """
    return text.rstrip()


def is_valid_author(author: str) -> bool:
    """
    Validate a candidate author.

    We intentionally reject backticks because dataset content can contain
    lines such as:

        `tess_acme (Customer):` sure ...

    which are message content, not message headers.
    """

    author = author.strip()

    if not author:
        return False

    if len(author) > 80:
        return False

    if "`" in author:
        return False

    if ":" in author:
        return False

    return True


def is_valid_team(team: str) -> bool:
    """
    Validate an optional team identifier.
    """

    team = team.strip()

    if not team:
        return False

    if len(team) > 80:
        return False

    if "`" in team:
        return False

    if ":" in team:
        return False

    return True


def looks_like_plain_message_header(
    line: str,
) -> bool:
    """
    Decide whether a line in the plain:

        author: message

    format is likely to be a real message header.

    This is deliberately conservative.
    """

    match = PLAIN_MESSAGE_PATTERN.match(line)

    if not match:
        return False

    author = match.group("author").strip()
    text = match.group("text")

    if not is_valid_author(author):
        return False

    if author.lower() in PLAIN_AUTHOR_BLOCKLIST:
        return False

    # Plain authors in this dataset are generally compact identifiers.
    # This avoids interpreting ordinary prose like:
    #
    #   Customer impact: ...
    #
    # as a new speaker.
    if " " in author:
        return False

    # Avoid treating things like URLs or shell-ish content as speakers.
    if "/" in author:
        return False

    if not text.strip():
        return False

    return True


def parse_message_header(
    line: str,
) -> tuple[str, str | None, str] | None:
    """
    Return:
        (author, team, text)

    or None when the line is not a valid message header.
    """

    # -----------------------------------------------------------------------
    # Strong form:
    #
    #   author (team): message
    # -----------------------------------------------------------------------

    match = PAREN_MESSAGE_PATTERN.match(line)

    if match:
        author = match.group("author").strip()
        team = match.group("team").strip()
        text = match.group("text")

        if (
            is_valid_author(author)
            and is_valid_team(team)
        ):
            return (
                author,
                team,
                text,
            )

        return None

    # -----------------------------------------------------------------------
    # Plain form:
    #
    #   author: message
    # -----------------------------------------------------------------------

    if looks_like_plain_message_header(line):
        match = PLAIN_MESSAGE_PATTERN.match(line)

        if match:
            return (
                match.group("author").strip(),
                None,
                match.group("text"),
            )

    return None


def parse_slack_file(
    file_path: str | Path,
    stats: ParserStats | None = None,
) -> dict[str, Any]:
    """
    Parse one EnterpriseRAG-Bench Slack document.

    Structure:

        channel

        author (team): message

        author: message

    Multiline content is preserved.

    Fenced code blocks are treated as message content and are never parsed
    as message headers.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Not a file: {path}"
        )

    content = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = content.splitlines()

    # Remove blank lines before channel.
    while lines and not lines[0].strip():
        lines.pop(0)

    # Remove trailing blank lines.
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return {
            "document_id": path.stem,
            "source": "slack",
            "channel": None,
            "messages": [],
            "message_count": 0,
        }

    # First non-empty line is the channel.
    channel = lines[0].strip()

    messages: list[dict[str, Any]] = []

    current_message: dict[str, Any] | None = None

    inside_code_block = False

    for line in lines[1:]:

        # -------------------------------------------------------------------
        # Code fence handling.
        #
        # We keep the code block exactly inside the current message and
        # never attempt to interpret its lines as Slack headers.
        # -------------------------------------------------------------------

        if line.strip().startswith("```"):
            if current_message is not None:
                current_message["text"] += (
                    "\n" + line.rstrip()
                )

            if line.strip().startswith("```"):
                inside_code_block = not inside_code_block

                if (
                    inside_code_block
                    and stats is not None
                ):
                    stats.fenced_code_blocks += 1

            continue

        if inside_code_block:
            if current_message is not None:
                current_message["text"] += (
                    "\n" + line.rstrip()
                )

                if stats is not None:
                    stats.continuation_lines += 1

            continue

        # -------------------------------------------------------------------
        # Blank lines.
        # -------------------------------------------------------------------

        if not line.strip():
            if current_message is not None:
                current_message["text"] += "\n"

                if stats is not None:
                    stats.continuation_lines += 1

            continue

        # -------------------------------------------------------------------
        # Try to identify a new Slack message.
        # -------------------------------------------------------------------

        header = parse_message_header(line)

        if header is not None:
            author, team, message_text = header

            if current_message is not None:
                current_message["text"] = (
                    current_message["text"].strip()
                )

                messages.append(current_message)

            current_message = {
                "author": author,
                "team": team,
                "text": clean_text(message_text),
            }

            if stats is not None:
                if (
                    PAREN_MESSAGE_PATTERN.match(line)
                    is not None
                ):
                    stats.parenthesized_headers += 1
                else:
                    stats.plain_headers += 1

            continue

        # -------------------------------------------------------------------
        # Everything else is continuation content.
        # -------------------------------------------------------------------

        if current_message is not None:
            current_message["text"] += (
                "\n" + line.rstrip()
            )

            if stats is not None:
                stats.continuation_lines += 1

    # -----------------------------------------------------------------------
    # Save final message.
    # -----------------------------------------------------------------------

    if current_message is not None:
        current_message["text"] = (
            current_message["text"].strip()
        )

        messages.append(current_message)

    if stats is not None:
        stats.messages += len(messages)

    return {
        "document_id": path.stem,
        "source": "slack",
        "channel": channel,
        "messages": messages,
        "message_count": len(messages),
    }


def parse_all_slack_files(
    input_dir: Path,
    output_file: Path,
) -> None:
    """
    Parse all Slack files into JSONL.
    """

    files = sorted(
        input_dir.glob("*.txt")
    )

    if not files:
        raise FileNotFoundError(
            f"No .txt files found in: {input_dir}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    stats = ParserStats()

    success_count = 0
    error_count = 0

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as output:

        for index, file_path in enumerate(
            files,
            start=1,
        ):
            try:
                parsed = parse_slack_file(
                    file_path,
                    stats,
                )

                output.write(
                    json.dumps(
                        parsed,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                success_count += 1
                stats.documents += 1

            except Exception as exc:
                error_count += 1
                stats.errors += 1

                print(
                    f"[ERROR] {file_path.name}: {exc}"
                )

            if (
                index % 500 == 0
                or index == len(files)
            ):
                print(
                    f"Processed {index}/{len(files)} files | "
                    f"success={success_count} | "
                    f"errors={error_count} | "
                    f"messages={stats.messages}"
                )

    print()
    print("=" * 70)
    print("PARSER COMPLETE")
    print("=" * 70)

    print(
        f"Documents processed:       {stats.documents}"
    )

    print(
        f"Successful documents:      {success_count}"
    )

    print(
        f"Failed documents:          {error_count}"
    )

    print(
        f"Messages parsed:           {stats.messages}"
    )

    print(
        f"Parenthesized headers:     "
        f"{stats.parenthesized_headers}"
    )

    print(
        f"Plain headers:             "
        f"{stats.plain_headers}"
    )

    print(
        f"Continuation lines:        "
        f"{stats.continuation_lines}"
    )

    print(
        f"Fenced code blocks:        "
        f"{stats.fenced_code_blocks}"
    )

    print(
        f"Output:                    {output_file}"
    )


def main() -> None:
    # Project structure:
    #
    # deptrace/
    #   backend/
    #     ingestion/
    #       parse_slack.py
    #
    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    input_dir = (
        project_root
        / "data"
        / "enterprise-rag"
        / "slack"
    )

    output_file = (
        project_root
        / "data"
        / "enterprise-rag"
        / "parsed"
        / "slack.jsonl"
    )

    print("=" * 70)
    print("EnterpriseRAG-Bench Slack Parser")
    print("=" * 70)

    print(
        f"Input : {input_dir}"
    )

    print(
        f"Output: {output_file}"
    )

    print()

    parse_all_slack_files(
        input_dir=input_dir,
        output_file=output_file,
    )


if __name__ == "__main__":
    main()