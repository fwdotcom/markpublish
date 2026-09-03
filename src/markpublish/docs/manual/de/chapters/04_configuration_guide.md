# Projektkonfiguration mit markpublish.yaml

Die zentrale Steuerungsdatei eines jeden markpublish-Projekts ist die `markpublish.yaml`. Sie definiert das Dokument deklarativ: Metadaten, Layout-Vorgaben, Gliederung und die Zuordnung der Markdown-Dateien zu Kapiteln und Abschnitten.

## Die drei Strukturebenen

markpublish organisiert Dokumente in drei klar voneinander abgegrenzten Ebenen:

```text
document
└── parts (Abschnitte)
    └── chapters (Kapitel)
        └── [Unterkapitel in chapters]
```

### Document (Dokumentebene)

Die oberste Ebene `document:` beschreibt das Gesamtdokument:
* **Metadaten:** Titel, Untertitel, Autoren, Version, Datum, Sprache, Status und Copyright-Hinweise.
* **Layout-Schalter:** Anzeige des Deckblatts (`cover`), Aktivierung von Kopfzeilen (`header`) und Fußzeilen (`footer`).
* **Globale Verzeichnisvorgaben:** Steuerung der Tiefe für das Gesamt-Inhaltsverzeichnis (`document_toc`), Abschnittsverzeichnisse (`part_toc`) und lokale Kapitelverzeichnisse (`chapter_toc`).
* **Nummerierungsregeln:** Vorgaben zur automatischen Nummerierung von Überschriften (`autonum_style`, `autonum_from_level`, `autonum_prefix`).

#### Eigene Metadatenfelder

Unter `document:` sind über die bekannten Schlüssel hinaus **beliebige eigene Felder** erlaubt. Sie erscheinen ohne weiteres Zutun im Metadatenraster des Deckblatts:

```yaml
document:
  title: "Projektbericht"
  abteilung: "Controlling"
  kunde: "Musterunternehmen GmbH"
  freigegeben: true
```

Drei Dinge sind dabei zu wissen:

* **Die Beschriftung kommt aus der i18n-Kaskade.** Findet sich dort kein Eintrag für den Schlüssel, druckt das Deckblatt den Schlüssel selbst — also `abteilung` statt `Abteilung`. Legen Sie dafür eine `i18n.yaml` neben Ihre `markpublish.yaml`:

  ```yaml
  # i18n.yaml, im Projektverzeichnis
  de:
    abteilung: "Abteilung"
    kunde: "Kunde"
    freigegeben: "Freigegeben"
  ```

  Diese Datei ist die letzte Stufe der Kaskade und gewinnt damit gegen Programm und Theme (siehe Kapitel *Template- und Designsystem*).
* **Der Typ bleibt erhalten.** Ein `true` ist ein Wahrheitswert und kein Text: das Deckblatt setzt `Ja` beziehungsweise `Yes`, je nach Dokumentsprache. Die beiden Wörter stehen als `bool_true` und `bool_false` in der i18n-Kaskade.
* **Ein Tippfehler wird gedruckt, nicht gemeldet.** `titel:` statt `title:` ergibt kein Fehlerbild, sondern eine zusätzliche Zeile auf dem Deckblatt. `markpublish labels` zeigt jedes Feld mit seinem Befund an — ein Blick dorthin vor dem ersten Bauen erspart die Suche.

### Parts (Abschnitte)

Ein Dokument wird durch `parts:` in übergeordnete Abschnitte gegliedert (z. B. „Hauptteil“, „Fallstudien“, „Anhänge“). 
* Ein Abschnitt fasst logisch zusammengehörige Kapitel zusammen.
* Abschnitte können mit Trennseiten (`break_before: "divider"`) oder einfachen Seitenumbrüchen (`break_before: "page"`) eingeleitet werden.
* Auf Abschnittsebene gesetzte Einstellungen (z. B. Verzeichnistiefe oder Nummerierungspräfixe wie `autonum_prefix: "A."`) vererben sich automatisch auf alle darin enthaltenen Kapitel.

### Chapters (Kapitel)

Die Liste `chapters:` innerhalb eines Abschnitts verweist auf die eigentlichen Markdown-Inhaltsdateien:
* Jedes Kapitel besitzt einen Verweis auf die Markdown-Datei (`file:`), optional einen Bezeichner in der YAML (`chapter:`) sowie eine optionale Kurzbeschreibung (`summary:`).
* Kapitel können über das Feld `break_before` steuern, ob vor ihnen eine Trennseite erzeugt wird, ein einfacher Seitenwechsel erfolgt oder der Text nahtlos anschließt.
* Kapitel können untereinander angeordnet werden; die inhaltliche Nummerierungs- und Gliederungstiefe (1.1, 1.1.1) entsteht dabei ausschließlich aus den Überschriftenebenen (H2, H3) innerhalb der Markdown-Dateien.

---

## Beispiel einer vollständigen Konfiguration

Das folgende Beispiel zeigt eine praxisnahe, vollständige `markpublish.yaml`:

```yaml
# markpublish.yaml

document:
  title: "Projektbericht Jahresabschluss"
  subtitle: "Analyse, Ergebnisse und Ausblick"
  summary: "Umfassender Gesamtbericht über die Projektphasen des vergangenen Geschäftsjahres."
  author: "Projektgruppe Controlling"
  date: "auto"
  version: "1.2.0"
  language: "de"
  copyright: "© 2026 Musterunternehmen GmbH"

  # Layout-Elemente
  cover: true
  header: true
  footer: true

  # Verzeichnistiefen
  document_toc: 2
  part_toc: 2
  chapter_toc: "none"

  # Nummerierung
  autonum_style: "decimal"
  autonum_from_level: 1

theme: "default"

parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "chapters/01_einleitung.md"
        chapter: "Einleitung und Projektziele"
        break_before: "page"

      - file: "chapters/02_analyse.md"
        chapter: "Marktanalyse und Vorgehen"
        break_before: "page"

      - file: "chapters/03_ergebnisse.md"
        chapter: "Zentrale Ergebnisse"
        break_before: "divider"

  - part: "Anhänge"
    break_before: "divider"
    autonum_from_level: 2
    autonum_prefix: "A."
    chapters:
      - file: "chapters/anhang_tabellen.md"
        chapter: "Detailtabellen"

      - file: "chapters/anhang_glossar.md"
        chapter: "Glossar"
```

Eine vollständige Übersicht aller verfügbaren Schlüssel, Datentypen, Standardwerte und Kombinationsmöglichkeiten für jede der drei Ebenen finden Sie in **Anhang A: Schema-Referenz markpublish.yaml** am Ende dieses Handbuchs.
