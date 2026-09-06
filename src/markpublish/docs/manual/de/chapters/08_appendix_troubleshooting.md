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

* markpublish liefert die hochwertige serifenlose Schriftfamilie **Open Sans** direkt im Paket mit.

* Das Standard-Theme greift automatisch auf diese Schrift zu. Sie müssen auf Ihrem Betriebssystem keine Schriften manuell nachinstallieren.

* Wenn Sie in eigenen Themes andere Schriften nutzen möchten, können Sie die Schriftdateien (`.ttf`, `.otf`) direkt im Ordner `pdf/fonts/` Ihres Themes ablegen oder auf dem System installieren. markpublish bindet Theme-Schriften automatisch in den Suchpfad ein.

---

## Häufig gestellte Fragen (FAQ)

### Wie verhindere ich eine Trennseite vor einem Kapitel?

Standardmäßig leitet ein Kapitel mit `break_before: "page"` ein, während Abschnitte (`parts:`) mit `break_before: "divider"` eine repräsentative Trennseite erzeugen. Wenn ein Kapitel oder Abschnitt direkt ohne neue Trennseite anschließen soll, setzen Sie:

```yaml
break_before: "none"
```

### Wie kann ich die Seitennummerierung für jedes Kapitel neu starten?

Setzen Sie in der `markpublish.yaml` auf Dokument- oder Kapitel-Ebene:

```yaml
pagenum_reset: true
```

markpublish setzt die Seitenzahl zu Beginn des Kapitels automatisch auf 1 zurück und berechnet die Gesamtzahl der Seiten konsistent.

### Werden Hyperlinks im PDF klickbar exportiert?

Ja. Sowohl interne Verweise (aus dem Inhaltsverzeichnis oder Fußnoten) als auch externe Weblinks (`[Webseite](https://example.com)`) werden als echte, anklickbare PDF-Hyperlinks erzeugt.
