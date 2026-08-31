# Kapitel, Unterkapitel und Parts

`markpublish` unterstützt eine flexible und intuitive Strukturierung von Dokumenten.

## Kapitel-Definition

Ein einfaches Kapitel wird mit `file:`, optionalem `title:` und `summary:` angegeben:

```yaml
chapters:
  - file: "chapters/01_intro.md"
    title: "Einleitung"
    summary: "Zielsetzung des Leitfadens."
    divider_page: true           # Erzeugt eine Trennseite vor dem Kapitel
    toc: false                   # Kein kapitelweises Mini-TOC
```

## Hierarchische Unterkapitel

Um ein Unterkapitel zu definieren, rücken Sie einfach weitere Kapitel unter `chapters:` ein:

```yaml
chapters:
  - file: "chapters/02_architecture.md"
    title: "Systemarchitektur"
    divider_page: true
    toc: 2                       # Mini-TOC bis Überschriftstiefe 2
    chapters:
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"
        divider_page: false
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Client"
        divider_page: false
```

`markpublish` nummeriert die Unterkapitel automatisch konsistent als `2.1` und `2.2`.

## Übergeordnete Abschnitte (Parts / Blöcke)

Für Hauptabschnitte oder Anhangsblöcke, die mehrere Kapitel umfassen, verwenden Sie das Schlüsselwort `part:`:

```yaml
chapters:
  - part: "Anhänge"
    summary: "Ergänzende Tabellen und Referenzen."
    divider_page: true           # Große Trennseite für den gesamten Anhang
    autonum: "none"              # Keine vorangestellte Ziffer
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Anhang A: Referenz"
      - file: "chapters/appendix_b.md"
        title: "Anhang B: Glossar"
```

Der Part-Titel (z. B. *"Anhänge"*) wird automatisch in die laufenden 2-zeiligen Kopfzeilen der Einzelseiten übernommen.

