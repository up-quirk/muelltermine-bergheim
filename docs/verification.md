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

## Noch gesondert zu prüfen

Der lokale Docker-Daemon startet auf dem Entwicklungssystem nicht; WSL meldet keine installierte Distribution. Ein erfolgreicher lokaler Linux-Containerbuild wurde deshalb noch nicht nachgewiesen. Die GitHub-Prüfkonfiguration baut beide angegebenen Architekturen und führt die Python-Prüfungen unter Linux aus. Ergebnisse einer Supervisor-Installation werden hier nachgetragen.

Andere Stadtteile, gescannte PDFs und abweichende Tabellenlayouts sind nicht mit eigenen Beispielen verifiziert. Die App ist als experimentell gekennzeichnet.
