# Mülltermine Bergheim

Eigenständige Home-Assistant-App mit automatischem Kalenderabruf und einer Werkstatt für PDF-Suchregeln.

- PDF-Kalender von den Stadtwerken automatisch finden, täglich aktualisieren und ab Oktober nach dem Folgejahr suchen.
- Links Suchmuster bearbeiten, rechts Treffer mit Datum, hervorgehobenem Text und PDF-Seite sehen.
- Erst **Speichern und übernehmen** aktiviert Änderungen. Die Vorschau verwendet denselben Parser wie der Kalender.
- PDF-/ICS-URLs, URL-Muster, Stadtteil und Tonnen über die eingebettete Oberfläche konfigurieren.
- ICS- und JSON-Kalender über einen ausschließlich lesenden Anschluss bereitstellen.

## Installation

[![Repository in Home Assistant hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fup-quirk%2Fmuelltermine-bergheim)

1. Dieses Repository unter **Einstellungen → Apps → App installieren → Repositories** hinzufügen:
   `https://github.com/up-quirk/muelltermine-bergheim`
2. **Mülltermine Bergheim** installieren und starten.
3. **Weboberfläche öffnen** wählen. Beim ersten Start werden die Kalender automatisch abgerufen.
4. Die Treffer prüfen und die gewünschten Regeln speichern.

Home Assistant OS mit Supervisor; Architekturen `aarch64` und `amd64`. Der Supervisor baut Version 0.1.0 lokal aus dem Dockerfile. Die Installation kann daher einige Minuten dauern.

## Kalender verwenden

Die App bietet standardmäßig:

- `http://DEINE-HA-ADRESSE:8098/calendar.ics` – iCalendar-Abonnement, etwa für die generische ICS-Quelle in Waste Collection Schedule.
- `http://DEINE-HA-ADRESSE:8098/api/calendar` – JSON mit Terminen und Abrufstatus.

Port 8098 liefert ausschließlich Kalenderdaten und benötigt keine Anmeldung. Nur im vertrauenswürdigen lokalen Netz bereitstellen; keine Portweiterleitung ins Internet einrichten. Der Editor läuft separat über Home Assistant Ingress. Die App benötigt weder Supervisor- noch Home-Assistant-API-Zugriff und keinen Zugriff auf deine `configuration.yaml`.

Eine bestehende Müllkonfiguration kann während der Einrichtung parallel laufen. Für die spätere Umstellung Quelle und Sensoren gemeinsam prüfen; bisherige Einträge erst danach entfernen. Individuelle YAML-Muster können in die Regelfelder übernommen werden.

## Unterstützte PDFs

Textbasierte Bergheimer Jahreskalender mit sechs Monaten pro Seite. Die veröffentlichten Dateien für **Bergheim und Kenten 2026 und 2027** wurden vollständig nach Datum und Tonnenart geprüft. Andere Stadtteile sind auswählbar, aber noch nicht mit eigenen Dateien verifiziert. Gescannte oder strukturell anders aufgebaute PDFs werden mit einer Fehlermeldung abgelehnt.

Standardregeln: Restmüll, Gelbe Tonne, Biotonne und Papier. Große 770-/1.100-Liter-Container werden von der normalen Restmüllregel ausgeschlossen. Zusätzliche Tonnen lassen sich über **+ Tonne** ergänzen.

[Ausführliche Anleitung](muelltermine_bergheim/DOCS.md) · [Design](docs/design.md) · [Entwicklungsprüfungen](docs/verification.md)

## Entwicklung

```powershell
uv venv --python 3.12
uv pip install -r muelltermine_bergheim/requirements.txt
uv pip install -e .
.venv/Scripts/python tools/fetch_fixtures.py
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python muelltermine_bergheim/run.py --local --data-dir data --editor-port 18099 --feed-port 18098
```

Im lokalen Modus bindet der Editor nur an `127.0.0.1`. Unter Linux die entsprechenden Programme in `.venv/bin/` verwenden. Im Browser `http://127.0.0.1:18099/` öffnen.

Parser, Zuordnung und Kalenderexport haben keine Home-Assistant-Abhängigkeit. Dadurch kann die Datenquelle später in eine Integration übernommen werden; die eigene Regelwerkstatt bleibt eine App-Funktion.

## Lizenz und Daten

Der Programmcode steht unter der MIT-Lizenz. Die Kalenderdaten stammen von den [Stadtwerken Bergheim](https://swbm.de/geschaeftsfelder/abfallentsorgung/abfallkalender/). Die Original-PDFs und ICS-Dateien werden nicht in diesem Repository veröffentlicht; für Prüfungen werden sie von der offiziellen Quelle heruntergeladen. Die MIT-Lizenz bezieht sich auf den Programmcode, nicht auf die Stadtwerke-Dokumente.
