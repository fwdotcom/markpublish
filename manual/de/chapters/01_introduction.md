# Einführung & Architektur

Willkommen beim **markpublish Benutzerhandbuch**. `markpublish` ist ein modernes, quelloffenes Publishing-Werkzeug, das aus einfachen Markdown-Dateien professionell gesetzte **PDF-Publikationen** und **HTML-Vorschauen** erzeugt.

## Motivation & Zielsetzung

Viele Dokumentationswerkzeuge erfordern entweder komplexe LaTeX-Setups oder beschränken sich auf reine HTML-Webseiten. `markpublish` verbindet die Einfachheit von Markdown mit der typografischen Präzision von **CSS Paged Media** über die [WeasyPrint](https://weasyprint.org/)-Engine.

### Kernvorteile auf einen Blick:
- **Modulare Kapitel**: Jedes Kapitel wird als separate Markdown-Datei gepflegt.
- **Hierarchische Struktur**: Beliebig tief schachtelbare Unterkapitel und übergeordnete Abschnitte (*Parts*).
- **Deklarative Steuerung**: Ein zentrales Manifest (`markpublish.yaml`) steuert Inhalt, Metadaten und Layout.
- **W3C CSS Paged Media**: Exakte Kontrolle über `@page`-Ränder, 2-zeilige Kopf- und Fußzeilen, Seitenzahlen und Trennseiten.
- **Erweiterbare Pipeline**: Saubere Trennung zwischen Parser, Renderer und Template-Ebenen.

## Die Verarbeitungs-Pipeline

Die Architektur von `markpublish` folgt einem mehrstufigen Prozess:

1. **Konfigurations-Lader (`config.loader`)**: Liest die YAML-Struktur ein, validiert Datentypen und löst dynamische Variablen (z. B. `date: auto`) auf.
2. **Template-Resolver (`templates.resolver`)**: Sucht nach der 3-stufigen Priorität (*User* > *Common/Workspace* > *Package*) nach dem passenden Theme für das Zielformat.
3. **Markdown- & TOC-Engine (`markdown.engine`)**: Parst Markdown mit erweiterten Erweiterungen (Callouts, Tabellen, Pygments-Syntax-Highlighting), vergibt konsistente Überschriftennummern (`1.1`, `1.2`) und baut Inhaltsverzeichnisse auf.
4. **Renderer (`renderers.pdf` & `renderers.html`)**: Übergibt die gerenderten HTML- und CSS-Fragmente an WeasyPrint für den PDF-Export oder speichert eigenständiges, responsives HTML.

