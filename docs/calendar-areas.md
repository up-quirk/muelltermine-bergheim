# Kalenderbereiche der Stadtwerke Bergheim

Stand der Prüfung: 19.11.2026, Kalenderjahr 2027.
Quelle: https://swbm.de/geschaeftsfelder/abfallentsorgung/abfallkalender/

Die offizielle Seite bietet 13 Pläne nach Stadtteilen, keine Auswahl nach PLZ:
Ahe; Bergheim und Kenten; Büsdorf; Fliesteden; Glesch; Glessen; Niederaußem;
Oberaußem; Paffendorf; Quadrath-Ichendorf; Rheidt-Hüchelhoven; Thorr; Zieverich.
Bergheim und Kenten teilen sich einen Plan. Die Pläne haben unterschiedliche
Abholtermine, etwa Restmüll am 05.01.2027 für Bergheim/Kenten, 07.01. für Büsdorf,
08.01. für Glesch und 11.01. für Quadrath-Ichendorf.

Alle 13 PDF-Pläne wurden geladen und mit den Standardregeln verarbeitet.
Die originale Glessener Neufassung enthält vier Seiten (davon zwei leer); auf der
zweiten Kalenderseite fehlt die Tagesspalte im Dezember. Die App bestimmt diese
Tage nur, wenn die anderen Monatsspalten derselben Zeile übereinstimmen und der
gedruckte Dezember-Wochentag zum Datum passt. Sonst wird das PDF abgelehnt.

Die offiziellen ICS-Dateien wurden ebenfalls verglichen. Bei drei Bereichen
weichen die veröffentlichten Quellen voneinander ab (ICS enthält einen zusätzlichen
Termin gegenüber PDF):

| Bereich | Datum | Tonne |
|---|---|---|
| Büsdorf | 14.05.2027 | Bio |
| Rheidt-Hüchelhoven | 24.12.2027 | Gelb |
| Zieverich | 28.09.2027 | Restmüll |

Diese Unterschiede werden nicht automatisch zusammengeführt oder korrigiert.
PDF bleibt die Voreinstellung. Die App wertet die ausdrücklich gewählte Quelle
aus; ob die Stadtwerke einen Termin berichtigen, muss dort geklärt werden.
Die Übereinstimmung beider Formate ist keine Voraussetzung zum Verwenden eines
Bereichs. Weitere interne Touren oder eine postalische Zuordnung sind auf der
veröffentlichten Kalenderübersicht nicht ausgewiesen.

## Anpassung bei Portaländerungen

Unter **Einstellungen öffnen** oder **Bereich, PDF & Sensoren**:

1. Kalenderbereich wählen; für neue Bezeichnungen „Anderen Bereich eingeben“.
2. Kalenderübersichtsseite bei geändertem Portalpfad anpassen.
3. Optional „PDF-/ICS-Link-Suchmuster“ als regulären Ausdruck auf Download-URLs
   einschränken. Bereich und Jahr werden zusätzlich automatisch geprüft.
4. Optional eine direkte PDF-URL oder ein URL-Muster als Rückfall eintragen:
   `https://example.org/{publication_year}/{month}/plan_{year}.pdf`.
   Unterstützt: `{year}`, `{publication_year}`, `{month}`.
5. **Downloadlinks suchen** prüft ungespeicherte Eingaben für das gewählte Jahr.
   Es zeigt gefundene Links und zusätzliche Muster-URLs, lädt die PDFs aber nicht
   und verändert keine aktiven Termine. Die aktiven URLs stehen darunter separat.
6. Erst speichern und **Kalender abrufen** aktiviert die neue Konfiguration.

Adress- und Dateinamenänderungen benötigen so kein App-Update. Grundlegend
geänderte PDF-Tabellen oder gescannte Dokumente können weiterhin eine Parser-
Anpassung benötigen; URL-Muster ändern nicht das Dokumentformat.
