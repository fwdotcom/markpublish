# Anhang B: Fehlerbehebung und FAQ

Dieser Anhang bietet konkrete Hilfestellungen bei typischen Problemen während des Veröffentlichungsprozesses sowie Antworten auf häufige Fragen.

## Diagnose von Kompilierungsfehlern

Sollte ein Kompiliervorgang mit einer Fehlermeldung der Typst-Engine abbrechen, speichert markpublish den vollständig generierten Typst-Quellcode automatisch im aktuellen Arbeitsverzeichnis:

```text
.markpublish/last_failed_build.typ
```

### Vorgehen zur Fehleranalyse

1. Öffnen Sie die Datei `.markpublish/last_failed_build.typ` in einem beliebigen Texteditor.

2. Suchen Sie nach dem in der Fehlermeldung genannten Begriff, Variablennamen oder Textfragment.

3. Anhand des umgebenden Kontexts lässt sich unmittelbar erkennen, welches Markdown-Kapitel oder welcher Formatierungsblock die Ursache war.

---

## Häufige Ursachen und Lösungen

### Bilder oder Grafiken werden nicht gefunden

**Problem:** Typst bricht mit einer Meldung wie `image not found` ab.

**Lösung:**

* Pfade zu Abbildungen im Markdown (z. B. `![Diagramm](images/architektur.png)`) werden immer **relativ zur jeweiligen Markdown-Datei** aufgelöst.

* Liegt die Datei `01_kapitel.md` im Ordner `chapters/`, muss der Ordner `images/` entweder in `chapters/images/` liegen oder als `../images/architektur.png` referenziert werden.

* markpublish kopiert lokale Bilddateien während des Builds automatisch in den internen Build-Ordner.

### Ungültige Einrückungen in der Konfiguration (YAML)

**Problem:** markpublish meldet beim Start `Configuration error: mapping values are not allowed here` oder `YAML parsing error`.

**Lösung:**

* YAML reagiert strikt auf falsche Einrückungen. Verwenden Sie für Einrückungen stets **zwei Leerzeichen** und niemals Tabulatoren.

* Achten Sie darauf, dass Listeneinträge (`-`) und verschachtelte Schlüssel bündig zueinander stehen.

### Anpassung statischer Textbeschriftungen (i18n)

**Problem:** Ein generierter Text (wie „Inhaltsverzeichnis“ oder „Kapitel“) soll umformuliert werden oder fehlt in einer neuen Sprache.

**Lösung:**

* Führen Sie `markpublish labels` aus, um alle aufgelösten Textvariablen und deren Herkunftsebene anzuzeigen.

* Ergänzen oder überschreiben Sie die gewünschten Schlüssel entweder direkt in einer projektlokalen `i18n.yaml` (im Ordner neben der `markpublish.yaml`) oder in der `i18n.yaml` Ihres Themes.

### Schriften und Schriftfamilien

**Problem:** Fehlermeldungen bezüglich Schriftarten oder unerwartetes Schriftbild.

**Lösung:**

* Das Standard-Theme nutzt die mitgelieferte Schriftfamilie **Open Sans**; eine manuelle Schriftinstallation auf dem Betriebssystem ist nicht erforderlich.
* Für eigene Themes können Sie Schriftdateien (`.ttf`, `.otf`) direkt im Ordner `pdf/fonts/` Ihres Themes ablegen. markpublish bindet Theme-Schriften automatisch in den Suchpfad ein.

### Fehlendes Metadatum (UndefinedMetadataError)

**Problem:** Der Build bricht mit der Meldung `Metadatum '...' wird vom Theme gelesen, ist im Dokument aber nicht gesetzt` ab.

**Lösung:**

* Das Theme greift per `meta.at("schluessel")` auf ein Metadatum zu, das in der `markpublish.yaml` unter `document:` nicht definiert ist und im Theme keinen Fallback besitzt.
* Tragen Sie das fehlende Feld unter `document:` in Ihrer `markpublish.yaml` ein (freie Felder sind dort uneingeschränkt zulässig), oder hinterlegen Sie im Theme einen Standardwert: `meta.at("schluessel", default: (value: none)).value`.

### Fehlende Textbeschriftung (UndefinedLabelError)

**Problem:** Der Build bricht mit der Meldung `Label '...' ist im Template notiert, aber in keiner i18n-Ebene definiert` ab.

**Lösung:**

* Das Template greift über `labels.at("...")` auf einen Textbaustein zu, der in keiner Datei der Beschriftungskaskade für die aktive Dokumentsprache hinterlegt ist.
* Ergänzen Sie den Schlüssel unter dem entsprechenden Sprachkürzel (z. B. `de:`) in einer `i18n.yaml` direkt in Ihrem Projektordner oder im Theme.

### Theme-Signatur passt nicht (Theme-Signaturfehler)

**Problem:** `markpublish labels` oder der Build melden `Theme und Aufruf passen nicht zusammen`.

**Lösung:**

* Die Typst-Funktion `setup-document` in `template.typ` deklariert nicht alle erforderlichen Parameter.
* markpublish übergibt alle Metadaten gesammelt über das Wörterbuch `meta: (:)`. Stellen Sie sicher, dass Ihr Theme diesen Parameter deklariert: `#let setup-document(..., meta: (:), labels: (:), body) = { ... }` (oder `..rest` akzeptiert).

### Abweisung unbekannter Schlüssel (unknown_key)

**Problem:** markpublish bricht mit einer Meldung wie `chapters kennt diesen Schlüssel nicht: 'break_befor' -- meinten Sie 'break_before'?` ab.

**Lösung:**

* Auf Abschnitts- (`parts:`) und Kapitel-Ebene (`chapters:`) weist markpublish unbekannte Schlüssel strikt zurück, um Tippfehler frühzeitig abzufangen. Prüfen Sie den genannten Schlüssel; eigene freie Datenfelder sind ausschließlich unter `document:` zulässig.

### Zielordner bei init ist nicht leer

**Problem:** `markpublish init` bricht mit der Meldung `Das Verzeichnis ... besteht bereits und ist nicht leer` ab.

**Lösung:**

* `init` überschreibt niemals vorhandene Dateien. Wählen Sie einen neuen Verzeichnisnamen oder leeren Sie das Verzeichnis vor der Initialisierung.

---

## Häufig gestellte Fragen (FAQ)

### Was ist der Unterschied zwischen Benutzeroberflächensprache und Dokumentsprache?

markpublish trennt die Sprache der Programmoberfläche strikt von der Sprache des Dokuments:

* **Programmoberfläche (`--ui-lang`, `MARKPUBLISH_UI_LANG`):** Steuert, in welcher Sprache Fehlermeldungen, Hilfetexte und Diagnoseausgaben im Terminal erscheinen (`de` oder `en`). Ohne Angabe gilt die Sprache des Betriebssystems.
* **Dokumentsprache (`language:` in `markpublish.yaml`):** Bestimmt Typografie, Silbentrennung, Datumsformat und feste Texte (wie „Inhaltsverzeichnis“ oder „Kapitel“) im PDF. Ein deutsches Terminal kann somit problemlos ein englisches PDF erzeugen.

### Wie verhindere ich eine Trennseite vor einem Kapitel?

Standardmäßig leitet ein Kapitel mit `break_before: "page"` auf einer neuen Seite ein. Soll ein Kapitel direkt ohne Seitenwechsel anschließen, setzen Sie in der Kapiteldefinition `break_before: "none"`.

### Warum erscheint mein Abschnitt nirgends im Dokument?

Abschnitte (`parts:`) stehen standardmäßig auf `break_before: "none"`: Sie klammern Kapitel, belegen keine eigene Seite und erscheinen nicht im Inhaltsverzeichnis. Soll der Abschnitt sichtbar werden, notieren Sie:

```yaml
parts:
  - part: "Anhänge"
    break_before: "divider"   # gestaltete Trennseite
```

Mit `break_before: "page"` erhält der Abschnitt eine Überschrift auf einer neuen Seite statt einer Trennseite.

### Wie kann ich die Seitennummerierung für jedes Kapitel neu starten?

Setzen Sie in der `markpublish.yaml` auf Dokument- oder Kapitel-Ebene `pagenum_reset: true`. markpublish setzt die Seitenzahl zu Kapitelbeginn automatisch auf 1 zurück und berechnet die Gesamtzahl der Seiten konsistent.

### Werden Hyperlinks im PDF klickbar exportiert?

Ja. Sowohl interne Verweise (aus dem Inhaltsverzeichnis oder Fußnoten) als auch externe Weblinks (im Markdown als `[Linktext](URL)` notiert) werden im PDF als echte, anklickbare Hyperlinks erzeugt.


