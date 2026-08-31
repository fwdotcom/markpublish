"""
GitHub-style callout alerts extension for Python-Markdown.
Transforms:
    > [!NOTE]
    > Body text...
into PyMdown / Python-Markdown admonition syntax:
    !!! note "Hinweis"
        Body text...
Die sprachabhaengigen Standardtitel stehen in markpublish.i18n.LABELS
(Schluessel alert_note, alert_tip, ...).
"""

from __future__ import annotations

import re
from typing import List, Mapping, Optional

from markdown import Extension
from markdown.preprocessors import Preprocessor

from markpublish.i18n import get_labels

GITHUB_ALERT_HEADER_RE = re.compile(
    r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s+(.*))?$',
    re.IGNORECASE
)


class GitHubAlertsPreprocessor(Preprocessor):
    """Converts GitHub-style blockquote alerts to standard admonition blocks."""

    def __init__(self, md, language: str = "de", labels: Optional[Mapping[str, str]] = None):
        super().__init__(md)
        self.language = language or "de"
        # Die aufgeloeste Kaskade, sofern der Aufrufer sie kennt. Ohne sie
        # bleiben nur die Programmtexte - dann koennte ein Theme zwar
        # alert_note setzen, im Callout stuende aber weiter "Hinweis".
        self.labels = labels

    def run(self, lines: List[str]) -> List[str]:
        # Die Alert-Titel stehen in derselben Tabelle wie alle uebrigen
        # statischen Texte - eine Stelle pro Sprache statt zwei.
        labels = self.labels if self.labels else get_labels(self.language)

        new_lines: List[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            match = GITHUB_ALERT_HEADER_RE.match(line)
            if match:
                alert_type = match.group(1).lower()
                custom_title = match.group(2)
                default_title = labels.get(f"alert_{alert_type}", alert_type.capitalize())
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
            # Default bewusst {} und nicht None: Extension.setConfig() jagt
            # einen None-Default durch parseBoolValue() und macht aus der
            # Label-Tabelle einen Wahrheitswert.
            "labels": [{}, "Resolved label cascade; falls back to the program defaults"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        lang = self.getConfig("language", "de")
        labels = self.getConfig("labels", {})
        # Prioritaet unter 25: fenced_code / superfences laufen bei 25 und
        # ersetzen Code-Bloecke vorher durch Platzhalter. Bei einer hoeheren
        # Prioritaet wuerde ein dokumentiertes "> [!NOTE]" INNERHALB eines
        # Code-Blocks mit umgeschrieben.
        md.preprocessors.register(
            GitHubAlertsPreprocessor(md, language=lang, labels=labels), "github_alerts", 24
        )
