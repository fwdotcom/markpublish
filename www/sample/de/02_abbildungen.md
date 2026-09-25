# Abbildungen & Verweise

Grafiken werden mit einer Beschriftung zur nummerierten Abbildung. Wort und Nummer setzt markpublish selbst, und jede Abbildung lässt sich im Text über ihre ID anspringen.

![Verarbeitungskette von Markdown zu PDF](pipeline.svg){width=100% noframe}

/// figure-caption
    attrs: {id: abb-pipeline}
Vom Markdown-Kapitel zum druckfertigen PDF
///

Wie [](#abb-pipeline) zeigt, liest markpublish die Kapiteldateien ein, nummeriert Überschriften, Abbildungen und Tabellen und übergibt das Ergebnis an Typst. Verweise wie dieser bleiben dabei immer richtig nummeriert und sind im PDF anklickbar.
