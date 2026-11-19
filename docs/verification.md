# Prüfstand Version 0.1.0

Stand: 18. November 2026.

## Lokal ausgeführt

- Python 3.12.14 unter Windows, isolierte virtuelle Umgebung mit festgeschriebenen Abhängigkeiten.
- 18 automatisierte Prüfungen bestanden: PDF-/ICS-Parsing, konkrete Abholdaten, Jahresprüfung, ungültige PDFs und reguläre Ausdrücke, Kalenderexport, Downloadlinksuche, Abruffehler, fehlendes Folgejahr, persistente Konfiguration, Entwurfsisolation, fehlerhafte Dateiersetzung, mehrjährige ICS-Quellen, HTTP-Schnittstellen und PNG-Vorschau.
- Offizielle Quellen für Bergheim und Kenten: 2026 Rest 26 / Gelb 26 / Bio 44 / Papier 13; 2027 Rest 26 / Gelb 26 / Bio 43 / Papier 13. Datum-/Tonnenpaare stimmen zwischen PDF und ICS überein.
- Echter automatischer Download: PDFs 2026 und 2027 auf der Stadtwerke-Seite selbst gefunden, 217 aktive Datum-/Tonnenpaare erzeugt, keine Abruffehler.
- Browserprüfung: Desktop 1440 Pixel und Mobil 390 Pixel, Auswahl von Testdokument/Tonne, Vorschauaktualisierung, ungültiges Muster, Standardregeln speichern.
- Konkreter Vorschautest: Restmüll-Muster auf `Biotonne` geändert; Vorschau 43 Treffer, aktive Restmüllausgabe für 2027 weiterhin 26 Termine.
- `node --check` und Python-Kompilierung ohne Fehler.
- Unabhängiges Code-Review; dabei gefundene Fehler mit Regressionstests behoben.

## Prüfung auf Home Assistant

Der Supervisor hat Version 0.1.0 aus dem veröffentlichten Repository erfolgreich als Linux-Container gebaut und installiert. Die App wurde gestartet und hat beide Kalender selbst heruntergeladen. Die Ausgabe enthält 217 Ereignisse, aktive Jahre 2026 und 2027 und keine Abruffehler.

Die Ingress-Schnittstelle wurde auf der installierten App geprüft: Konfiguration lesen (HTTP 200), Entwurfsmuster testen (Restmüllregel auf Biotonne: 43 Vorschau-Treffer) und Originalseite als PNG rendern (HTTP 200, `image/png`). Die aktive Restmüllausgabe für 2027 blieb bei 26 Terminen. Der über das lokale Netzwerk veröffentlichte ICS-Anschluss antwortet mit HTTP 200 und 217 VEVENT-Einträgen.

Die vollständige Browserbedienung wurde lokal geprüft; auf Home Assistant wurde die Ingress-API geprüft. Die zweite deklarierte Prozessorarchitektur wurde nicht separat gebaut. Ein lokaler Docker-Build auf dem Windows-Entwicklungssystem war wegen der dort nicht startenden Docker-/WSL-Umgebung nicht möglich; der erfolgreiche Supervisor-Build ersetzt diesen Laufzeittest auf der vorhandenen HA-Hardware.

## Automatisierung und Grenzen

`docs/verify-workflow.example.yml` enthält eine vorbereitete GitHub-Actions-Konfiguration für Python-Prüfungen und beide Containerarchitekturen. Sie ist keine aktive Workflow-Datei: Die vorhandene GitHub-Anmeldung hat keine `workflow`-Berechtigung, und GitHub lehnte einen Push mit aktiver Workflow-Datei ab. Der App-Code wurde anschließend ohne zusätzliche Kontoberechtigungen veröffentlicht. Die Vorlage kann später mit passender Berechtigung nach `.github/workflows/verify.yml` übernommen werden.

Andere Stadtteile, gescannte PDFs und abweichende Tabellenlayouts sind nicht mit eigenen Beispielen verifiziert. Die App ist als experimentell gekennzeichnet.
# Version 0.2.0 – MQTT Discovery

- 26 Tests bestanden (Python 3.12), einschließlich Terminberechnung, Konfiguration,
  Passwortredaktion, Neustart/Birth, Wiederverbindung, fehlendem Broker, Entfernung
  deaktivierter Tonnen, fehlgeschlagener Veröffentlichung und Passwortrotation.
- JavaScript-Syntaxprüfung bestanden.
- Lokale Browserprüfung: automatische/manuelle Broker-Auswahl, Speichern,
  geleertes Passwortfeld nach Speichern bei weiterhin gespeicherten Zugangsdaten;
  mobile Breite 390 Pixel ohne horizontalen Überlauf; keine JavaScript-Fehler.
- Unabhängiges Review hat zwei Fehler bei Passwortrotation gefunden; korrigiert
  und durch Regressionstest abgesichert.
- Live: Supervisor baut und startet 0.2.0; automatische MQTT-Broker-Erkennung
  funktioniert. Vier Sensoren teilen ein Gerät und liefern gültige Zustände samt
  next_date/days_until. App-Stopp setzt alle vier auf unavailable; nach App-Start
  kehren dieselben Kennungen mit gültigen Werten zurück. 217 Ereignisse, keine
  Abruffehler. Wohnzimmer-Karten umgestellt, REST-YAML entfernt und erfolgreich
  geprüft/neu geladen. Kein Home-Assistant-Core-Neustart erforderlich.
# Version 0.2.1 – Tonnenfarben

27 automatisierte Tests bestanden. Der neue Regressionstest prüft die Übertragung
der Regelfarbe und Farbänderungen bei gleichbleibender Sensor-Kennung. Review ohne
wesentliche Befunde. Supervisor-Update auf 0.2.1 erfolgreich; alle vier Sensoren
liefern `color`. Live-Farbänderung an Gelb über App-Konfiguration → MQTT-Attribut →
HA-Kartenvorlage geprüft; ursprüngliche Farbe #fcdd07 wiederhergestellt.
Dashboard-Symbole, Seitenstreifen und Tönung verwenden jetzt dynamische Attribute;
Vorlagen registrieren Sensor-Listener. Konfiguration gespeichert und zurückgelesen.
Keine visuelle Browserprüfung des HA-Dashboards für dieses Update.
