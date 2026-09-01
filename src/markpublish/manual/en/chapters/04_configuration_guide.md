# Configuration Guide

`markpublish.yaml` is the control document of every publication. It falls into three parts: metadata, template settings and chapter definitions.

## The `document` object

Everything global — metadata and layout switches — lives under `document:`:

```yaml
document:
  title: "markpublish User Guide"
  subtitle: "Modern PDF and HTML publishing"
  summary: "Short abstract for the cover page and metadata."
  author: "Frank Winter"
  organisation: "WASDCAT Games"
  date: "auto"                    # "auto" (today) or a fixed date "2026-08-31"
  version: "1.0.0"                # optional - omit it and the field disappears
  language: "en"                  # language code for labels and date format

  # Global switches
  cover: true                     # Cover page on/off
  toc: true                       # Global table of contents
  autonum_type: "decimal"         # "decimal", "roman", "legal", "none"
  header: true                    # Running header
  footer: true                    # Running footer
```

### Automatic date resolution
With `date: "auto"` or `date: "today"`, markpublish inserts the current date in the format matching the document language:
- `language: "de"` → `31.08.2026`
- `language: "en"` → `2026-08-31`

### Additional metadata fields
Any extra key (`status: "Draft"`, `department: "IT Architecture"`, …) may be defined freely and is available in every Jinja2 template as `document.<name>`.
