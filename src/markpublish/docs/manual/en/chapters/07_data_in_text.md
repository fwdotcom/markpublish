# Data in the Text {#data-in-the-text}

Values from `markpublish.yaml` can be inserted into the text, repeated, looked up and tied to conditions. markpublish evaluates statements before the Markdown and inserts the values only afterwards: a `|` or `*` inside a value can therefore never break a table or a markup.

Principle: no value may be missing. A placeholder or path without a value stops the build with file and line instead of leaving a gap.

---

## Placeholders

`{{name}}` inserts a value from `document:`, e.g. `{{author}}`, `{{version}}` or `{{date}}` (the computed date for `"auto"`); this includes custom metadata fields. Values needed only in the text belong under `custom:`. They may be nested there and are addressed with dots:

```yaml
document:
  author: "Frank Winter"
  custom:
    support_mail: "support@example.com"
    procedure:
      name: "Procedure X"
```

```markdown
Contact: {{author}}, {{custom.support_mail}}.
This document describes {{custom.procedure.name}}.
```

If an inserted value is an email address or a URL, it becomes a link; if the placeholder already sits inside a link, that link is kept. Values under `custom` do not reach the theme. Larger data sets can be loaded from separate files with `!file` (see [](#values-from-other-files)).

## Loops

`{% for %}` repeats the lines up to `{% endfor %}` for every entry of a group, in the order of the YAML file – for instance one table row per role:

```yaml
document:
  custom:
    roles:
      owner: {label: "Procedure owner", name: "A. Sample"}
      admin: {label: "Technical administration", name: "B. Example"}
```

```markdown
| Role | Name | Key |
| :--- | :--- | :--- |
{% for (role, key) in custom.roles %}
| {{role.label}} | {{role.name}} | {{key}} |
{% endfor %}
```

`(role, key)` also yields the entry's name (`owner`); `for role in …` is enough when it is not needed. Loops can be nested; their names apply only inside them.

## Short Names

`{% set %}` gives a long path a short name. It applies until the end of the file, inside a loop or condition until its end:

```markdown
{% set owner = custom.roles.owner %}
Responsible: {{owner.name}}.
```

## Lookups

When a value refers by key to an entry of another group, `group[path]` looks it up: markpublish inserts the value of `path` as the key. Data thus live in one place, even when several entries need them.

```yaml
document:
  custom:
    systems:
      crm: {name: "Salesforce CRM", location: "EU (Frankfurt)", external: true}
    flows:
      customers: {title: "Customer master data", system: crm}
```

`{{custom.systems[custom.flows.customers.system].name}}` yields `Salesforce CRM`. Loops and short names make it convenient:

```markdown
{% for f in custom.flows %}
{% set sys = custom.systems[f.system] %}
- {{f.title}}: {{sys.name}}, {{sys.location}}
{% endfor %}
```

* The value inside the brackets must be a single value; a loop key (`key`) works as well.
* If there is no entry with that key, the build stops – a typo in the data shows up at once.
* Lookups work in the Markdown, not in the entries under `document:` themselves (title, cover page).

## Conditions

`{% if %}` includes lines only when the condition holds; `{% else %}` is optional:

```markdown
{% if custom.procedure.dpia_required %}
A data protection impact assessment is attached (annex 3).
{% else %}
A data protection impact assessment is not required.
{% endif %}

{% if custom.procedure.operation == "cloud" %}
Operation is outsourced to the service provider.
{% endif %}
```

* `{% if path %}` needs a boolean (`true` or `false`).
* `{% if path == "value" %}` compares a single value with a text; numbers are compared as text (`== "2024"`).
* A missing path is an error, not a false condition.

## Rules for Statements

* **Statements stand alone on their line.** The line disappears entirely in the build, so a table stays contiguous. Inside a quote or callout, `>` may precede it.
* **Showing them literally:** in code and code blocks, placeholders and statements stay as written; in running text, prefix a backslash: `\{{author}}`, `\{% … %}`.
* **Names:** a short or loop name must not hide an entry under `document` (`author`, `custom` …).
* **Errors** such as a missing `{% endfor %}` or `{% endif %}`, an unknown path or a wrongly nested block stop the build with file and line.

## Example: Data Flows and Systems

The `markpublish.yaml` of this manual contains a small data set:

```yaml
document:
  custom:
    systems:
      crm: {name: "Salesforce CRM", location: "EU (Frankfurt)", external: true}
      erp: {name: "SAP S/4HANA", location: "Germany", external: false}
    flows:
      customers: {title: "Customer master data", system: crm}
      invoices: {title: "Invoice data", system: erp}
```

A table with one row per data flow, the system looked up and the operation depending on the system:

```markdown
| Data flow | System | Location | Operation |
| :--- | :--- | :--- | :--- |
{% for f in custom.flows %}
{% set sys = custom.systems[f.system] %}
{% if sys.external %}
| {{f.title}} | {{sys.name}} | {{sys.location}} | Service provider |
{% else %}
| {{f.title}} | {{sys.name}} | {{sys.location}} | Own data centre |
{% endif %}
{% endfor %}
```

Result:

| Data flow | System | Location | Operation |
| :--- | :--- | :--- | :--- |
{% for f in custom.flows %}
{% set sys = custom.systems[f.system] %}
{% if sys.external %}
| {{f.title}} | {{sys.name}} | {{sys.location}} | Service provider |
{% else %}
| {{f.title}} | {{sys.name}} | {{sys.location}} | Own data centre |
{% endif %}
{% endfor %}

If a system's location changes, one line in the YAML file is enough – every table that looks it up follows.
