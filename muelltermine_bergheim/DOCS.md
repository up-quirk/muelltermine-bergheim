# Einrichtung und Bedienung

## Erststart

Nach der Installation **Starten** und dann **Weboberfläche öffnen** wählen. Der Abruf läuft im Hintergrund. Die Oberfläche ist über Ingress in Home Assistant eingebettet und verwendet dessen Anmeldung.

Die App verwendet zunächst „Bergheim und Kenten“, Datenformat PDF und die offizielle Stadtwerke-Übersichtsseite. Pro Tag wird die Seite neu gelesen, damit auch Änderungen an Dateinamen und nachträgliche PDF-Versionen erkannt werden. Ab Oktober werden das aktuelle und das nächste Kalenderjahr getrennt geladen.

## Suchregeln testen

1. Oben das gewünschte Dokument auswählen. Der neueste PDF-Kalender wird zunächst vorausgewählt.
2. Eine Tonne links auswählen. Suchmuster als regulären Ausdruck eingeben; nach 350 Millisekunden Tipp-Pause erscheinen rechts die Treffer.
3. Rechts sind Datum, Originaltext mit Markierungen und PDF-Seite sichtbar. „Alle Tonnen“ zeigt auch kombinierte Abholungen. Unter „Original-PDF“ lässt sich die Datei ansehen.
4. Anzeigename, Groß-/Kleinschreibung, Farbe und Aktivierung können je Tonne geändert werden. Die Kennung muss eindeutig bleiben.
5. **Speichern und übernehmen** aktiviert alle geänderten Regeln und Einstellungen. Die Kalenderausgabe wird unmittelbar neu berechnet.

Ein ungültiger Ausdruck zeigt eine Fehlermeldung und wird nicht übernommen. Rechenzeit und Musterlänge sind begrenzt. Eine Regel darf nicht schon den leeren Text treffen.

Beispiele:

| Tonne | Suchmuster | Zweck |
| --- | --- | --- |
| Restmüll | `(?:^| / )Hausmüll(?:$| / )` | Normale Hausmülltonne; schließt die ausgeschriebenen Großcontainer aus |
| Bio | `Biotonne` | Auch in kombinierten Abholungen |
| Papier | `blaue Tonne` | Auch gemeinsam mit Bio |
| Gelb | `gelbe To(?:nne)?\.?` | Erfasst auch abgeschnittene PDF-Beschriftungen wie „gelbe To“ |
| Große Container | `(?:^| / )C(?:$| / )|Hausmüll 770` | Optionale zusätzliche Regel für die wöchentliche Abholung |

Die Standardregeln arbeiten ohne Beachtung der Groß-/Kleinschreibung. PDF-Texte und ICS-Beschriftungen können unterschiedlich sein; bei einem Wechsel des Datenformats die Vorschau erneut prüfen.

## Eigene PDF-Datei testen

**Eigenes PDF testen** wählen, Kalenderjahr angeben und eine PDF-Datei bis 20 MB hochladen. Die Datei bleibt als Testdokument gespeichert. Ein Upload ersetzt keine automatisch heruntergeladene Kalenderquelle. Die Regeln werden gegen dieses Dokument getestet, aber beim Speichern auf die aktiven heruntergeladenen Kalender angewendet.

## Download-Einstellungen

Unter **Abruf & Einstellungen**:

- **Stadtteil:** Bezeichnung auf der Stadtwerke-Seite. Bisher vollständig geprüft: Bergheim und Kenten.
- **Kalenderübersichtsseite:** Öffentliche HTTPS-Seite mit PDF-/ICS-Links.
- **Datenformat:** PDF, ICS oder automatisch (ICS bevorzugt, PDF als Ersatz).
- **Folgejahr suchen ab:** Monat für die zusätzliche Suche; vorgeschlagen Oktober.
- **PDF-/ICS-URL-Muster:** Ersatz für die Linksuche. Eine vollständige feste URL ist ebenfalls möglich.
- **Downloadlinks zusätzlich filtern:** Optionaler regulärer Ausdruck auf die gefundenen Download-URLs.

Unterstützte Platzhalter in URL-Mustern:

| Platzhalter | Bedeutung |
| --- | --- |
| `{year}` | Kalenderjahr, etwa 2027 |
| `{publication_year}` | Vorjahr und Kalenderjahr werden probiert, etwa 2026 und 2027 |
| `{month}` | Upload-Monate von 12 bis 01, zweistellig |

Beispiel: `https://swbm.de/wp-content/uploads/{publication_year}/{month}/Bergheim_Abfallkalender_{year}.pdf`.

Links von der Übersichtsseite haben Vorrang. Die URL-Muster greifen, wenn keine passende Datei geladen werden konnte. Nach Änderungen **Speichern und übernehmen**, dann **Kalender abrufen** wählen. Der tägliche Abruf erfolgt alle 24 Stunden ab App-Start; ein manueller Abruf ist jederzeit möglich.

Bei fehlendem Folgejahr oder Netzwerkfehlern bleiben die letzten gültigen Dokumente und Termine erhalten. Status und Fehlermeldungen sind in der Oberfläche und im App-Protokoll sichtbar. Ein neues Dokument muss zum angegebenen Kalenderjahr passen und eine vollständige Jahrestabelle enthalten.

## Home-Assistant-Kalender

Der lesende Anschluss ist standardmäßig `8098/tcp`; die Portzuordnung lässt sich auf der Netzwerkseite der App ändern. Er liefert:

- `/calendar.ics`: Ganztägige Termine, stabile Ereigniskennungen, eigene Ereignisse für jede Tonne.
- `/api/calendar`: JSON mit Terminen und Status.
- `/healthz`: Zustand des HTTP-Dienstes.

Zum Beispiel in Waste Collection Schedule über die Oberfläche die generische ICS-Quelle und `http://DEINE-HA-ADRESSE:8098/calendar.ics` verwenden. Die Quelle veröffentlicht vergangene und zukünftige Termine der gespeicherten aktiven Jahre; die Kalenderintegration entscheidet, welche davon angezeigt werden.

Der Anschluss ist ohne Anmeldung lesbar. Die Portzuordnung kann deaktiviert werden, wenn der Kalender zunächst nur in der App geprüft werden soll. Der Editor-Port 8099 wird nicht auf den Host veröffentlicht.

## Speicherung und Sicherung

Die App speichert `config.json`, `documents.json`, `status.json` und Dokumente samt extrahierten Datensätzen in `/data`. Dieses Verzeichnis bleibt über Neustarts und App-Updates erhalten und wird im Home-Assistant-App-Backup berücksichtigt. Es enthält keine Zugangsdaten. Die normale Supervisor-Konfiguration enthält nur `log_level`; alle fachlichen Einstellungen sind in der eingebetteten Oberfläche.

## Grenzen

Keine OCR: Gescannte PDFs werden abgelehnt. Bei geänderter Tabellenstruktur muss der Parser angepasst werden. Die Jahreskalender sind die veröffentlichte Planung der Stadtwerke und können kurzfristige Sondermeldungen außerhalb der Kalenderdateien nicht berücksichtigen.
