"""
GitHub-style callout alerts extension for Python-Markdown.
Transforms:
    > [!NOTE]
    > Body text...
into PyMdown / Python-Markdown admonition syntax:
    !!! note "Hinweis"
        Body text...
with language-aware default titles (de: Hinweis/Tipp/Wichtig/Warnung/Achtung, en: Note/Tip/Important/Warning/Caution).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from markdown import Extension
from markdown.preprocessors import Preprocessor


GITHUB_ALERT_HEADER_RE = re.compile(
    r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s+(.*))?$',
    re.IGNORECASE
)

DEFAULT_TITLES: Dict[str, Dict[str, str]] = {
    "de": {
        "note": "Hinweis",
        "tip": "Tipp",
        "important": "Wichtig",
        "warning": "Warnung",
        "caution": "Achtung",
    },
    "en": {
        "note": "Note",
        "tip": "Tip",
        "important": "Important",
        "warning": "Warning",
        "caution": "Caution",
    },
}


class GitHubAlertsPreprocessor(Preprocessor):
    """Converts GitHub-style blockquote alerts to standard admonition blocks."""

    def __init__(self, md, language: str = "de"):
        super().__init__(md)
        self.language = language or "de"

    def run(self, lines: List[str]) -> List[str]:
        lang_key = "de" if self.language.lower().startswith("de") else "en"
        titles_map = DEFAULT_TITLES.get(lang_key, DEFAULT_TITLES["en"])

        new_lines: List[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            match = GITHUB_ALERT_HEADER_RE.match(line)
            if match:
                alert_type = match.group(1).lower()
                custom_title = match.group(2)
                default_title = titles_map.get(alert_type, alert_type.capitalize())
                title = custom_title.strip() if custom_title else default_title

                # Start admonition header
                new_lines.append(f'!!! {alert_type} "{title}"')
                i += 1

                # Gather subsequent blockquote lines belonging to this alert
                while i < n:
                    sub_line = lines[i]
                    # If another alert begins, stop this alert
                    if GITHUB_ALERT_HEADER_RE.match(sub_line):
                        break

                    if sub_line.startswith('>'):
                        content = sub_line[1:]
                        if content.startswith(' '):
                            content = content[1:]
                        new_lines.append(f'    {content}')
                        i += 1
                    else:
                        break
            else:
                new_lines.append(line)
                i += 1

        return new_lines


class GitHubAlertsExtension(Extension):
    """Extension that enables GitHub-style callouts (> [!NOTE], > [!TIP], etc.)."""

    def __init__(self, **kwargs):
        self.config = {
            "language": ["de", "Language for default alert titles ('de' or 'en')"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        lang = self.getConfig("language", "de")
        md.preprocessors.register(GitHubAlertsPreprocessor(md, language=lang), "github_alerts", 27)
