# Besondere Markdown-Features

markpublish unterstützt den vollen Funktionsumfang des modernen CommonMark- und GitHub Flavored Markdown-Standards. Grundlegende Elemente wie Überschriften, Absätze, Textauszeichnungen (*kursiv*, **fett**), Tabellen, Aufzählungen, Quellcode-Blöcke und Weblinks funktionieren exakt wie gewohnt.

Dieses Kapitel konzentriert sich ausschließlich auf die darüber hinausgehenden Spezialfeatures und typografischen Erweiterungen von markpublish.

---

## Hinweisboxen (Admonitions und Callouts)

Zur optischen Hervorhebung wichtiger Passagen unterstützt markpublish GitHub-konforme Callout-Blöcke. 

### Syntax

```markdown
> [!NOTE]
> Dies ist ein allgemeiner Informationstext mit nützlichen Details.

> [!TIP]
> Ein praktischer Tipp für schnellere Arbeitsabläufe.

> [!IMPORTANT]
> Wichtige Information, die für das Verständnis unerlässlich ist.

> [!WARNING]
> Warnung vor möglichen Fehlbedienungen oder unerwartetem Verhalten.

> [!CAUTION]
> Kritischer Sicherheitshinweis vor potenziellen Datenverlusten.
```

### Live-Darstellung im Dokument

Die obige Auszeichnung wird im PDF wie folgt als gestaltete Boxen mit farbigem Rahmen und Icon gerendert:

> [!NOTE]
> Dies ist ein allgemeiner Informationstext mit nützlichen Details.

> [!TIP]
> Ein praktischer Tipp für schnellere Arbeitsabläufe.

> [!IMPORTANT]
> Wichtige Information, die für das Verständnis unerlässlich ist.

> [!WARNING]
> Warnung vor möglichen Fehlbedienungen oder unerwartetem Verhalten.

> [!CAUTION]
> Kritischer Sicherheitshinweis vor potenziellen Datenverlusten.

### Automatische Lokalisierung über i18n-Labels

Die Titelleiste der Hinweisboxen („Hinweis“, „Tipp“, „Wichtig“, „Warnung“, „Achtung“) wird automatisch über die Beschriftungsdatei `i18n.yaml` der gewählten Dokumentensprache bezogen:

| Box-Typ | Verwendeter i18n-Schlüssel | Deutsche Beschriftung |
| :--- | :--- | :--- |
| `[!NOTE]` | `alert_note` | Hinweis |
| `[!TIP]` | `alert_tip` | Tipp |
| `[!IMPORTANT]` | `alert_important` | Wichtig |
| `[!WARNING]` | `alert_warning` | Warnung |
| `[!CAUTION]` | `alert_caution` | Achtung |

Wird im Markdown ein eigener Titel gewünscht, kann dieser in der ersten Zeile direkt angegeben werden:

```markdown
> [!NOTE] Individuelle Überschrift
> Eigener Inhalt mit spezifischem Titel.
```

> [!NOTE] Individuelle Überschrift
> Eigener Inhalt mit spezifischem Titel.

---

## Definitionslisten

Für Glossare, Begriffserklärungen oder Parameterübersichten bieten Definitionslisten eine besonders saubere typografische Struktur.

### Syntax

```markdown
Markdown
: Einfache, lesbare Auszeichnungssprache für formatierte Texte im Klartextformat.

markpublish.yaml
: Zentrale Projekt-Konfigurationsdatei zur Steuerung von Dokumentstruktur, Metadaten und Nummerierung.

Theme
: Gestaltungsvorlage aus Typst-Templates und Beschriftungen, die das visuelle Layout des Dokuments bestimmt.

Typst
: Moderne, hochperformante Satz-Engine, die markpublish zur typografischen Erzeugung von Druck-PDFs nutzt.
```

### Live-Darstellung im Dokument

Markdown
: Einfache, lesbare Auszeichnungssprache für formatierte Texte im Klartextformat.

markpublish.yaml
: Zentrale Projekt-Konfigurationsdatei zur Steuerung von Dokumentstruktur, Metadaten und Nummerierung.

Theme
: Gestaltungsvorlage aus Typst-Templates und Beschriftungen, die das visuelle Layout des Dokuments bestimmt.

Typst
: Moderne, hochperformante Satz-Engine, die markpublish zur typografischen Erzeugung von Druck-PDFs nutzt.

---

## Aufgabenlisten (Tasklists)

Zur Darstellung von Checklisten, To-Do-Listen oder Meilensteinen stehen Aufgabenlisten zur Verfügung.

### Syntax

```markdown
- [x] Python 3.10 oder neuer bereitstellen
- [x] markpublish installieren
- [ ] Erstes eigenes Dokument veröffentlichen
```

### Live-Darstellung im Dokument

- [x] Python 3.10 oder neuer bereitstellen
- [x] markpublish installieren
- [ ] Erstes eigenes Dokument veröffentlichen

---

## Mathematische Formeln

markpublish ermöglicht das direkte Setzen mathematischer Formeln im Fließtext oder als abgesetzte Formelblöcke. Die Formeln werden über die Satz-Engine Typst typografisch präzise gerendert.

### Syntax

```markdown
Die berühmte Energie-Masse-Äquivalenz lautet $E = mc^2$.

Abgesetzte Formel:

$$ A = \pi \cdot r^2 $$
```

### Live-Darstellung im Dokument

Die berühmte Energie-Masse-Äquivalenz lautet $E = mc^2$.

Abgesetzte Formel:

$$ A = \pi \cdot r^2 $$

---

## Alltägliche Sonderzeichen

Viele Dokumentationswerkzeuge erfordern das umständliche Maskieren bestimmter Symbole. markpublish verarbeitet gebräuchliche Zeichen im Fließtext vollautomatisch und kollisionsfrei:

* **Währungsbeträge:** `$5.00` oder `10.50 $` werden nicht versehentlich als mathematische Formeln interpretiert.
* **Programmiersprachen:** Namen wie `C#` lösen keine Typst-Sonderbefehle aus.
* **Benutzernamen und Erwähnungen:** `@author` oder `user@domain.com` werden sicher gedruckt.
* **Spitze Klammern:** Technische Platzhalter wie `<zielverzeichnis>` bleiben im Text erhalten.
