# Einleitung

## Motivation und Zielsetzung

Markdown ist das führende Format für technische Dokumentationen, Notizen und Projektberichte. Seine Stärke liegt in der Einfachheit und Lesbarkeit im reinen Textformat. Sobald jedoch aus diesen Texten hochwertige, druckfertige Berichte, Handbücher oder Whitepapers entstehen sollen, stoßen herkömmliche Werkzeuge an ihre Grenzen. Häufig folgt ein zeitaufwendiger manueller Nachbearbeitungsschritt in Textverarbeitungs- oder Layoutprogrammen.

**markpublish** schließt diese Lücke: Es verwandelt strukturierte Markdown-Dateien über eine deklarative Konfiguration vollautomatisch in typografisch anspruchsvolle, professionell gestaltete PDF-Dokumente. 

Das Ziel von markpublish ist es, Entwicklern, technischen Redakteuren und Autoren einen nahtlosen Veröffentlichungsprozess zu bieten. Inhalte werden in einfachem Markdown verfasst, während markpublish die vollständige Kontrolle über Layout, Gliederung, Trennseiten, Nummerierung, Verzeichnisse und Typografie übernimmt.

## Kernfeatures

markpublish zeichnet sich durch einen klaren Fokus auf Dokumentenqualität, Geschwindigkeit und Verlässlichkeit aus:

* **Moderne Satzqualität durch Typst:** Durch die Verwendung der innovativen Satz-Engine Typst entstehen Dokumente mit herausragender typografischer Präzision, perfektem Randausgleich und ästhetischem Layout.
* **Extrem hohe Kompiliergeschwindigkeit:** Selbst umfangreiche Dokumente mit dutzenden Seiten, Abbildungen und Tabellen werden in rund ein bis zwei Sekunden vollständig gesetzt.
* **Einfache Installation und Portabilität:** Als reguläres Python-Paket lässt sich markpublish plattformübergreifend auf Windows, macOS und Linux ohne komplizierte Einrichtung betreiben.
* **Deklarative Projektkonfiguration:** Eine einzige Datei (`markpublish.yaml`) steuert das gesamte Dokument – von Metadaten über Gliederungsebenen bis hin zu Kopf- und Fußzeilen.
* **Mehrstufige Dokumentenarchitektur:** Unterstützung einer klaren Zweiteilung in übergeordnete Abschnitte (*Parts*) und inhaltstragende Kapitel (*Chapters*) mit flexibler Trennseiten-Steuerung.
* **Präzise Verzeichnisse und Nummerierung:** Vollautomatische Generierung von Gesamtinhaltsverzeichnissen, Abschnittsverzeichnissen und lokalen Kapitelverzeichnissen sowie flexibel konfigurierbare Kapitel- und Überschriftennummerierung.
* **Umfassende Markdown-Erweiterungen:** Standardmäßige Unterstützung von GitHub-konformen Hinweisboxen (Admonitions/Callouts), Tabellen, Definitionslisten, Fußnoten, Aufgabenlisten und Quellcode mit Syntax-Highlighting.
* **Kaskadierende Mehrsprachigkeit (i18n):** Integrierte Unterstützung für mehrsprachige Dokumente mit automatischer Spracherkennung und anpassbaren Beschriftungen.

## Architektur im Überblick

Die Arbeitsweise von markpublish folgt einer klaren Verarbeitungs-Pipeline:

```text
Eingaben:
  ├── Konfiguration    (markpublish.yaml)
  ├── Inhalte          (chapters/*.md)
  └── Layout           (templates/<theme>/)
           │
           ▼
  [ markpublish Pipeline ]
           │
           ▼
  [ Typst Satz-Engine ]
           │
           ▼
  [ Fertiges PDF-Dokument ]
```

1. **Konfigurations- und Dokumentenanalyse:** markpublish liest die `markpublish.yaml` ein, validiert sämtliche Einstellungen und baut die Gliederungshierarchie aus Abschnitten und Kapiteln auf.
2. **Inhaltsaufbereitung:** Die Markdown-Dateien der Kapitel werden eingelesen und strukturiert aufbereitet. Überschriften erhalten ihre exakte Nummerierung, Sprungmarken werden gesetzt und Verzeichniseinträge synchron erfasst.
3. **Template-Zusammenstellung:** Das gewählte Theme (standardmäßig das integrierte Standard-Theme) stellt die Layout-Vorgaben bereit. Metadaten, konfigurierte Kopf- und Fußzeilen, Trennseiten und Textinhalte werden präzise in die Typst-Umgebung übergeben.
4. **Kompilierung zum PDF:** Die Typst-Engine kompiliert das Gesamtdokument in einem einzigen, hocheffizienten Durchlauf direkt in die fertige PDF-Datei.
