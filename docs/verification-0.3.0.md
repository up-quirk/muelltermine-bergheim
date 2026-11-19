# Prüfung 0.3.0

19.11.2026: 33 lokale automatisierte Tests bestanden, einschließlich PDF-Auswertung
aller 13 Kalenderbereiche für 2027 und Fehlerbehandlung bei fehlenden Dezember-
Wochentagen im Glessener Sonderformat. Vorschau der Downloadquellen mit Entwurfs-
Einstellungen verändert weder Konfiguration noch Dokumente. Bei nicht erreichbarer
Übersichtsseite bleiben Muster-URLs mit einem Warnhinweis sichtbar. HTTP-Schnittstelle
geprüft. JavaScript-Syntaxprüfung bestanden; unabhängiger Review nach zwei
Korrekturen ohne verbleibende wesentliche Befunde.

Browser: Auswahl Ahe, Link-RegEx `Ahe.*2027`, PDF-Muster mit `{year}` ergibt genau
den offiziellen Ahe-PDF-/ICS-Link und die erwartete Ersatz-URL. Vor dem Speichern
bleibt die aktive Konfiguration Bergheim und Kenten. Eigene Bereichseingabe,
Muster-Speicherung und mobile Breite 390 px ohne horizontalen Überlauf geprüft.

GitHub Actions: erster Workflow-Lauf 44481935612 erfolgreich in allen drei Jobs
(Python/JavaScript, linux/amd64, linux/arm64). Die finale App-Fassung wird ebenfalls
vor Veröffentlichung durch denselben Workflow geprüft.

Offizielle Datenquellen und die drei beobachteten Unterschiede zwischen PDF und
ICS sind in calendar-areas.md dokumentiert. Originaldateien werden nicht im
Repository verbreitet; die CI lädt sie über tools/fetch_fixtures.py.
