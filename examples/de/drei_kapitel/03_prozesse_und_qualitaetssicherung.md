# Prozesse & Qualitätssicherung

Die Erstellung technischer Dokumente endet nicht mit dem Schreiben des Textes. Ein geregelter Freigabeprozess stellt sicher, dass Dokumente alle typografischen und inhaltlichen Anforderungen vor der Weitergabe an Kunden oder das Druckhaus erfüllen.

## Der Veröffentlichungs-Workflow

Ein robuster Publikationszyklus gliedert sich in drei aufeinanderfolgende Phasen: Redaktion, automatisierte Validierung und finale Archivierung.

### Redaktionelle Erstellung
Autoren erstellen Kapitel lokal in Markdown und überprüfen das Schriftbild regelmäßig mit schnellen Vorschau-Builds. Da der Build-Prozess weniger als eine Sekunde beansprucht, kann die Ausgabe praktisch in Echtzeit geprüft werden.

### Automatisierte CI-Validierung
Bei jedem Pull-Request oder Commit führt das Continuous-Integration-System automatisierte Qualitätsprüfungen durch:

> [!IMPORTANT]
> Vor jedem Release muss die Konsistenz aller internen Verweise und die Gültigkeit des YAML-Schemas sichergestellt sein. Fehlerhafte Pfadangaben brechen den Build sofort ab.

> [!WARNING]
> Änderungen an Schrifthierarchien oder Randabständen können zu unvorhergesehenen Seitenumbrüchen führen. Überprüfen Sie insbesondere Tabellen und abgesetzte Code-Blöcke nach Layout-Anpassungen.

> [!CAUTION]
> Manuelle Eingriffe in die generierte PDF-Datei (z. B. nachträgliche Bearbeitung mit externen PDF-Editoren) zerstören die Reproduzierbarkeit und sollten unter allen Umständen vermieden werden.

## Veröffentlichungs-Checkliste

Vor der endgültigen Publikation oder Übergabe an den Druck empfiehlt sich das Abarbeiten der folgenden Kontrollliste:

- [x] Vollständigkeit aller Kapiteldateien im Manifest prüfen
- [x] Korrekte Sprach- und Silbentrennungseinstellungen (`language: "de"`) verifizieren
- [x] Inhaltsverzeichnistiefe und Nummerierungsmuster abgleichen
- [x] Autorenangaben, Versionsnummer und Datum auf dem Deckblatt aktualisieren
- [x] Fußnoten und Quellenverweise auf Vollständigkeit prüfen
- [ ] Freigabe durch das Fachlektorat einholen
- [ ] PDF/A-Konformität für Langzeitarchivierung validieren
- [ ] Digitale Signatur zur Dokumenten-Authentifizierung anbringen

## Ausblick und Weiterentwicklung

Durch die konsequente Standardisierung auf **markpublish** wird Dokumentation zu einem vollwertigen Bestandteil des Software-Engineering-Prozesses. Die Kombination aus Versionsverwaltung, automatisierten Testketten und deterministischem Buchdruck-Satz eliminiert typische Fehlerquellen und garantiert ein langlebiges, repräsentatives Schriftbild.
