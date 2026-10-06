# Einleitung

## Motivation und Zielsetzung

Markdown ist das führende Format für technische Dokumentationen, Notizen und Projektberichte. Seine Stärke liegt in der Einfachheit und Lesbarkeit im reinen Textformat. Sobald jedoch aus diesen Texten hochwertige, druckfertige Berichte, Handbücher oder Whitepapers entstehen sollen, stoßen herkömmliche Werkzeuge an ihre Grenzen. Häufig folgt ein zeitaufwendiger manueller Nachbearbeitungsschritt in Textverarbeitungs- oder Layoutprogrammen.

**markpublish** schließt diese Lücke: Es verwandelt strukturierte Markdown-Dateien über eine einfache, aber mächtige Konfiguration vollautomatisch in typografisch anspruchsvolle, professionell gestaltete PDF-Dokumente.

Das Ziel von markpublish ist es, Entwicklern, technischen Redakteuren und Autoren einen nahtlosen Veröffentlichungsprozess zu bieten. Inhalte werden in einfachem Markdown verfasst, während markpublish die vollständige Kontrolle über Layout, Gliederung, Trennseiten, Nummerierung, Verzeichnisse und Typografie übernimmt.

## Kernfeatures

markpublish zeichnet sich durch einen klaren Fokus auf Dokumentenqualität, Geschwindigkeit und Verlässlichkeit aus:

* **Moderne Satzqualität durch Typst:** Die Satz-Engine Typst sorgt für typografische Präzision, perfekten Randausgleich und ein ästhetisches Layout.

* **Hohe Kompiliergeschwindigkeit:** Selbst umfangreiche Dokumente mit Dutzenden von Seiten, Abbildungen und Tabellen werden in rund ein bis zwei Sekunden vollständig gesetzt.

* **Einfache Installation und Portabilität:** Als reguläres Python-Paket lässt sich markpublish plattformübergreifend auf Windows, macOS und Linux ohne komplizierte Einrichtung betreiben.

* **Deklarative Konfiguration:** Eine einzige Datei (`markpublish.yaml`) steuert das gesamte Projekt.

* **Mehrstufige Dokumentenarchitektur:** Unterstützung einer klaren Zweiteilung in übergeordnete Abschnitte (*Parts*) und inhaltstragende Kapitel (*Chapters*) mit flexibler Trennseiten-Steuerung.

* **Präzise Verzeichnisse und Nummerierung:** Vollautomatische Generierung von Gesamtinhaltsverzeichnis, Abschnittsverzeichnissen und lokalen Kapitelverzeichnissen sowie flexibel konfigurierbare Kapitel- und Überschriftennummerierung.

* **Umfassende Markdown-Erweiterungen:** Standardmäßige Unterstützung von GitHub-konformen Hinweisboxen (Admonitions/Callouts), Tabellen, Definitionslisten, Fußnoten, Aufgabenlisten und Quellcode mit Syntax-Highlighting.

* **Kaskadierende Mehrsprachigkeit (i18n):** Mehrsprachige Dokumente und Themes (statische Texte wie Inhaltsverzeichnis, Kapitel, Seitenzahlen) über eine vierstufige Kaskade. Auch die Programmoberfläche (CLI) ist zweisprachig (Deutsch und Englisch) und folgt der Systemsprache.

## Architektur im Überblick

Die Arbeitsweise von markpublish folgt einer klaren Verarbeitungs-Pipeline:

1. **Konfigurations- und Dokumentenanalyse:** markpublish liest die Datei `markpublish.yaml` ein, validiert sämtliche Einstellungen und baut die Gliederungshierarchie aus Abschnitten und Kapiteln auf.

2. **Inhaltsaufbereitung:** Die Markdown-Dateien der Kapitel werden über eine Syntaxbaum-Pipeline (ElementTree AST) eingelesen und durch einen nativen Typst-Serializer (`TypstSerializer`) direkt in sauberes Typst-Markup überführt. Überschriften und Verzeichnisse werden auf AST-Ebene synchronisiert, Sprungmarken gesetzt und lokale Bildpfade automatisch für den Bau isoliert.

3. **Template-Zusammenstellung:** Das gewählte Theme (standardmäßig das integrierte Standard-Theme) stellt die Layout-Vorgaben bereit. Metadaten (gesammelt in einem typisierten `meta`-Wörterbuch), Kopf- und Fußzeilen, Trennseiten und Textinhalte werden präzise in die Typst-Umgebung übergeben.

4. **Kompilierung zum PDF:** Die Typst-Engine kompiliert das Gesamtdokument in einem einzigen, hocheffizienten Durchlauf direkt in die fertige PDF-Datei. Tritt ein Fehler auf, wird der generierte Typst-Code zur schnellen Diagnose in `.markpublish/last_failed_build.typ` abgelegt.

## Nutzung von KI bei der Softwareentwicklung

Bei der Entwicklung von markpublish wurden verschiedene KI-Modelle bewusst als Werkzeuge eingesetzt: beim Entwerfen und Schreiben von Code ebenso wie als Gesprächspartner für Architekturentscheidungen, für Anregungen zu Bedienung und Typografie und für gegenseitige Code-Reviews, bei denen ein Modell die Entwürfe eines anderen prüft. Das hat die Entwicklung beschleunigt und die Codequalität spürbar verbessert.

Die Grenzen waren ebenso deutlich: Fachlicher Kontext, die Richtung des Projekts und der letzte Feinschliff kommen nicht aus einem Sprachmodell. Jede Änderung wurde vom Autor geprüft, zusammengeführt und verantwortet.

markpublish selbst enthält keine KI-Funktionen. Alle Dokumente werden ausschließlich lokal auf Ihrem Rechner verarbeitet.
