# Daten im Text

Werte aus `document:` und `custom:` lassen sich im Markdown einsetzen, wiederholen, nachschlagen und an Bedingungen knüpfen. Ein Wert ohne Eintrag bricht den Bau mit Datei und Zeile ab.

| Eingabe | Wirkung |
| :--- | :--- |
| `{{author}}`, `{{custom.a.b}}` | Wert einsetzen; Mail- und Webadressen werden Links |
| `{% for x in custom.gruppe %}` … `{% endfor %}` | Zeilen je Eintrag wiederholen, in YAML-Reihenfolge |
| `{% for (x, key) in custom.gruppe %}` | dazu den Namen des Eintrags als `{{key}}` |
| `{% set kurz = custom.a.b %}` | Kurzname für einen Pfad, bis Datei- bzw. Blockende |
| `custom.systeme[d.system]` | Nachschlagen: Wert von `d.system` als Schlüssel einsetzen |
| `{% if pfad %}` … `{% else %}` … `{% endif %}` | Zeilen nur bei `true`; `else` optional |
| `{% if pfad == "wert" %}` | Vergleich mit einem Text |
| `\{{author}}`, `\{% … %}` | wörtlich zeigen; in Code ohnehin |

Anweisungen stehen allein in ihrer Zeile (in Zitat oder Hinweisbox mit `>` davor) und verschwinden beim Bau, eine Tabelle bleibt zusammenhängend. Nachschlagen geht nur im Markdown, nicht in den Angaben unter `document:` selbst.

```markdown
| Datenfluss | System | Betrieb |
| :--- | :--- | :--- |
{% for d in custom.datenfluesse %}
{% set sys = custom.systeme[d.system] %}
{% if sys.extern %}
| {{d.bezeichnung}} | {{sys.name}} | Dienstleister |
{% else %}
| {{d.bezeichnung}} | {{sys.name}} | intern |
{% endif %}
{% endfor %}
```
