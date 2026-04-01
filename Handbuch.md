# Handbuch: Arbeitszeit-Tool der Alhambra-Gesellschaft

**Version:** April 2026
**Zielgruppe:** Alle Mitarbeiterinnen und Mitarbeiter
**System:** arbeitszeit.alhambra-gesellschaft.de

---

Willkommen beim Arbeitszeit-Tool der Alhambra-Gesellschaft. Dieses System ersetzt das bisherige Kimai und ermöglicht es Ihnen, Ihre Arbeitszeiten einfach zu erfassen, Urlaub zu beantragen und Ihre Stunden jederzeit einzusehen — alles auf einem Blick.

Dieses Handbuch erklärt Ihnen Schritt für Schritt, wie das System funktioniert. Sie benötigen kein technisches Vorwissen.

---

## Inhaltsverzeichnis

**Für alle Mitarbeiter**
1. [Anmeldung](#1-anmeldung)
2. [Einstempeln](#2-einstempeln)
3. [Pause](#3-pause)
4. [Ausstempeln](#4-ausstempeln)
5. [Zeiteinträge anzeigen und korrigieren](#5-zeiteinträge-anzeigen-und-korrigieren)
6. [Urlaub beantragen](#6-urlaub-beantragen)
7. [Krankmeldung eintragen](#7-krankmeldung-eintragen)
8. [Überstundenkonto](#8-überstundenkonto)
9. [Berichte herunterladen](#9-berichte-herunterladen)
10. [Mein Profil](#10-mein-profil)

**Für Manager**
11. [Urlaubsanträge genehmigen oder ablehnen](#11-urlaubsanträge-genehmigen-oder-ablehnen)
12. [Team-Kalender](#12-team-kalender)
13. [Überstunden im Blick behalten](#13-überstunden-im-blick-behalten)

**Für Administratoren**
14. [Neuen Mitarbeiter anlegen](#14-neuen-mitarbeiter-anlegen)
15. [Arbeitszeitpläne pflegen](#15-arbeitszeitpläne-pflegen)
16. [Feiertage](#16-feiertage)
17. [Monatliche Berichte für den Steuerberater](#17-monatliche-berichte-für-den-steuerberater)
18. [Kimai-Übergangszeit](#18-kimai-übergangszeit)

**[Häufige Fragen (FAQ)](#häufige-fragen-faq)**

---

# Für alle Mitarbeiter

---

## 1. Anmeldung

### Wie melde ich mich an?

Sie benötigen **keinen neuen Benutzernamen und kein neues Passwort**. Das Arbeitszeit-Tool nutzt Ihren bestehenden **Nextcloud-Account** (cloud.alhambra-gesellschaft.de).

**Es gibt zwei Wege, das Tool zu öffnen:**

**Weg 1 — über Nextcloud (empfohlen):**
1. Melden Sie sich wie gewohnt bei Nextcloud an: [cloud.alhambra-gesellschaft.de](https://cloud.alhambra-gesellschaft.de)
2. Klicken Sie in der linken Navigationsleiste auf den Eintrag **"Arbeitszeiten"** — dieser erscheint als eigene Seite direkt in Nextcloud.
3. Das Arbeitszeit-Tool öffnet sich, ohne dass Sie sich erneut anmelden müssen.

**Weg 2 — direkt im Browser:**
1. Rufen Sie [arbeitszeit.alhambra-gesellschaft.de](https://arbeitszeit.alhambra-gesellschaft.de) auf.
2. Sie sehen eine Schaltfläche **"Mit Nextcloud anmelden"** (oder ähnlich). Klicken Sie darauf.
3. Sie werden kurz zu Nextcloud weitergeleitet, bestätigen dort (falls nötig) die Anmeldung, und werden automatisch zurückgeleitet.
4. Ab diesem Moment sind Sie im Arbeitszeit-Tool angemeldet.

### Was passiert beim allerersten Login?

Beim ersten Mal wird automatisch ein Konto für Sie angelegt. Ihr Name und Ihre E-Mail-Adresse werden aus Nextcloud übernommen — Sie müssen nichts eingeben. Ihre Urlaubstage und Arbeitszeitplan sind bereits von der Verwaltung eingetragen.

> **Tipp:** Wenn Sie sich über Nextcloud anmelden, bleiben Sie dauerhaft eingeloggt, solange Sie Nextcloud geöffnet haben.

---

## 2. Einstempeln

Einstempeln bedeutet: Sie teilen dem System mit, dass Sie jetzt mit der Arbeit beginnen.

### Schritt für Schritt

1. Öffnen Sie das Arbeitszeit-Tool (siehe Abschnitt 1).
2. Sie befinden sich auf der **Startseite (Dashboard)**. Oben sehen Sie eine große Uhr oder einen Timer-Bereich.
3. Klicken Sie auf den grünen Button **"Einloggen"** oder **"Arbeit starten"**.
4. Der Button wechselt die Farbe und zeigt nun an, wie lange Sie bereits arbeiten — zum Beispiel: *"Seit 08:02 Uhr — 00:15:34"*.
5. Das System hat Ihre Startzeit gespeichert. Sie müssen nichts weiter tun.

**Was bedeuten die Buttons?**
- **Grüner Button "Arbeit starten"** — startet die Zeiterfassung
- **Gelber Button "Pause"** — hält die Zeit an (Pausenmodus)
- **Roter Button "Ausstempeln"** — beendet Ihren Arbeitstag

> **Hinweis:** Sie können immer nur einmal gleichzeitig eingestempelt sein. Wenn Sie versehentlich versuchen, nochmals einzustempeln, zeigt das System einen Hinweis: *"Sie sind bereits eingestempelt."*

---

## 3. Pause

### Pause starten

1. Klicken Sie während der Arbeitszeit auf den gelben Button **"Pause"**.
2. Der Timer stoppt. Das System zeigt an: *"Pause gestartet."*
3. Die Zeit, die Sie pausieren, wird als Pausenzeit gezählt — nicht als Arbeitszeit.

### Pause beenden

1. Klicken Sie auf den grünen Button **"Arbeit fortsetzen"** (erscheint, wenn Sie pausieren).
2. Das System zeigt an: *"Arbeit fortgesetzt."* Der Timer läuft wieder.

### Was passiert, wenn ich vergesse, die Pause zu beenden?

Wenn Sie auf "Pause" geklickt haben aber vergessen, auf "Fortsetzen" zu klicken, und danach auf "Ausstempeln" drücken, zählt die gesamte Zwischenzeit als Pause. Sie sollten den Zeiteintrag anschließend korrigieren (siehe Abschnitt 5).

### Die gesetzliche Pausenregel — was ist das?

Das System prüft beim Ausstempeln automatisch, ob Ihre Pause den gesetzlichen Anforderungen entspricht (§ 4 Arbeitszeitgesetz). Die Regeln sind:

| Arbeitszeit | Mindestpause |
|-------------|-------------|
| Bis 6 Stunden | Keine Pflicht |
| Mehr als 6 Stunden | 30 Minuten |
| Mehr als 9 Stunden | 45 Minuten |

Das Gute: Sie müssen diese Regeln nicht selbst im Kopf behalten. Das System prüft sie automatisch (mehr dazu in Abschnitt 4).

---

## 4. Ausstempeln

### Schritt für Schritt

1. Klicken Sie am Ende Ihrer Arbeitszeit auf den roten Button **"Ausstempeln"**.
2. Das System speichert Ihre Endzeit und berechnet Ihre heutige Arbeitszeit.
3. Sie sehen eine Bestätigung: *"Ausgestempelt!"*

### Die automatische Pausenkorrektur — einfach erklärt

Beim Ausstempeln schaut das System, wie lang Ihr Arbeitstag war und wie viel Pause Sie gemacht haben. Falls Ihre eingetragene Pause kürzer war als die gesetzlich vorgeschriebene Mindestpause, **verlängert das System Ihre Pause automatisch**.

**Beispiel:** Sie arbeiten 7 Stunden, haben aber nur 20 Minuten Pause gemacht. Gesetzlich sind mindestens 30 Minuten Pflicht. Das System setzt Ihre Pause automatisch auf 30 Minuten — Ihre anrechenbare Arbeitszeit beträgt dadurch 6 Stunden 30 Minuten statt 6 Stunden 40 Minuten.

**Warum macht das System das?** Das schützt sowohl Sie als auch das Unternehmen. Arbeitgeber sind gesetzlich verpflichtet, dafür zu sorgen, dass die Mindestpausen eingehalten werden.

**Was sehe ich davon?** In Ihrem Zeiteintrag (Abschnitt 5) sehen Sie die korrigierte Pausenzeit. Falls eine Korrektur stattgefunden hat, erscheint ein Hinweis bei dem betreffenden Eintrag.

### Warnung bei langen Arbeitstagen

Falls Sie mehr als 8 Stunden netto gearbeitet haben, zeigt das System eine **gelbe Warnung**. Bei mehr als 10 Stunden erscheint eine **rote Warnung**. Das ist nur ein Hinweis — Ihr Eintrag wird trotzdem gespeichert.

---

## 5. Zeiteinträge anzeigen und korrigieren

### Wo finde ich meine Zeiten?

1. Klicken Sie in der Navigation oben (oder im Menü) auf **"Meine Zeiten"** oder **"Zeiteinträge"**.
2. Sie sehen eine Liste aller Ihrer Einträge — mit Datum, Startzeit, Endzeit, Pausenzeit und der berechneten Arbeitszeit.
3. Die aktuellsten Einträge stehen oben.

**Was bedeuten die Status-Angaben?**
- **Läuft** — Sie sind gerade eingestempelt
- **Pausiert** — Sie sind im Pausenmodus
- **Abgeschlossen** — normal ausgestempelt
- **Automatisch geschlossen** — das System hat Sie um 23:55 Uhr ausgestempelt, weil Sie es vergessen haben (Sie erhalten in diesem Fall eine E-Mail)
- **Manuell eingetragen** — ein Eintrag wurde nachträglich von Hand erstellt oder geändert

### Kann ich einen Eintrag korrigieren?

Ja. Wenn Sie einen Fehler bemerken (falsche Startzeit, falsche Pausenzeit), wenden Sie sich bitte an Ihren **Manager oder Administrator**. Dieser kann den Eintrag im System anpassen. Korrekturen werden im System protokolliert.

> **Hinweis:** Aus Datenschutz- und Revisionsgründen können Mitarbeiter ihre eigenen Einträge nicht selbst verändern. Die Korrektur erfolgt immer durch einen Vorgesetzten oder die Verwaltung.

---

## 6. Urlaub beantragen

### Schritt für Schritt

1. Klicken Sie im Menü auf **"Abwesenheiten"** oder **"Urlaub beantragen"**.
2. Klicken Sie auf die Schaltfläche **"Neuen Antrag stellen"**.
3. Wählen Sie den **Typ** aus dem Auswahlfeld:
   - **Urlaub** — regulärer Jahresurlaub
   - **Sonderurlaub** — z. B. Hochzeit, Beerdigung
   - **Überstundenausgleich** — freie Tage, die mit Überstunden verrechnet werden
   - **Unbezahlter Urlaub**
4. Tragen Sie das **Startdatum** und das **Enddatum** ein.
5. Optional: Schreiben Sie eine kurze **Begründung** (freiwillig, außer bei Sonderurlaub).
6. Klicken Sie auf **"Antrag einreichen"**.

### Was passiert danach?

- Das System berechnet automatisch, wie viele Arbeitstage Ihr Urlaubsantrag umfasst (Feiertage und Wochenenden werden herausgerechnet).
- Ihr Manager erhält eine **Benachrichtigung** per E-Mail.
- Der Antrag erscheint in Ihrer Liste mit dem Status **"Ausstehend"**.
- Sobald Ihr Manager entschieden hat, erhalten Sie eine E-Mail und der Status ändert sich auf **"Genehmigt"** oder **"Abgelehnt"**.

### Was, wenn ich keinen Manager zugewiesen habe?

Dann wird Ihr Antrag automatisch genehmigt. Das System zeigt in der Begründung *"Auto-genehmigt (kein Manager zugewiesen)"*.

### Wann kann ich keinen Urlaub beantragen?

Das System prüft vor dem Einreichen, ob Sie noch genug Urlaubstage haben. Wenn nicht, erhalten Sie eine Fehlermeldung wie: *"Nicht genug Urlaub: 3,0 Tage verfügbar."* In diesem Fall müssen Sie entweder weniger Tage beantragen oder mit der Verwaltung sprechen.

---

## 7. Krankmeldung eintragen

Eine Krankmeldung tragen Sie genauso ein wie einen Urlaubsantrag, nur mit dem Typ **"Krankheit"**.

### Schritt für Schritt

1. Klicken Sie im Menü auf **"Abwesenheiten"** > **"Neuen Antrag stellen"**.
2. Wählen Sie als Typ: **"Krankheit"**.
3. Tragen Sie den ersten und (wenn bereits bekannt) letzten Krankheitstag ein.
4. Klicken Sie auf **"Antrag einreichen"**.

> **Wichtig:** Krankmeldungen werden im Gegensatz zum Urlaub nicht von Ihrem Urlaubskonto abgezogen. Sie benötigen dafür auch keine Genehmigung — der Eintrag wird automatisch bestätigt.

**Bitte denken Sie daran:** Die Pflicht zur Vorlage einer ärztlichen Krankschreibung ab dem dritten Tag gilt weiterhin — das System ersetzt diese nicht. Die Krankmeldung im Tool dient nur der internen Zeiterfassung.

---

## 8. Überstundenkonto

### Was ist das Überstundenkonto?

Das Überstundenkonto zeigt Ihnen, wie viele Überstunden Sie bisher angesammelt (oder abgebaut) haben. Es ist gewissermaßen Ihr "Stunden-Sparbuch".

### Wo finde ich es?

1. Klicken Sie im Menü auf **"Überstunden"**.
2. Sie sehen Ihren aktuellen **Saldo** — zum Beispiel: *"+12,5 Stunden"* oder *"−2,0 Stunden"*.
3. Darunter sehen Sie eine detaillierte **Auflistung aller Buchungen**, zum Beispiel:
   - *"Monatsabrechnung März 2026: +4 Stunden"*
   - *"Überstundenausgleich: −8 Stunden"*

### Wie wird das Überstundenkonto berechnet?

Am Ende jeden Monats rechnet das System automatisch ab: Es vergleicht, wie viele Stunden Sie laut Ihrem Arbeitszeitplan arbeiten sollten (**Soll-Stunden**) mit den tatsächlich geleisteten Stunden (**Ist-Stunden**). Die Differenz wird Ihrem Überstundenkonto gutgeschrieben oder abgezogen.

**Beispiel:** Ihr Soll für März war 168 Stunden, gearbeitet haben Sie 172 Stunden — es werden 4 Überstunden gutgeschrieben.

### Was zählt ins Konto?

- **Gutschriften (+):** Monatliche Abrechnungen, bei denen Sie mehr als Ihre Soll-Stunden gearbeitet haben
- **Abzüge (−):** Überstundenausgleich-Urlaub, manuelle Korrekturen durch die Verwaltung, Jahresüberträge

---

## 9. Berichte herunterladen

Sie können sich jederzeit einen **Monatsnachweis** als PDF oder Excel-Datei herunterladen — zum Beispiel zur eigenen Kontrolle oder auf Anfrage.

### Schritt für Schritt

1. Klicken Sie im Menü auf **"Berichte"**.
2. Wählen Sie das **Jahr** und den **Monat**, für den Sie einen Bericht möchten.
3. Klicken Sie auf:
   - **"PDF herunterladen"** — erzeugt ein druckfertiges Dokument mit allen Ihren Zeiteinträgen des Monats
   - **"Excel herunterladen"** — erzeugt eine Tabelle, die Sie weiter bearbeiten können

Die Datei wird automatisch heruntergeladen. Der Dateiname enthält Ihren Namen und den Zeitraum, z. B.: `arbeitszeitnachweis_2026_03_musterfrau.pdf`

> **Hinweis:** Um Missbrauch zu verhindern, können Sie maximal 10 Berichte pro Minute herunterladen.

---

## 10. Mein Profil

### Wo finde ich mein Profil?

Klicken Sie im Menü oben rechts auf Ihren Namen oder auf **"Profil"**.

### Was steht in meinem Profil?

Ihr Profil zeigt:
- **Name und E-Mail** — aus Nextcloud übernommen
- **Beschäftigungsart** — z. B. Vollzeit, Teilzeit, Minijob, Praktikant
- **Wöchentliche Arbeitsstunden** — Ihr vertraglich vereinbartes Stundenpensum
- **Urlaubsanspruch pro Jahr** — z. B. 30 Tage
- **Einstellungsdatum**
- **Bundesland** — relevant für die automatische Feiertagsberechnung (Standard: Bayern)
- **Mein Arbeitszeitplan** — welche Stunden pro Wochentag erwartet werden
- **Vorgesetzter (Manager)** — wer für Ihre Urlaubsgenehmigungen zuständig ist

### Was kann ich selbst ändern?

Aktuell kann die Profilinformation nur von der Verwaltung (Administration) geändert werden. Wenn Sie eine Korrektur benötigen — z. B. weil Ihre Wochenarbeitszeit sich geändert hat — wenden Sie sich an Ihren Ansprechpartner in der Verwaltung.

---

# Für Manager

---

## 11. Urlaubsanträge genehmigen oder ablehnen

Als Manager werden Sie per **E-Mail benachrichtigt**, sobald eines Ihrer Teammitglieder einen Urlaubsantrag einreicht.

### Über die E-Mail

Die E-Mail enthält einen direkten Link zum Antrag. Klicken Sie darauf und Sie gelangen direkt zur Entscheidungsansicht (Sie müssen sich ggf. zuerst anmelden).

### Über die Abwesenheitsliste

1. Klicken Sie im Menü auf **"Abwesenheiten"**.
2. Sie sehen alle Anträge Ihres Teams. Anträge mit dem Status **"Ausstehend"** warten auf Ihre Entscheidung.
3. Klicken Sie auf einen Antrag.
4. Sie sehen:
   - Name des Mitarbeiters
   - Urlaubszeitraum und Anzahl der Tage
   - Ggf. eine Begründung
5. Klicken Sie auf **"Genehmigen"** oder **"Ablehnen"**.
6. Optional: Tragen Sie einen **Kommentar** ein (z. B. den Grund für eine Ablehnung).
7. Bestätigen Sie Ihre Entscheidung.

Der Mitarbeiter wird automatisch per E-Mail über Ihre Entscheidung informiert.

> **Tipp:** Wenn Sie mehrere Anträge gleichzeitig genehmigen möchten, können Sie das über den Django-Admin tun (Abschnitt 14). Wählen Sie mehrere Anträge aus und nutzen Sie die Aktion **"Ausgewählte Anträge genehmigen"**.

---

## 12. Team-Kalender

Der Team-Kalender zeigt Ihnen auf einen Blick, wer wann abwesend ist.

### So öffnen Sie den Team-Kalender

1. Klicken Sie im Menü auf **"Abwesenheiten"** > **"Team-Kalender"**.
2. Sie sehen alle **genehmigten** Abwesenheiten Ihres Teams — sortiert nach Datum.
3. Die Ansicht zeigt: Name, Abwesenheitstyp (Urlaub, Krankheit etc.) und Zeitraum.

Der Kalender ist rein informativ und zeigt nur genehmigte Abwesenheiten. Ausstehende oder abgelehnte Anträge werden hier nicht angezeigt.

---

## 13. Überstunden im Blick behalten

Als Manager können Sie die Überstundenkonten Ihrer Teammitglieder einsehen.

Wenden Sie sich hierfür an den Administrator, der Ihnen entsprechenden Zugang einrichten kann, oder sehen Sie sich die Berichte der einzelnen Mitarbeiter an (Abschnitt 9).

Im **Django-Admin-Bereich** (arbeitszeit.alhambra-gesellschaft.de/admin/) können Manager mit erweiterten Rechten die Überstunden-Transaktionen aller Teammitglieder einsehen und ggf. manuelle Korrekturen beantragen.

---

# Für Administratoren

---

## 14. Neuen Mitarbeiter anlegen

Neue Mitarbeiter können sich selbst nicht registrieren — sie müssen von einem Administrator angelegt werden.

### Schritt für Schritt

1. Öffnen Sie den Admin-Bereich: [arbeitszeit.alhambra-gesellschaft.de/admin/](https://arbeitszeit.alhambra-gesellschaft.de/admin/)
2. Klicken Sie auf **"Benutzer"** (unter dem Abschnitt "Authentifizierung und Autorisierung").
3. Klicken Sie oben rechts auf **"Benutzer hinzufügen"**.
4. Tragen Sie ein:
   - **Benutzername** — am besten identisch mit dem Nextcloud-Benutzernamen
   - **E-Mail-Adresse** — muss mit der Nextcloud-E-Mail übereinstimmen (wichtig für den automatischen Login!)
   - **Vorname und Nachname**
5. Speichern Sie den Benutzer.

**Anschliessend das Profil anlegen:**

6. Klicken Sie auf **"Mitarbeiterprofile"** (unter dem Abschnitt "Accounts").
7. Klicken Sie auf **"Mitarbeiterprofil hinzufügen"**.
8. Wählen Sie den soeben erstellten Benutzer aus.
9. Füllen Sie aus:
   - **Wöchentliche Arbeitsstunden** (z. B. 40 für Vollzeit, 20 für halbe Stelle)
   - **Jahresurlaub in Tagen** (z. B. 30)
   - **Einstellungsdatum**
   - **Beschäftigungsart** (Vollzeit, Teilzeit, Minijob, Praktikant)
   - **Bundesland** (Standard: Bayern — BY)
   - **Manager** — wählen Sie den Vorgesetzten aus, der Urlaubsanträge genehmigt
10. Speichern.

> **Wichtig:** Die E-Mail-Adresse im System muss exakt mit der E-Mail-Adresse im Nextcloud-Account übereinstimmen. Nur so funktioniert das automatische Verknüpfen beim ersten Login.

---

## 15. Arbeitszeitpläne pflegen

Der **Arbeitszeitplan** legt fest, an welchen Wochentagen und wie viele Minuten ein Mitarbeiter arbeiten soll. Er ist die Grundlage für die Überstundenberechnung.

### Arbeitszeitplan anlegen oder ändern

1. Öffnen Sie den Admin-Bereich.
2. Klicken Sie auf **"Arbeitszeitpläne"** (unter "Accounts").
3. Klicken Sie auf **"Arbeitszeitplan hinzufügen"**.
4. Wählen Sie den **Mitarbeiter** aus.
5. Tragen Sie die Minuten pro Wochentag ein:
   - Beispiel Vollzeit (8h/Tag): Montag bis Freitag je **480 Minuten**, Samstag/Sonntag **0**
   - Beispiel Teilzeit (4h/Tag): Montag bis Freitag je **240 Minuten**
6. Tragen Sie das **Gültig ab**-Datum ein (z. B. den ersten Tag des neuen Vertrags).
7. Falls der Plan irgendwann endet, tragen Sie auch **Gültig bis** ein. Lassen Sie das Feld leer, wenn der Plan unbegrenzt gilt.
8. Speichern.

**Mehrere Pläne möglich:** Ein Mitarbeiter kann mehrere Arbeitszeitpläne haben — z. B. wenn sich seine Stunden geändert haben. Das System verwendet immer den Plan, der zum jeweiligen Datum passt.

**Schnell-Referenz: Stunden in Minuten**

| Stunden/Tag | Minuten |
|-------------|---------|
| 4 Stunden | 240 |
| 5 Stunden | 300 |
| 6 Stunden | 360 |
| 7 Stunden | 420 |
| 8 Stunden | 480 |
| 8,5 Stunden | 510 |

---

## 16. Feiertage

Feiertage werden vom System **automatisch berücksichtigt** — Sie müssen nichts manuell eintragen.

Das System ist auf das Bundesland **Bayern (BY)** eingestellt und berücksichtigt automatisch alle bayerischen Feiertage, z. B. Heilige Drei Könige (6. Januar), Mariä Himmelfahrt (15. August), Allerheiligen (1. November) und andere.

An Feiertagen werden keine Soll-Stunden berechnet. Wenn ein Mitarbeiter an einem Feiertag arbeitet, werden diese Stunden vollständig als Überstunden gebucht.

> **Für Mitarbeiter in anderen Bundesländern:** Das Bundesland kann im Mitarbeiterprofil individuell eingestellt werden (Abschnitt 14, Feld "Bundesland"). Das System berechnet dann die Feiertage für das jeweilige Bundesland.

---

## 17. Monatliche Berichte für den Steuerberater

Am Ende jeden Monats (oder auf Anfrage) können Sie Arbeitszeitnachweise für alle Mitarbeiter als PDF oder Excel-Datei herunterladen.

### Einzelner Bericht (für einen Mitarbeiter)

Jeder Mitarbeiter kann seinen eigenen Monatsbericht selbst herunterladen (Abschnitt 9). Als Administrator können Sie dasselbe für jeden Benutzer tun, indem Sie sich als dieser Benutzer einloggen oder den Bericht über den Admin-Bereich abrufen.

### Batch-Export (für mehrere Mitarbeiter gleichzeitig)

1. Öffnen Sie den Admin-Bereich.
2. Klicken Sie auf **"Abwesenheitsanträge"** (unter "Absences").
3. Um die monatliche Überstundenabrechnung für alle Mitarbeiter auszulösen, wenden Sie sich an den technischen Administrator — dieser führt den Monatsabschluss-Job aus.

> **Hinweis:** Die monatliche Überstundenberechnung läuft automatisch als Hintergrundaufgabe. Falls für einen bestimmten Monat noch keine Abrechnung vorliegt, kann der Administrator den Job manuell anstoßen.

### Was enthält der Bericht?

Der Monatsbericht enthält:
- Name des Mitarbeiters und Monat/Jahr
- Alle Zeiteinträge des Monats mit Start, Ende, Pause und Netto-Arbeitszeit
- Summe der Ist-Stunden
- Soll-Stunden laut Arbeitsvertrag
- Differenz (Überstunden oder Minusstunden)
- Hinweise auf eventuelle Regelverstöße (z. B. unzureichende Pausen)

---

## 18. Kimai-Übergangszeit

Das neue Arbeitszeit-Tool startet mit einem **sauberen Neuanfang** — es gibt keinen automatischen Import der alten Kimai-Daten.

**Was bedeutet das konkret?**

- Die **alten Kimai-Daten** (Zeiten vor dem Umstieg) bleiben im alten Kimai-System erhalten und können dort weiterhin eingesehen werden. Kimai läuft auf dem Server weiter, wird aber nicht mehr aktiv genutzt.
- Alle **neuen Zeiteinträge** ab dem Startdatum des neuen Systems werden ausschließlich im neuen Tool erfasst.
- Das **Überstundenkonto** beginnt mit dem Startsaldo, den die Verwaltung manuell einträgt (sofern alte Überstunden übernommen werden sollen).

**Falls Sie alte Zeiten aus Kimai benötigen** (z. B. für Abschlussberichte), wenden Sie sich an den Administrator. Die Kimai-Instanz bleibt im Lesemodus verfügbar.

---

# Häufige Fragen (FAQ)

---

### Ich habe vergessen auszustempeln — was nun?

Das System bemerkt das automatisch. Jeden Abend um **23:55 Uhr** prüft das System, ob es noch offene (laufende oder pausierte) Zeiteinträge gibt. Falls ja, schließt es diese automatisch ab und setzt Ihre Endzeit auf 23:55 Uhr.

Sie erhalten dann eine **E-Mail** mit dem Hinweis, dass Ihr Timer automatisch gestoppt wurde, und der Bitte, Ihren Zeiteintrag zu überprüfen.

Was dann zu tun ist: Wenden Sie sich an Ihren Manager oder die Verwaltung und teilen Sie mit, wann Sie tatsächlich aufgehört haben zu arbeiten. Der Eintrag kann dann entsprechend korrigiert werden.

---

### Meine Pause wurde automatisch verlängert — warum?

Das Gesetz schreibt vor, dass Sie bei mehr als 6 Stunden Arbeit mindestens 30 Minuten Pause machen müssen, bei mehr als 9 Stunden mindestens 45 Minuten (§ 4 Arbeitszeitgesetz).

Wenn Ihre tatsächliche Pause kürzer war als diese Mindestzeit, korrigiert das System Ihre Pausenzeit beim Ausstempeln automatisch auf das gesetzliche Minimum. Ihre anrechenbare **Netto-Arbeitszeit** verringert sich dadurch entsprechend.

Das ist keine Bestrafung, sondern eine gesetzliche Vorgabe. Falls Sie in dieser Zeit wirklich gearbeitet haben und die Korrektur falsch ist, wenden Sie sich an Ihren Vorgesetzten.

---

### Ich sehe eine Warnung bei meinem Zeiteintrag — was bedeutet das?

Warnungen (gelbes Ausrufezeichen) und Fehler (rotes Ausrufezeichen) können folgendes bedeuten:

| Symbol | Bedeutung |
|--------|-----------|
| Gelbe Warnung | Sie haben mehr als 8 Stunden gearbeitet — das ist ungewöhnlich, aber nicht verboten |
| Roter Fehler | Sie haben mehr als 10 Stunden netto gearbeitet — das überschreitet das gesetzliche Tageslimit (§ 3 ArbZG) |
| Roter Fehler | Die Pause war nicht ausreichend (wurde aber automatisch korrigiert) |

Warnungen und Fehler werden gespeichert. Bei regelmäßigen Überschreitungen sollte das mit dem Vorgesetzten besprochen werden.

---

### Wo finde ich meinen Resturlaub?

Ihren aktuellen Urlaubssaldo finden Sie in Ihrem **Profil** (oben rechts im Menü auf Ihren Namen klicken) oder in der **Abwesenheitsliste**.

Das System berechnet Ihren Resturlaub so:
**Jahresanspruch** (z. B. 30 Tage) minus **bereits genehmigte Urlaubstage** im laufenden Jahr = **Resturlaub**

> **Hinweis:** Anträge mit dem Status "Ausstehend" werden beim Resturlaub noch nicht abgezogen — erst nach der Genehmigung.

Vom Vorjahr **übertragener Urlaub** wird vom Administrator manuell gutgeschrieben (maximal 5 Tage, sofern im Profil so eingestellt).

---

### Kann ich Zeiten nachträglich korrigieren?

Mitarbeiter können ihre eigenen Zeiten nicht selbst verändern. Bei Bedarf wenden Sie sich an Ihren **Vorgesetzten oder die Verwaltung** und schildern Sie kurz, was korrigiert werden soll (z. B. "Ich war am 15.03. bis 17:30 Uhr, nicht bis 23:55 Uhr"). Die Verwaltung nimmt die Korrektur dann im Admin-Bereich vor.

Alle Korrekturen werden im System protokolliert, damit die Nachvollziehbarkeit gewährleistet bleibt.

---

### Was passiert, wenn ich an einem Feiertag arbeite?

Feiertage werden automatisch erkannt (für Bayern). An einem Feiertag gibt es keine Soll-Stunden. Das bedeutet:

- Wenn Sie an einem Feiertag arbeiten und Ihre Stunden einstempeln, werden **alle geleisteten Stunden als Überstunden** auf Ihr Überstundenkonto gebucht.
- Es wird keine Strafe oder Warnung angezeigt — das System erfasst die Stunden ganz normal.

---

### Ich kann mich nicht einloggen — was tun?

**Schritt 1:** Prüfen Sie, ob Sie sich bei Nextcloud (cloud.alhambra-gesellschaft.de) normal anmelden können. Wenn Nextcloud nicht funktioniert, liegt das Problem dort — sprechen Sie mit Ihrem Nextcloud-Administrator.

**Schritt 2:** Falls Nextcloud funktioniert, aber das Arbeitszeit-Tool Sie nicht einloggt: Öffnen Sie [arbeitszeit.alhambra-gesellschaft.de](https://arbeitszeit.alhambra-gesellschaft.de) direkt im Browser (nicht über Nextcloud) und versuchen Sie den Login erneut.

**Schritt 3:** Falls es immer noch nicht klappt: Wenden Sie sich an die Verwaltung. Möglicherweise ist Ihr Konto im Arbeitszeit-Tool noch nicht angelegt oder Ihre E-Mail-Adresse stimmt nicht mit der Nextcloud-E-Mail überein.

**Häufige Ursache:** Wenn Sie zuletzt Ihre E-Mail-Adresse in Nextcloud geändert haben, muss die Verwaltung die neue E-Mail auch im Arbeitszeit-Tool aktualisieren.

---

*Bei weiteren Fragen wenden Sie sich bitte an Ihre zuständige Ansprechperson in der Verwaltung oder an den Administrator des Systems.*

*Dieses Handbuch wurde erstellt für die Alhambra-Gesellschaft — April 2026.*
