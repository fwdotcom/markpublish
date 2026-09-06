# Welcome to markpublish

Congratulations, you have created your new markpublish project.

It consists of two files: `markpublish.yaml` and this chapter in `welcome.md`.

## Building the PDF

Change into the newly created project directory and build the PDF:

```bash
cd Test
markpublish build
```

## Adding further chapters

Create a new Markdown file and add it with another `file:` key under
`chapters:` in `markpublish.yaml`. Paths are relative to the configuration
file:

```yaml
parts:
  - part: "Main Part"
    chapters:
      - file: "welcome.md"
      - file: "your_new_md_file.md"
```

That is all it takes: on the next `markpublish build` the new chapter stands in the PDF – in the order the files are listed under `chapters:`.

## Looking things up

The manual and the quick reference tell you more. markpublish writes both for you straight from the command line:

```bash
markpublish cheatsheet                  # print the compact quick reference
markpublish manual                      # print the detailed user guide
```

For the current state of development have a look at https://github.com/fwdotcom/markpublish. Enjoy creating documents with markpublish!
