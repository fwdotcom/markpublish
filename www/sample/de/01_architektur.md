# Einführung & Systemarchitektur

markpublish transformiert strukturierte Markdown-Dateien in publikationsreife Dokumente. Struktur, Metadaten und Designvorgaben werden zentral in `markpublish.yaml` definiert — alles andere ist reiner, wartbarer Text.

> [!NOTE]
> Die native Satz-Engine Typst übernimmt den präzisen Buchdruck-Satz, automatische Silbentrennung und konsistente Schriftartverwaltung ganz ohne externe LaTeX- oder Pandoc-Ketten.

## Modulare Gliederung
Dokumente können in Hauptteile (*Parts*), Kapitel und Trennseiten gegliedert werden. Jede Datei bleibt lesbarer Markdown-Text, während das Manifest die Gesamtreihe organisiert und die automatische Nummerierung steuert.

