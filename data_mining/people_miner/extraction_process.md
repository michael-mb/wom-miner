---
gitea: none
include_toc: true
---

# People Miner

**Implementierung: [siehe mining/people](../../mining/people/)**

## Zielsetzung

- Personen finden und folgende Entitäten zuordnen:
  - Organisationen - Fakultät, Lehrstuhl, Institut und/oder Arbeitsgruppe
  - Forschungsthemen
  - Projekte
  - Publikationen (?) - ggf. über andere Datenbanken
- Kontaktdaten und weitere Informationen bereitstellen:
  - Mailadresse
  - Profilseite oder Homepage
  - Bild (?)
- Auseinanderhalten von unterschiedlichen Personen mit gleichem Namen.

Die Beziehung von verschiedenen Mitarbeitern kann ggf. beim People Mining sogar ausgelassen werden, da bei einer Zuordnung zu Organisationen und Projekten implizit auch Mitarbeiter verknüpft werden.

## Möglichkeit 1: Unstrukturierte Suche

- Suche nach <u>Namen</u> für Personen mittels Named Entity Recognition (NER) auf allen gecrawlten Seiten (z.B. Blogartikeln, Projektbeschreibungen)
- Zuordnung zu Organisationen geschieht aus dem Text mittels NLP-Heuristiken ("Max Muster vom Institut für X"), statistischen Verfahren ("die Seiten, wo der Name am häufigsten auftritt"), über Beziehungen ("Personen, die oft aufeinander verweisen oder auf den gleichen Seiten gehören zusammen") oder Hyperlinks

**Vorteile**
- Relevanz der Person ergibt sich direkt aus Häufigkeit / Aktualität der Texte.
- Aus dem gefundenem Text ist in der Regel das Forschungsthema ersichtlich
- NER benötigt lediglich Fließtext

**Nachteile**
- Keine Zuordnung zu Organisationen möglich; diese muss separat erfolgen
- Person muss nicht mehr an der Uni arbeiten oder nicht zur Uni gehören

**Pipeline**
1. Eingabe: <u>Reintext</u> einer Seite ohne HTML-Tags
   - Möglichst ohne Dinge, die häufig vorkommen (Header, Footer)
   - Möglichst ohne Navigationselemente
1. NER liefert Namen von Personen
1. Zuordnung zu Organisationen über
   - Heuristiken (Beispiel: "[Vorname] [Nachname] vom [Organisation]")
   - Statistische Verfahren (Beispiel: "Die Seite, wo der Mitarbeitername am häufigsten auftritt, gehört zu der Organisation des Mitarbeiters")
   - Modellierung von Beziehungen (Beispiel: "Mitarbeiter, die zum gleichen Lehrstuhl gehören, tauchen vsl. häufig bei ähnlichen URLs auf"; "Personen, die gehäuft zusammen auftreten oder aufeinander verweisen, gehören vermutlich zusammen")
   - Hyperlinks (Beispiel: `<a href="uni.edu/institut/mustermann">Max Mustermann</a>`)
1. Zuordnung zu Forschungsthemen und -projekten über Keywords (Beispiel: "In Seiten, die Max Mustermann erwähnen, geht es häufig um KI")

## Möglichkeit 2: Strukturierte Suche

- Suche nach Listen / Tabellen mit Mitarbeitern
- Identifizieren von <u>Profilseiten</u>, auf denen sich Mitarbeiter vorstellen

**Vorteile**
- Direkte Zuordnung zu Organisation möglich, ggf. auch Forschungsthemen oder -projekte
- Kontaktdaten vsl. an einem Ort
- Daten über Mitarbeiter sind in der Regel aktuell
- Auseinanderhalten von unterschiedlichen Personen gut möglich, da unwahrscheinlich, dass zwei Personen mit exakt gleichem Namen bei derselben Organisation arbeiten
- Hat man die Homepage eines Mitarbeiters, kommt man auch gut an Publikationslisten etc.

**Nachteile**
- Benötigt HTML-Verarbeitung und wsl. Vorverarbeitung (z.B. Organization Mining)
- HTML-Parsing setzt eher auf Heuristiken denn auf NLP

**Pipeline**
1. Eingabe: <u>HTML</u> der Seite inkl. Titel
   - Möglichst ohne Dinge, die häufig vorkommen (Header, Footer)
   - Möglichst ohne Navigationselemente
   - Rausfiltern von speziellen Tags wie `<pre>`
1. Herausfinden, ob die Seite eine Liste (über HTML oder über die Anzahl an Namen) mit mehreren Personennamen (über NER) enthält => falls ja: Annahme, dass es sich hierbei um Mitarbeiterliste handelt (ggf. gepaart mit Schlüsselwörtern wie "Mitarbeiter", "Team", "Staff", "Wissenschaftliche Mitarbeiter")
   - Von hier den Links zu den Detailseiten zu den Mitarbeitern folgen
   - Alternativ direkt Detailseiten finden (z.B. über `h1` oder `head/title`)
1. Auf der Detailseite zu Mitarbeitern nach weiteren Informationen schauen
   - Keyword Extraction liefert Forschungsthemen
   - Links oder andere Namen führen zu Forschungsprojekten
   - Regex für Mailadressen
   - Foto

## Allgemeine Notizen

- Für beide Ansätze wird NER benötigt
- Ehemalige, Alumni und (studentische) Hilfskräfte sollten gefiltert werden.
- Verwaltung sollte gefiltert werden.
- Kann mit dem Organization Mining verbunden werden. Beispiel: Ein Lehrstuhl hat immer genau einen Professor als Leitung. Etwas, bei dem 4 Professoren sind, muss eine höhergeordnete Organisation sein.
- Wie halten wir es mit Titeln (Dr., Prof.)?
- **Normalisierung** der Namen
   - Ohne akademischen Titel
   - Ohne Diakritika (z.B. á), allerdings mit deutschen Umlauten (ä, ü, ö) und ß
- Schwierigkeit: Wie erkennen wir Personen, die gleich heißen, aber in unterschiedlichen Gebieten vorkommen?
   - Ähnlichkeit der URL? Ähnlichkeit des Kontexts?
