# Daten im Text {#daten-im-text}

Werte aus der `markpublish.yaml` lassen sich in den Text einsetzen, wiederholen, nachschlagen und an Bedingungen knüpfen. Anweisungen wertet markpublish vor dem Markdown aus, eingesetzt werden die Werte erst danach: Ein `|` oder `*` in einem Wert kann deshalb keine Tabelle und keine Auszeichnung zerstören.

Grundsatz: Kein Wert darf fehlen. Ein Platzhalter oder Pfad ohne Wert bricht den Bau mit Datei und Zeile ab, statt eine Lücke zu lassen.

---

## Platzhalter

`{{name}}` setzt eine Angabe aus `document:` ein, etwa `{{author}}`, `{{version}}` oder `{{date}}` (bei `"auto"` das errechnete Datum); das gilt auch für eigene Metadatenfelder. Werte, die nur im Text gebraucht werden, gehören unter `custom:`. Dort dürfen sie verschachtelt sein und werden mit Punkten angesprochen:

```yaml
document:
  author: "Frank Winter"
  custom:
    support_mail: "support@example.com"
    verfahren:
      name: "Verfahren X"
```

```markdown
Ansprechpartner: {{author}}, {{custom.support_mail}}.
Dieses Dokument beschreibt {{custom.verfahren.name}}.
```

Ist ein eingesetzter Wert eine E-Mail-Adresse oder eine URL, wird er ein Link; steht der Platzhalter schon in einem Link, bleibt es bei diesem. Werte unter `custom` erreichen das Theme nicht. Größere Datenbestände lassen sich mit `!file` aus eigenen Dateien laden (siehe [](#werte-aus-anderen-dateien)).

## Schleifen

`{% for %}` wiederholt die Zeilen bis `{% endfor %}` für jeden Eintrag einer Gruppe, in der Reihenfolge der YAML-Datei – etwa eine Tabellenzeile je Rolle:

```yaml
document:
  custom:
    rollen:
      owner: {bezeichnung: "Verfahrensverantwortliche/r", name: "A. Muster"}
      admin: {bezeichnung: "Technische Administration", name: "B. Beispiel"}
```

```markdown
| Rolle | Name | Schlüssel |
| :--- | :--- | :--- |
{% for (rolle, key) in custom.rollen %}
| {{rolle.bezeichnung}} | {{rolle.name}} | {{key}} |
{% endfor %}
```

`(rolle, key)` liefert zusätzlich den Namen des Eintrags (`owner`); `for rolle in …` genügt, wenn er nicht gebraucht wird. Schleifen lassen sich schachteln, ihr Name gilt nur in ihnen.

## Kurznamen

`{% set %}` gibt einem langen Pfad einen Kurznamen. Er gilt bis zum Ende der Datei, innerhalb einer Schleife oder Bedingung bis zu deren Ende:

```markdown
{% set owner = custom.rollen.owner %}
Verantwortlich ist {{owner.name}}.
```

## Nachschlagen

Verweist ein Wert per Schlüssel auf einen Eintrag einer anderen Gruppe, schlägt `gruppe[pfad]` ihn nach: markpublish setzt den Wert von `pfad` als Schlüssel ein. So stehen Daten nur an einer Stelle, auch wenn mehrere Einträge sie brauchen.

```yaml
document:
  custom:
    systeme:
      crm: {name: "Salesforce CRM", standort: "EU (Frankfurt)", extern: true}
    datenfluesse:
      kunden: {bezeichnung: "Kundenstammdaten", system: crm}
```

`{{custom.systeme[custom.datenfluesse.kunden.system].name}}` ergibt `Salesforce CRM`. In Schleifen und mit Kurznamen wird es handlich:

```markdown
{% for d in custom.datenfluesse %}
{% set sys = custom.systeme[d.system] %}
- {{d.bezeichnung}}: {{sys.name}}, {{sys.standort}}
{% endfor %}
```

* Der Wert in den Klammern muss ein einzelner Wert sein; ein Schleifenschlüssel (`key`) geht ebenso.
* Gibt es keinen Eintrag mit diesem Schlüssel, bricht der Bau ab – ein Tippfehler in den Daten fällt so sofort auf.
* Nachschlagen funktioniert im Markdown, nicht in den Angaben unter `document:` selbst (Titel, Deckblatt).

## Bedingungen

`{% if %}` nimmt Zeilen nur auf, wenn die Bedingung zutrifft; `{% else %}` ist optional:

```markdown
{% if custom.verfahren.dsfa_erforderlich %}
Eine Datenschutz-Folgenabschätzung liegt bei (Anlage 3).
{% else %}
Eine Datenschutz-Folgenabschätzung ist nicht erforderlich.
{% endif %}

{% if custom.verfahren.betrieb == "cloud" %}
Der Betrieb erfolgt beim Dienstleister.
{% endif %}
```

* `{% if pfad %}` verlangt einen Wahrheitswert (`true` oder `false`).
* `{% if pfad == "wert" %}` vergleicht einen einzelnen Wert mit einem Text; Zahlen werden als Text verglichen (`== "2024"`).
* Ein fehlender Pfad ist ein Fehler, keine falsche Bedingung.

## Regeln für Anweisungen

* **Anweisungen stehen allein in ihrer Zeile.** Die Zeile verschwindet beim Bau vollständig, eine Tabelle bleibt also zusammenhängend. In einem Zitat oder einer Hinweisbox darf `>` davorstehen.
* **Wörtlich zeigen:** In Code und Codeblöcken bleiben Platzhalter und Anweisungen stehen, im Fließtext mit vorangestelltem Backslash: `\{{author}}`, `\{% … %}`.
* **Namen:** Ein Kurz- oder Schleifenname darf keine Angabe unter `document` verdecken (`author`, `custom` …).
* **Fehler** wie ein fehlendes `{% endfor %}` oder `{% endif %}`, ein unbekannter Pfad oder ein falsch verschachtelter Block brechen den Bau mit Datei und Zeile ab.

## Beispiel: Datenflüsse und Systeme

Die `markpublish.yaml` dieses Handbuchs enthält eine kleine Datensammlung:

```yaml
document:
  custom:
    systeme:
      crm: {name: "Salesforce CRM", standort: "EU (Frankfurt)", extern: true}
      erp: {name: "SAP S/4HANA", standort: "Deutschland", extern: false}
    datenfluesse:
      kunden: {bezeichnung: "Kundenstammdaten", system: crm}
      rechnungen: {bezeichnung: "Rechnungsdaten", system: erp}
```

Eine Tabelle mit einer Zeile je Datenfluss, das System nachgeschlagen und der Hinweis abhängig vom Betrieb:

```markdown
| Datenfluss | System | Standort | Betrieb |
| :--- | :--- | :--- | :--- |
{% for d in custom.datenfluesse %}
{% set sys = custom.systeme[d.system] %}
{% if sys.extern %}
| {{d.bezeichnung}} | {{sys.name}} | {{sys.standort}} | Dienstleister |
{% else %}
| {{d.bezeichnung}} | {{sys.name}} | {{sys.standort}} | eigenes Rechenzentrum |
{% endif %}
{% endfor %}
```

Ergebnis:

| Datenfluss | System | Standort | Betrieb |
| :--- | :--- | :--- | :--- |
{% for d in custom.datenfluesse %}
{% set sys = custom.systeme[d.system] %}
{% if sys.extern %}
| {{d.bezeichnung}} | {{sys.name}} | {{sys.standort}} | Dienstleister |
{% else %}
| {{d.bezeichnung}} | {{sys.name}} | {{sys.standort}} | eigenes Rechenzentrum |
{% endif %}
{% endfor %}

Ändert sich der Standort eines Systems, genügt eine Zeile in der YAML-Datei – jede Tabelle, die es nachschlägt, zieht mit.
