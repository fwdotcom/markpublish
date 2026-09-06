# Projektkonfiguration mit markpublish.yaml

Die zentrale Steuerungsdatei eines jeden markpublish-Projekts ist die Datei `markpublish.yaml`. Sie definiert das Dokument deklarativ: Metadaten, Layout-Vorgaben, Gliederung und die Zuordnung der Markdown-Dateien zu Kapiteln und Abschnitten.

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

Metadaten
: Titel, Untertitel, Autoren, Version, Datum, Sprache, Status und Copyright-Hinweise.

Layout-Schalter
: Anzeige des Deckblatts (`cover`), Aktivierung von Kopfzeilen (`header`) und Fußzeilen (`footer`).

Globale Verzeichnisvorgaben
: Steuerung der Tiefe für das Gesamt-Inhaltsverzeichnis (`document_toc`), Abschnittsverzeichnisse (`part_toc`) und lokale Kapitelverzeichnisse (`chapter_toc`).

> [!IMPORTANT] Keine Wahrheitswerte bei Verzeichnisschaltern
> Die Schalter `document_toc`, `part_toc` und `chapter_toc` akzeptieren **keine** Booleans (`true` oder `false`). Verwenden Sie `"full"` (volle Tiefe), `"none"` (kein Verzeichnis) oder eine positive Zahl ab `1` für die maximale Gliederungstiefe (z. B. `2`). Ein notiertes `document_toc: false` bricht die Validierung mit einer deutlichen Meldung ab.

Nummerierungsregeln
: Vorgaben zur automatischen Nummerierung von Überschriften (`autonum_style`, `autonum_from_level`, `autonum_prefix`).

#### Eigene Metadatenfelder

Unter `document:` sind über die bekannten Schlüssel hinaus **beliebige eigene Felder** erlaubt. Sie erreichen das Theme, werden aber nicht von selbst gedruckt:

```yaml
document:
  title: "Projektbericht"
  abteilung: "Controlling"
  kunde: "Musterunternehmen GmbH"
  freigegeben: true
```

Das Metadatenraster des Deckblatts zeigt ausschließlich die Angaben, die das verwendete Theme dafür vorsieht – im mitgelieferten Standard-Theme sind das Version, Datum, Autor, Copyright und Status. Ein eigenes Feld kommt erst dazu, wenn das Theme es ausdrücklich aufführt (siehe Kapitel *Templates und Mehrsprachigkeit*).

> [!NOTE] Warum nicht automatisch?
> Würde jedes freie Feld ungefragt auf dem Deckblatt landen, stünde dort auch jeder Tippfehler: Aus `abteilnug: "Controlling"` würde eine zusätzliche Zeile, die niemand angeordnet hat. So bleibt das Titelblatt die Entscheidung des Themes.

Drei Dinge sind dabei zu wissen:

* **Ungenutzte Felder meldet `markpublish labels`.** Ein Feld, das kein Theme abholt, erscheint dort mit dem Befund *ungenutzt* und am Fuß der Ausgabe noch einmal gesammelt – genau hier fällt auch ein vertippter Schlüssel auf. Ein Blick dorthin vor dem ersten Bauen erspart die Suche.

* **Die Beschriftung kommt aus der i18n-Kaskade.** Sobald ein Theme das Feld druckt, braucht es dazu einen Text; findet sich keiner, druckt das Deckblatt den Schlüssel selbst – also `abteilung` statt `Abteilung`. Legen Sie dafür eine `i18n.yaml` neben Ihre `markpublish.yaml`:

  ```yaml
  # i18n.yaml, im Projektverzeichnis
  de:
    abteilung: "Abteilung"
    kunde: "Kunde"
    freigegeben: "Freigegeben"
  ```

  Diese Datei ist die letzte Stufe der Kaskade und gewinnt damit gegen Programm und Theme (siehe Kapitel *Templates und Mehrsprachigkeit*).

* **Der Typ bleibt erhalten.** Ein `true` ist ein Wahrheitswert und kein Text: Das Deckblatt setzt `Ja` beziehungsweise `Yes`, je nach Dokumentsprache. Die beiden Wörter stehen als `bool_true` und `bool_false` in der i18n-Kaskade.

### Parts (Abschnitte)

Ein Dokument wird durch `parts:` in übergeordnete Abschnitte gegliedert (z. B. „Hauptteil“, „Fallstudien“, „Anhänge“):

* Ein Dokument muss immer über `parts:` aufgebaut sein; ein flaches `chapters:` direkt auf oberster Ebene wird abgewiesen.

* Ein Abschnitt fasst logisch zusammengehörige Kapitel zusammen.

* Ohne Angabe tritt ein Abschnitt selbst nicht in Erscheinung (`break_before: "none"`): er klammert seine Kapitel und vererbt seine Einstellungen, belegt aber keine Seite und erscheint nicht im Inhaltsverzeichnis. Mit `break_before: "divider"` erhält er eine gestaltete Trennseite, mit `break_before: "page"` eine Überschrift auf einer neuen Seite.

* Auf Abschnittsebene gesetzte Einstellungen (z. B. Verzeichnistiefe oder Nummerierungspräfixe wie `autonum_prefix: "A."`) vererben sich automatisch auf alle darin enthaltenen Kapitel.

* Auf `parts:` sind ausschließlich die deklarierten Konfigurationsschlüssel erlaubt. Unbekannte Schlüssel (wie `break_befor`) werden mit Ähnlichkeitsvorschlägen abgelehnt, um unbemerkte Fehlkonfigurationen auszuschließen.

### Chapters (Kapitel)

Die Liste `chapters:` innerhalb eines Abschnitts verweist auf die eigentlichen Markdown-Inhaltsdateien:

* Jedes Kapitel verweist auf seine Markdown-Datei (`file:`). Autoren können in ihren Markdown-Dateien ganz natürlich mit einer `#`-Überschrift beginnen.

* Über **`show_title:`** (`true` oder `false`, Standard: `true`) lässt sich steuern, ob die `#`-Überschrift der Markdown-Datei auf der Inhaltsseite gerendert werden soll. Wird vor dem Kapitel eine Trennseite erzeugt (`break_before: "divider"`), kann mit `show_title: false` verhindert werden, dass der Titel auf der Folgeseite doppelt erscheint – die Inhaltsseite beginnt dann direkt mit dem Fließtext oder der ersten Zwischenüberschrift.

* Über die optionalen Schlüssel **`toc_title:`** (für Inhaltsverzeichnisse und Kopfzeilen) und **`divider_title:`** (für Trennseiten) können gezielt abweichende Titel vergeben werden (z. B. eine prägnante Kurzform im Inhaltsverzeichnis gegenüber einer ausführlichen Überschrift auf der Textseite). Fehlen die Schlüssel, erben beide automatisch die `#`-Überschrift der Datei.

* Soll eine Trennseite erzeugt werden (`break_before: "divider"`) oder das Kapitel im Inhaltsverzeichnis gelistet werden, muss mindestens eine `#`-Überschrift oder der entsprechende Titelschlüssel (`divider_title` / `toc_title`) vorhanden sein, andernfalls bricht der Build mit einer klaren Fehlermeldung ab.

* Kapitel können über das Feld `break_before` steuern, ob vor ihnen eine Trennseite erzeugt wird, ein einfacher Seitenwechsel erfolgt oder der Text nahtlos anschließt.

* **Verschachtelte Unterkapitel:** Ein Kapitel kann über das Feld `chapters:` weitere Unterkapitel aufnehmen. Diese werden rekursiv aufgebaut und genauso strikt gegen Schreibfehler geprüft wie die Hauptebene. Unterkapitel erben Einstellungen (wie Nummerierungspräfixe) nach unten.


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
        break_before: "page"

      - file: "chapters/02_analyse.md"
        # Kurzform für das Inhaltsverzeichnis bei langer Datei-H1:
        toc_title: "Marktanalyse"
        break_before: "page"

      - file: "chapters/03_ergebnisse.md"
        break_before: "divider"

  - part: "Anhänge"
    break_before: "divider"
    autonum_from_level: 2
    autonum_prefix: "A."
    chapters:
      - file: "chapters/anhang_tabellen.md"

      - file: "chapters/anhang_glossar.md"
```

Eine vollständige Übersicht aller verfügbaren Schlüssel, Datentypen, Standardwerte und Kombinationsmöglichkeiten für jede der drei Ebenen finden Sie in **Anhang A: Schema-Referenz markpublish.yaml** am Ende dieses Handbuchs.
