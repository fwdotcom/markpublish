# Data in the Text

Values from `document:` and `custom:` can be inserted into the Markdown, repeated, looked up and tied to conditions. A value without an entry stops the build with file and line.

| Input | Effect |
| :--- | :--- |
| `{{author}}`, `{{custom.a.b}}` | insert a value; email and web addresses become links |
| `{% for x in custom.group %}` … `{% endfor %}` | repeat lines per entry, in YAML order |
| `{% for (x, key) in custom.group %}` | also the entry's name as `{{key}}` |
| `{% set short = custom.a.b %}` | short name for a path, until the end of file or block |
| `custom.systems[f.system]` | lookup: insert the value of `f.system` as the key |
| `{% if path %}` … `{% else %}` … `{% endif %}` | lines only for `true`; `else` optional |
| `{% if path == "value" %}` | compare with a text |
| `\{{author}}`, `\{% … %}` | show literally; code stays literal anyway |

Statements stand alone on their line (with `>` in front inside a quote or callout) and disappear in the build, so a table stays contiguous. Lookups work only in the Markdown, not in the entries under `document:` themselves.

```markdown
| Data flow | System | Operation |
| :--- | :--- | :--- |
{% for f in custom.flows %}
{% set sys = custom.systems[f.system] %}
{% if sys.external %}
| {{f.title}} | {{sys.name}} | Service provider |
{% else %}
| {{f.title}} | {{sys.name}} | In-house |
{% endif %}
{% endfor %}
```
