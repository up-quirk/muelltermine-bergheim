# Prüfung 0.3.1 – Bearbeiten und Navigation

33 bestehende Python-Regressionstests bestanden; JavaScript-Syntaxprüfung bestanden.
Die folgenden Abläufe wurden im lokalen Browser mit einem echten PDF-Kalender 2027
und den produktiven HTTP-Endpunkten geprüft:

- Sauberer Anfangsstand: Speichern und Verwerfen deaktiviert. Änderung aktiviert
  beide; Rückänderung auf denselben Wert deaktiviert sie wieder.
- Regeln, Bereich, URL-Muster und MQTT-Passwort geändert, zwischen den Ansichten
  gewechselt und zurückgekehrt: Entwurf bleibt erhalten. Verwerfen setzt alles
  auf den gespeicherten Stand, leert Passwortfeld und stellt die 26 Restmüll-
  Vorschautermine wieder her. Server-Konfiguration bleibt unverändert.
- Browser-Zurück und expliziter Rückweg funktionieren mit sichtbarer Ansicht.
- Verzögerte Speicherantwort: nachfolgende Eingabe bleibt als ungespeicherter
  Entwurf erhalten. Verwerfen lädt den tatsächlich gespeicherten Zwischenstand.
- Fehlgeschlagenes Speichern: Eingabe bleibt erhalten, beide Aktionen wieder
  verfügbar. Ungültiges Suchmuster wird nicht auf dem Server übernommen.
- Verzögerte Quellsuche nach erfolgreichem Verwerfen: altes Ergebnis ignoriert.
- Laufende Quellsuche und fehlgeschlagenes Verwerfen: Eingabe bleibt erhalten und
  Suchbutton wird wieder aktiv. Dieser im Review gefundene Fehler ist korrigiert.
- Desktop 1440 px und Mobil 390 px visuell geprüft; kein horizontaler Überlauf.
  Speichern/Verwerfen bleiben beim Scrollen sichtbar. Verwerfen verwendet
  #F3DED0 mit Schrift #713E2A (berechneter Kontrast 6,67:1 im aktiven Zustand).
- Keine JavaScript-Fehler während der erfolgreichen Abläufe. Unabhängiger
  Re-Review ohne verbleibende wesentliche Befunde.

Ein Browser-Suchtest mit künstlich verzögerter Antwort dient nur zur Prüfung
asynchroner Abläufe; er ersetzt nicht die bereits separat getestete Linksuche.
