# Mülltermine Bergheim – freigegebener Umfang

Eigenständige Home-Assistant-App unter `up-quirk/muelltermine-bergheim`. Automatischer Download der Bergheimer Kalender, Suche nach dem Folgejahr ab Oktober, anpassbare Übersichts-URL und Dateimuster. PDF ist die voreingestellte Quelle; ICS kann alternativ ausgewertet werden. Gültige Daten bleiben bei Abruffehlern erhalten.

Die Ingress-Oberfläche bietet links Regeln und rechts Treffer mit Datum, Originaltext und PDF-Seite. Änderungen werden nach kurzer Tipp-Pause gegen das ausgewählte, zwischengespeicherte PDF getestet. Erst „Speichern und übernehmen“ aktiviert sie. Der automatische Betrieb verwendet denselben Parser und dieselbe Regelanwendung.

Konfiguration und Dokumente liegen im persistenten App-Verzeichnis `/data`. Die Weboberfläche verwaltet die fachlichen Einstellungen; die Supervisor-Registerkarte enthält nur Betriebsoptionen. Ein separater, ausschließlich lesender HTTP-Port stellt ICS und JSON für Home Assistant bereit. Der Editor ist nur über Ingress beziehungsweise im lokalen Entwicklungsmodus erreichbar.

Parser, Abfallzuordnung und Kalenderexport haben keine Home-Assistant-Abhängigkeit und können später für einen Integrationsbeitrag wiederverwendet werden. Bestehende Kalender werden während des isolierten Aufbaus nicht ersetzt.

Grenzen: Die PDF-Auswertung unterstützt die textbasierten Bergheimer Tabellen mit sechs Monaten je Seite. Gescannte und strukturell geänderte PDFs werden als Fehler gemeldet. Die Übernahme bestehender individueller YAML-Muster erfordert deren vollständige Aufnahme; bis dahin werden geprüfte Standardregeln geliefert.
