# Workflows & Quality Assurance

Document engineering extends beyond drafting content. A structured release process ensures that publications satisfy all typographic, structural, and regulatory criteria before client distribution or print submission.

## The Publication Lifecycle

A resilient publication workflow proceeds across three progressive phases: authoring, automated validation, and final archival.

### Local Drafting and Fast Feedback
Authors write chapters locally in Markdown and review formatting using instantaneous preview builds. Because compilation completes in sub-second times, layout feedback is virtually real-time.

### Automated Continuous Integration
Every commit or pull request triggers automated quality verification within CI runners:

> [!IMPORTANT]
> Verify the integrity of all internal cross-references and ensure YAML configuration files validate against the schema. Broken resource paths immediately halt the build pipeline.

> [!WARNING]
> Adjusting typographic scale or margin dimensions can trigger unexpected page reflows. Inspect tables and wide code listings carefully following layout modifications.

> [!CAUTION]
> Post-processing generated PDF files using third-party PDF editors destroys build reproducibility and should be avoided in production environments.

## Pre-Flight Checklist

Before final sign-off and distribution, complete the following pre-flight verification items:

- [x] Confirm all chapter source files are registered in the manifest
- [x] Verify document language and hyphenation dictionary (`language: "en"`)
- [x] Review table of contents depth and numbering patterns
- [x] Check author credits, version string, and build date on cover page
- [x] Validate completeness of footnotes and bibliographical references
- [ ] Complete editorial peer review
- [ ] Verify PDF/A compliance for long-term digital preservation
- [ ] Apply cryptographic digital signature for document provenance

## Summary and Outlook

Standardizing technical documentation workflows with **markpublish** turns documentation into a first-class engineering artifact. Combining Git version control, automated CI/CD validation, and deterministic typesetting eliminates common layout discrepancies and delivers publication-grade results.
