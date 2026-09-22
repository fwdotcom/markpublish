# Grundlagen & Typografie

Ein professionelles Satzsystem zeichnet sich dadurch aus, dass es dem Verfasser die Bürde komplexer visueller Gestaltungsentscheidungen abnimmt, ohne dabei gestalterische Präzision zu opfern. **markpublish** schlägt die Brücke zwischen der leicht lesbaren und universellen Markdown-Auszeichnung auf der einen und der kompromisslosen typografischen Güte moderner Druckschriften auf der anderen Seite.

## Die Trennung von Form und Inhalt

In der modernen Technischen Dokumentation ist die strikte Entkopplung redaktioneller Inhalte von ihrer grafischen Repräsentation der entscheidende Faktor für langfristige Wartbarkeit. Wird Formatierungslogik in Fließtexte eingestreut, sinkt die Wiederverwendbarkeit drastisch und automatisierte Prüfprozesse werden erschwert[^1].

[^1]: Siehe dazu auch die Richtlinien zur digitalen Barrierefreiheit und strukturierten Informationsarchitektur nach DIN EN ISO 21801.

Typografische Systeme wie markpublish realisieren dieses Paradigma über zwei elementare Säulen:

1. **Semantische Quellen:** Autoren verfassen reine Markdown-Dokumente (`.md`), die ausschließlich semantische Strukturierungselemente wie Absätze, Listen, Zitate und Tabellen nutzen.
2. **Deklaratives Manifest:** Eine zentrale Konfigurationsdatei (`markpublish.yaml`) steuert globale Parameter wie Papierformat, Ränder, Schriftgrade, Kolumnentitel und die logische Reihenfolge der Kapitel.

> [!NOTE]
> Durch die Verlagerung aller gestalterischen Vorgaben in das Theme und das Manifest bleibt der eigentliche Fließtext vollkommen portabel. Derselbe Inhalt kann ohne Eingriff in den Text als internes Diskussionspapier, technisches Referenzhandbuch oder Web-Publikation gerendert werden.

## Mikrotypografie und Schriftsatz

Guter Schriftsatz zeichnet sich durch optische Ruhe und harmonische Grauwertverteilung aus. Das im Hintergrund agierende Typst-Backend berechnet Zeilenumbrüche nach fortschrittlichen dynamischen Optimierungsalgorithmen, die Hurenkinder und Schusterjungen zuverlässig unterbinden.

Wichtige Kernkonzepte der Satzarchitektur im Überblick:

AST (Abstract Syntax Tree)
: Die hierarchische Baumstruktur, in die das eingehende Markdown zunächst überführt wird, bevor die Umwandlung in native Typst-Befehle erfolgt.

Satzspiegel
: Das harmonische Verhältnis der bedruckten Fläche einer Seite zu den umgebenden Weißräumen (Rändern), berechnet nach klassischen buchgestalterischen Proportionen.

Kolumnentitel
: Kopfzeilen, die dem Leser auf geraden und ungeraden Seiten dynamisch das aktuelle Dokument, die Hauptgruppe oder die Kapitelüberschrift anzeigen.

> [!TIP]
> Die integrierte Schriftart `Open Sans` wird mit allen benötigten Schriftschnitten (Regular, Italic, SemiBold, Bold) direkt im Paket mitgeliefert. Dies garantiert eine absolut reproduzierbare Zeilen- und Seitenaufteilung auf jedem Zielsystem.

### Gestaltungsregeln für Überschriften

Überschriften dienen nicht nur der optischen Gliederung, sondern etablieren eine logische Navigationshierarchie. markpublish synchronisiert die Nummerierung aller Ebenen automatisch mit dem Hauptinhaltsverzeichnis und eventuellen Abschnittsverzeichnissen. Manuelle Ziffern im Markdown-Text sind daher weder notwendig noch empfohlen.

