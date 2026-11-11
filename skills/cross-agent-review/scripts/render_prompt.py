#!/usr/bin/env python3
"""Fill a cross-agent-review prompt template.

Usage:
  render_prompt.py <template> <output> KEY=VALUE [KEY=VALUE ...]

Replaces every `{{KEY}}` in the template with VALUE. Exits with status 1 and
names the keys when the template still contains an unfilled `{{...}}`, or when
a given key does not appear in the template.
"""

import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    template_path, output_path, *assignments = argv
    text = Path(template_path).read_text()

    values: dict[str, str] = {}
    for assignment in assignments:
        key, sep, value = assignment.partition("=")
        if not sep:
            print(f"expected KEY=VALUE, got {assignment!r}", file=sys.stderr)
            return 2
        values[key] = value

    used = set(PLACEHOLDER.findall(text))
    unused = sorted(set(values) - used)
    if unused:
        print(f"keys not in template: {', '.join(unused)}", file=sys.stderr)
        return 1

    rendered = PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)
    missing = sorted(set(PLACEHOLDER.findall(rendered)))
    if missing:
        print(f"unfilled placeholders: {', '.join(missing)}", file=sys.stderr)
        return 1

    Path(output_path).write_text(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
