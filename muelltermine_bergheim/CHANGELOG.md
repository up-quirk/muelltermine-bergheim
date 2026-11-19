# Änderungen

## 0.3.1

- „Änderungen verwerfen“ lädt gespeicherte Regeln und Einstellungen samt Vorschau neu.
- Speichern und Verwerfen sind nur bei Änderungen aktiv und bleiben beim Scrollen erreichbar.
- Navigation getrennt von Kalenderaktionen, klare Ansichtstitel und Zurück-Schaltflächen.
- Browser-Zurück und Ansichtswechsel erhalten ungespeicherte Eingaben.
- Mobile Anordnung und Behandlung verspäteter Antworten verbessert.

## 0.3.0

- Deutliche Auswahl der 13 offiziellen Kalenderbereiche und Eingabe eigener Bereiche.
- Direkter Einstieg „Bereich & PDF-Suche“, Erklärung der automatischen Suche und Anzeige aktiver Quellen.
- PDF-/ICS-Linksuche mit ungespeicherten Einstellungen testen, ohne aktive Kalender zu ändern.
- Glessener PDF 2027 mit fehlender Dezember-Tagesspalte unterstützt.
- Automatische GitHub-Tests und Container-Builds für AMD64 und ARM64 aktiviert.

## 0.2.1

- MQTT-Sensoren stellen die konfigurierte Tonnenfarbe als Attribut `color` bereit.
- Farbänderungen nach dem Speichern werden automatisch übertragen, ohne neue Entitäten anzulegen.

## 0.2.0

- Optionale MQTT Discovery: Sensoren ohne configuration.yaml, gruppiert als Gerät.
- Automatische Broker-Zugangsdaten über Supervisor oder manuelle Verbindung mit TLS.
- Deutsche Terminanzeige, next_date/days_until und Abrufstatus als Attribute.
- Stabile Kennungen, Wiederverbindung, Home-Assistant-Startnachrichten und Verfügbarkeit.
- Bereinigung deaktivierter und gelöschter Tonnen; MQTT-Einstellungen in der Weboberfläche.

## 0.1.0

- Eigenständige Home-Assistant-App für Bergheim und Kenten.
- Automatische PDF-/ICS-Linksuche, täglicher Abruf und frühe Suche nach dem Folgejahr.
- Ingress-Oberfläche mit Live-Vorschau der Suchregeln gegen gespeicherte PDFs.
- Eigene PDF-Dateien zum isolierten Testen hochladen.
- Persistente Einstellungen und letzte gültige Kalenderdaten.
- Ausschließlich lesende ICS- und JSON-Schnittstelle.
