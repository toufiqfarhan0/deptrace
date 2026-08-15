from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MESSAGE_PATTERN = re.compile(
    r"^(?P<author>[^()\n]+?)\s+\((?P<team>[^()\n]+)\):\s*(?P<text>.*)$"
)


def parse_slack_file(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    content = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = content.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

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

    channel = lines[0].strip()

    messages: list[dict[str, Any]] = []
    current_message: dict[str, Any] | None = None

    for line in lines[1:]:
        if not line.strip():
            if current_message is not None:
                current_message["text"] += "\n"
            continue

        match = MESSAGE_PATTERN.match(line)

        if match:
            if current_message is not None:
                current_message["text"] = current_message["text"].strip()
                messages.append(current_message)

            current_message = {
                "author": match.group("author").strip(),
                "team": match.group("team").strip(),
                "text": match.group("text").rstrip(),
            }

        else:
            if current_message is not None:
                current_message["text"] += "\n" + line.rstrip()

    if current_message is not None:
        current_message["text"] = current_message["text"].strip()
        messages.append(current_message)

    return {
        "document_id": path.stem,
        "source": "slack",
        "channel": channel,
        "messages": messages,
        "message_count": len(messages),
    }


def parse_all_slack_files(input_dir: Path, output_file: Path) -> None:
    files = sorted(input_dir.glob("*.txt"))

    if not files:
        raise FileNotFoundError(
            f"No .txt files found in: {input_dir}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    success_count = 0
    error_count = 0

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as output:

        for index, file_path in enumerate(files, start=1):
            try:
                parsed = parse_slack_file(file_path)

                output.write(
                    json.dumps(
                        parsed,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                success_count += 1

            except Exception as exc:
                error_count += 1

                print(
                    f"[ERROR] {file_path.name}: {exc}"
                )

            if index % 500 == 0 or index == len(files):
                print(
                    f"Processed {index}/{len(files)} files | "
                    f"success={success_count} | "
                    f"errors={error_count}"
                )

    print("\nFinished.")
    print(f"Successful documents: {success_count}")
    print(f"Failed documents:     {error_count}")
    print(f"Output:               {output_file}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]

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

    parse_all_slack_files(
        input_dir=input_dir,
        output_file=output_file,
    )