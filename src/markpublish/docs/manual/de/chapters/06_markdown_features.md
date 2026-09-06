# Besondere Markdown-Features

markpublish unterstützt den vollen Funktionsumfang des modernen CommonMark- und GitHub-Flavored-Markdown-Standards. Grundlegende Elemente wie Überschriften, Absätze, Textauszeichnungen (*kursiv*, **fett**), Tabellen, Aufzählungen, Quellcode-Blöcke und Weblinks funktionieren exakt wie gewohnt.

Dieses Kapitel konzentriert sich ausschließlich auf die darüber hinausgehenden Spezialfeatures und typografischen Erweiterungen von markpublish. Jeder Abschnitt zeigt zuerst die Auszeichnung im Markdown und unmittelbar darunter das Ergebnis, wie es in diesem Handbuch gesetzt ist.

---

## Hinweisboxen (Admonitions und Callouts)

Zur optischen Hervorhebung wichtiger Passagen unterstützt markpublish GitHub-konforme Callout-Blöcke. Sie werden als Zitatblock notiert, dessen erste Zeile den Typ der Box in eckigen Klammern nennt:

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

Im PDF entstehen daraus gestaltete Boxen mit farbigem Rahmen und Icon:

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

Wird ein eigener Titel gewünscht, kann dieser direkt hinter dem Typ in der ersten Zeile angegeben werden:

```markdown
> [!NOTE] Individuelle Überschrift
> Eigener Inhalt mit spezifischem Titel.
```

> [!NOTE] Individuelle Überschrift
> Eigener Inhalt mit spezifischem Titel.

### Automatische Lokalisierung über i18n-Labels

Ohne eigenen Titel wird die Titelleiste der Hinweisboxen („Hinweis“, „Tipp“, „Wichtig“, „Warnung“, „Achtung“) automatisch über die Beschriftungsdatei `i18n.yaml` der gewählten Dokumentsprache bezogen:

| Box-Typ | Verwendeter i18n-Schlüssel | Deutsche Beschriftung |
| :--- | :--- | :--- |
| `[!NOTE]` | `alert_note` | Hinweis |
| `[!TIP]` | `alert_tip` | Tipp |
| `[!IMPORTANT]` | `alert_important` | Wichtig |
| `[!WARNING]` | `alert_warning` | Warnung |
| `[!CAUTION]` | `alert_caution` | Achtung |

### Alternative Schreibweise mit `!!!`

Neben der GitHub-Notation versteht markpublish auch die aus MkDocs bekannte Admonition-Schreibweise. Der Typ folgt auf drei Ausrufezeichen, ein optionaler Titel steht in Anführungszeichen dahinter, der Inhalt wird um vier Leerzeichen eingerückt:

```markdown
!!! warning "Eigener Titel"
    Der eingerückte Inhalt darf mehrere Absätze umfassen.
```

!!! warning "Eigener Titel"
    Der eingerückte Inhalt darf mehrere Absätze umfassen.

Beide Schreibweisen erzeugen dieselbe gestaltete Box. Ein Unterschied bleibt allerdings: Ohne eigenen Titel setzt `!!!` die englische Vorgabe der Erweiterung („Note“, „Tip“, „Warning“) statt der Beschriftung aus der i18n-Kaskade. Wer die lokalisierte Titelzeile möchte, notiert entweder `> [!NOTE]` oder gibt bei `!!!` einen ausdrücklich leeren Titel an:

```markdown
!!! note ""
    Die Titelzeile stammt dann aus der i18n-Kaskade.
```

!!! note ""
    Die Titelzeile stammt dann aus der i18n-Kaskade.

Ein unbekannter Typ (etwa `!!! info`) wird als Hinweis-Box gesetzt und behält seinen Namen als Titelzeile.

---

## Definitionslisten

Für Glossare, Begriffserklärungen oder Parameterübersichten bieten Definitionslisten eine besonders saubere typografische Struktur. Der Begriff steht in einer eigenen Zeile, die zugehörige Erläuterung folgt darunter, eingeleitet durch einen Doppelpunkt:

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

Gesetzt wird daraus ein Block aus hervorgehobenem Begriff und eingerückter Erläuterung:

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

Zur Darstellung von Checklisten, To-do-Listen oder Meilensteinen stehen Aufgabenlisten zur Verfügung. Notiert werden sie als Aufzählung, deren Einträge mit einer leeren oder angekreuzten Klammer beginnen:

```markdown
- [x] Python 3.10 oder neuer bereitstellen
- [x] markpublish installieren
- [ ] Erstes eigenes Dokument veröffentlichen
```

markpublish setzt Aufgabenlisten typografisch sauber ohne vorangestellte Aufzählungspunkte (Bullets) direkt mit der Checkbox und dem Text; mehrzeilige Beschreibungen brechen bündig unter der ersten Zeile um:

- [x] Python 3.10 oder neuer bereitstellen

- [x] markpublish installieren

- [ ] Erstes eigenes Dokument veröffentlichen

---

## Fußnoten

markpublish unterstützt die klassische Markdown-Notation für Fußnoten. Damit lassen sich weiterführende Hinweise, Quellenangaben oder detaillierte Erläuterungen auslagern, ohne den Lesefluss des Haupttextes zu unterbrechen.

Die Notation erfolgt zweistufig: An der gewünschten Textstelle steht ein Verweis wie `[^1]` oder ein sprechender Bezeichner wie `[^hinweis]`. Die zugehörige Definition kann an beliebiger Stelle im Markdown-Dokument notiert werden – üblicherweise am Ende des jeweiligen Abschnitts oder Kapitels:

```markdown
Dieser Satz enthält eine nummerierte Fußnote[^1] sowie eine Notiz mit Text-Schlüssel[^hinweis].

[^1]: Dies ist der Inhalt der ersten Fußnote.
[^hinweis]: Text-Schlüssel werden bei der Ausgabe automatisch in die richtige Ziffer umgewandelt.
```

Im Satz ergibt das die folgenden beiden Verweise; ihre Texte stehen am unteren Rand dieser Seite, und Verweisziffer und Fußnotentext sind im PDF gegenseitig verlinkt:

Dieser Satz enthält eine nummerierte Fußnote[^1] sowie eine Notiz mit Text-Schlüssel[^hinweis].

[^1]: Dies ist der Inhalt der ersten Fußnote.
[^hinweis]: Text-Schlüssel werden bei der Ausgabe automatisch in die richtige Ziffer umgewandelt.

---

## Mathematische Formeln

markpublish ermöglicht das direkte Setzen mathematischer Formeln im Fließtext oder als abgesetzte Formelblöcke. Die Formeln werden über die Satz-Engine Typst typografisch präzise gerendert.

Unterstützt werden gängige mathematische Ausdrücke wie Brüche (`\frac{a}{b}`), Wurzeln (`\sqrt{x}`), Summen (`\sum`), Integrale (`\int`), griechische Symbole (`\alpha`, `\pi`, `\sigma` etc.) sowie die native Typst-Math-Syntax. Formeln im Fließtext stehen zwischen einfachen Dollarzeichen, abgesetzte Formelblöcke zwischen doppelten:

```markdown
Die berühmte Energie-Masse-Äquivalenz lautet $E = m c^2$.

Abgesetzte Kreisflächenberechnung und quadratische Lösungsformel:

$$ A = \pi \cdot r^2 \quad \text{und} \quad x = \frac{-b \pm \sqrt{b^2 - 4 a c}}{2 a} $$
```

Im Satz ergibt das:

Die berühmte Energie-Masse-Äquivalenz lautet $E = m c^2$.

Abgesetzte Kreisflächenberechnung und quadratische Lösungsformel:

$$ A = \pi \cdot r^2 \quad \text{und} \quad x = \frac{-b \pm \sqrt{b^2 - 4 a c}}{2 a} $$

*Typografischer Hinweis zu Variablen:*  
In Typst Math stehen mehrbuchstabige Wörter für Funktionen oder Bezeichner (wie `sin`, `cos`, `sqrt`). Die Multiplikation einzelner Variablen wird deshalb durch ein Leerzeichen getrennt notiert (z. B. `m c^2` oder `4 a c`).

---

## Typografische Textauszeichnungen und Satzzeichen

markpublish unterstützt über Standard-Markdown hinaus feine typografische Textauszeichnungen und echte typografische Satzzeichen:

| Auszeichnung | Eingabe | Ausgabe | Typischer Einsatzzweck |
| :--- | :--- | :--- | :--- |
| **Hochstellung** | `10^3^` oder `m^2^` | 10^3^ bzw. m^2^ | Potenzen, Quadrat- und Kubikmeter |
| **Tiefstellung** | `H~2~O` oder `CO~2~` | H~2~O bzw. CO~2~ | Chemische Formeln, Indizes |
| **Durchgestrichen** | `~~veraltet~~` | ~~veraltet~~ | Korrekturen, überholte Angaben |
| **Halbgeviertstrich (En-Dash)** | `10--20 Uhr` | 10--20 Uhr | Bis-Striche, Zeit- und Seitenspannen |
| **Geviertstrich (Em-Dash)** | `Einwurf --- oder nicht` | Einwurf --- oder nicht | Gedanklicher Einschub, Sprechpause |
| **Auslassungspunkte (Ellipse)** | `Warten...` | Warten... | Satzabbrüche, Auslassungen |

> [!TIP] Fließtext und mathematischer Formelsatz
> Die Auszeichnungen `^hochgestellt^` und `~tiefgestellt~` eignen sich ideal für gebräuchliche Einheiten ($m^2$) und chemische Formeln ($H_2O$) im Fließtext. Für mathematische Gleichungen und Variablenformeln empfiehlt sich die native Formelumgebung mit `$...$` bzw. `$$...$$` (siehe Abschnitt *Mathematische Formeln*).

---

## Automatische Symbole und Pfeile

Häufige Symbole und Operatoren werden bei der Eingabe im Fließtext automatisch in typografische Glyphen umgewandelt:

| Symbol | Eingabe | Ausgabe | Typischer Einsatzzweck |
| :--- | :--- | :--- | :--- |
| **Pfeile** | `-->`, `<--`, `<-->` | -->, <--, <--> | Ablaufschritte, Rückverweise, Äquivalenz |
| **Brüche** | `1/2`, `1/4`, `3/4` | 1/2, 1/4, 3/4 | Mengenangaben, Brüche |
| **Rechenzeichen** | `+/-`, `=/=` | +/-, =/= | Toleranzen (±), mathematische Ungleichheit (≠) |
| **Urheberrecht & Marken** | `(c)`, `(tm)`, `(r)` | (c), (tm), (r) | Copyright, Trademark, Registered |

---

## Automatische Verlinkung und Querverweise

Web- und Mailadressen werden bei direkter Eingabe automatisch erkannt und formatiert. Über Anker-Links lässt sich zudem auf jede Überschrift im Dokument verweisen:

| Funktion | Eingabe | Ausgabe | Erläuterung |
| :--- | :--- | :--- | :--- |
| **Web-Adresse (Magic Link)** | `https://example.com` | https://example.com | URLs werden ohne Klammern verlinkt |
| **E-Mail-Adresse (Magic Link)** | `kontakt@example.com` | kontakt@example.com | Mailadressen werden automatisch klickbar |
| **Dokument-Querverweis** | `[Kapitelanfang](#besondere-markdown-features)` | [Kapitelanfang](#besondere-markdown-features) | Klickbare Sprungmarke auf Überschriften |

---

## Maskierungsfreie Sonderzeichen

Viele Dokumentationswerkzeuge erfordern das umständliche Maskieren bestimmter Symbole. markpublish verarbeitet gebräuchliche Zeichen im Fließtext vollautomatisch und kollisionsfrei:

| Kategorie | Beispiel | Verhalten im Dokument |
| :--- | :--- | :--- |
| **Währungsbeträge** | `$5.00` oder `10.50 $` | Werden nicht versehentlich als mathematische Formeln interpretiert. |
| **Programmiersprachen** | `C#` | Löst keine internen Typst-Sonderbefehle aus. |
| **Benutzernamen & Erwähnungen** | `@author` oder `user@domain.com` | Werden sicher als Text gedruckt bzw. verlinkt. |
| **Technische Bezeichner** | `<zielverzeichnis>` | Spitze Klammern bleiben als Text erhalten und gehen nicht verloren. |
