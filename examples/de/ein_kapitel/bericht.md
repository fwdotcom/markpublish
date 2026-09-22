# Projektbericht: Digitale Dokumenten-Workflows

Die automatisierte Erstellung hochwertiger technischer Dokumentationen stellt moderne Entwicklungsteams vor methodische Herausforderungen. Häufig führen historisch gewachsene Werkzeugketten zu fragmentierten Quellen, inkonsistentem Schriftbild und hohem manuellem Nachbearbeitungsaufwand. Dieser Bericht fasst die Erfahrungen bei der Einführung einer standardisierten Publikationspipeline mit **markpublish** zusammen.

## Ausgangslage und Zielsetzung

In verteilten Softwareprojekten entstehen Architekturbeschreibungen, Betriebshandbücher und Berichte dezentral in Markdown. Bisherige Konvertierungsprozesse über schwergewichtige LaTeX-Installationen oder HTML-Browser-Druckerzeugnisse zeigten erhebliche Schwächen:

- **Instabile Satzqualität:** Ungewollte Seitenumbrüche, fehlerhafte Silbentrennung und uneinheitliche Schriftarten.
- **Hohe Abhängigkeiten:** Komplexe Docker-Container oder lokale Laufzeitumgebungen jenseits von 2 GB Größe.
- **Fehlende Konsolidierung:** Keine zentrale Steuerung von Metadaten, Versionsständen und Titelseiten.

> [!NOTE]
> Das Primärziel bestand darin, eine schlanke, plattformunabhängige Pipeline zu etablieren, die direkt aus Git-Repositories reproduzierbare, druckreife PDF-Dateien ohne externe Binärabhängigkeiten generiert.

## Systemvergleich und Bewertung

Im Rahmen eines vierwöchigen Pilotprojekts wurden drei gängige Verfahren anhand definierter Qualitätskriterien evaluiert:

| Bewertungskriterium | Klassischer Office-Export | LaTeX / Pandoc | markpublish (Typst) |
| :--- | :--- | :--- | :--- |
| **Versionskontrolle (Git)** | Mangelhaft (Binärdateien) | Sehr gut (Reiner Text) | Exzellent (Markdown & YAML) |
| **Kompiliergeschwindigkeit** | Manuell / Langsam | Mäßig (mehrere Passes) | Extrem schnell (< 1 Sekunde) |
| **Installationsaufwand** | Proprietäre Software | Sehr hoch (> 2 GB) | Minimal (`pip install`) |
| **Typografische Qualität** | Variabel / Manuell | Hoch, aber komplex | Hochgradig konsistent |
| **Automatisierbarkeit (CI/CD)** | Nur über Workarounds | Gut etabliert | Nativ und leichtgewichtig |

Die Ergebnisse belegen, dass die Kombination aus nativem Typst-Backend und strukturiertem Markdown-Frontend den Durchsatz bei der Dokumentenproduktion signifikant steigert.

## Architektonische Leitprinzipien

Für die praktische Umsetzung wurden drei zentrale Konventionen verbindlich festgelegt:

### Trennung von Struktur und Inhalt
Sämtliche gestalterischen Vorgaben, Kapitelabfolgen und Metadaten werden ausschließlich im Projektmanifest `markpublish.yaml` gepflegt. Die Markdown-Dateien bleiben frei von Layout-Sonderregeln und konzentrieren sich vollständig auf den semantischen Inhalt.

### Deterministischer Satz
Durch fest in das Theme eingebettete Schriftarten (`Open Sans`) ist das typografische Ergebnis auf jedem Betriebssystem identisch – unabhängig davon, ob der Build lokal unter Windows, macOS oder in einer Linux-basierten GitHub-Actions-Umgebung ausgeführt wird.

### Integrierte Qualitätssicherung
Jeder Commit auf den Hauptzweig durchläuft eine automatisierte Prüfung. Erst wenn Linting-Regeln und automatisierte PDF-Kompilierung fehlerfrei abgeschlossen sind, werden die fertigen Dokumente für den Release freigegeben.

## Fazit und nächste Schritte

Die Umstellung auf **markpublish** reduzierte den Pflegeaufwand für Projektdokumente um mehr als 60 Prozent. Die Autoren schätzen die vertraute Markdown-Syntax, während das Management von einem stets einheitlichen und repräsentativen Erscheinungsbild profitiert. Als nächster Schritt ist die Anbindung an die zentrale Dokumentationsplattform für automatisierte Nightly-Builds geplant.
