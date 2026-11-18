# Änderungen

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
