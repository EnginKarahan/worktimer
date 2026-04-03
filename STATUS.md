# Arbeitszeit-App – Aktueller Stand (02.04.2026)

## Infrastruktur

| Komponente | Details |
|---|---|
| Server | Hetzner, erreichbar via Tailscale als `alhambra-cloud` |
| App-URL | https://time.alhambra-gesellschaft.de |
| Nextcloud | https://cloud.alhambra-gesellschaft.de (externer Hoster) |
| Container | `arbeitszeit` (docker compose in `/opt/infrastruktur/arbeitszeit/`) |
| DB | MariaDB im Container `arbeitszeit_db` |
| Deployment | `git pull origin master` + `docker compose restart arbeitszeit` |

## Implementierte Features

### Rollensystem
- `UserProfile.role` (EMPLOYEE / HR / ADMIN) + `UserRole`-Modell für Mehrfachrollen
- Migrations: `0002_userprofile_role.py`, `0003_userrole.py`, `0004_seed_userroles.py`
- `apps/core/permissions.py`: `get_active_role()`, `get_role()`, `hr_required`, `IsHROrAdmin`
- `apps/core/context_processors.py`: `user_role`, `user_roles`, `user_roles_display` in allen Templates
- Session-basierter Rollenwechsel: `POST /accounts/switch-role/`
- `base.html`: Rolle-Switcher-Dropdown (nur bei mehreren Rollen), HR-Nav-Link

### HR-App (`apps/hr/`)
- Dashboard (`/hr/`): Heute Abwesend, Jetzt eingestempelt, Offene Anträge
- Mitarbeiterverwaltung: Liste, Erstellen, Detail, Bearbeiten, Deaktivieren (Soft-Delete)
- Zeitkorrektur für Mitarbeiter durch HR
- Krankmeldung durch HR (`/hr/employees/<pk>/sick/`)
- Abwesenheitsgenehmigung/-ablehnung
- PDF/Excel-Berichte pro Mitarbeiter und Monat

### Abwesenheiten
- `LeaveType`-Seed-Data: Urlaub, Krank, Sonderurlaub, Unbezahlt, Überstundenausgleich
- `calculate_vacation_entitlement()`: Berücksichtigt Eintrittsdatum, §4 BUrlG Wartezeit, Wochenarbeitstage
- Urlaubssaldo in: Abwesenheitsliste, Dashboard, HR-Mitarbeiterdetail

### Zeitkorrektur
- `TimeEntry`-Felder: `is_manual_correction`, `corrected_by`, `correction_reason`, `original_start/end_time`
- `CorrectionService`: Korrekturfenster 7 Tage (Mitarbeiter) / 90 Tage (HR) / unbegrenzt (Admin)

### Audit-Log
- `AuditLog.actor_role`: Aktive Rolle wird bei jeder Aktion gespeichert
- Aktionen: `employee_created/updated/deactivated`, `absence_approved/rejected`, `sick_leave_entered_by_hr`, `time_entry_corrected`, `report_downloaded`

### Login / SSO
- Tailwind-gestylte Login-/Logout-Seiten (`templates/account/login.html`, `logout.html`)
- Nextcloud OIDC-Integration konfiguriert (`.env`: `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_SERVER_URL`)
- Button „Mit Nextcloud anmelden" → `/accounts/oidc/nextcloud/login/`
- `OIDCAccountAdapter`: Auto-Verknüpfung per E-Mail beim ersten Login

### Hilfe-Handbücher
- `/help/` → rollenbasiertes Template (Mitarbeiter / HR / Admin)

## Offene Punkte / Bekannte Probleme

### Nextcloud OIDC – noch nicht vollständig getestet
- Client muss in Nextcloud unter `settings/admin/user_oidc` angelegt sein (NICHT unter Sicherheit → OAuth 2.0)
- Redirect-URI: `https://time.alhambra-gesellschaft.de/accounts/oidc/nextcloud/login/callback/`
- Nach Klick auf „Mit Nextcloud anmelden" → Bestätigungsseite → Fortfahren → Nextcloud-Autorisierung

### Doppelte User-Accounts
- In der DB existieren 3 Accounts mit identischem Namen/E-Mail:
  - `admin` (engin.karahan@alhambra-gesellschaft.de)
  - `enginkarahan` (engin.karahan@alhambra-gesellschaft.de) ← vermutlich OIDC-erstellt
  - dritter Account (karahan@alhambra-gesellschaft.de)
- Bereinigung nötig: Duplikate über Django-Admin `/admin/` löschen, einen Account als primär festlegen

### Login-Sperre zurücksetzen (falls nötig)
```bash
docker exec -it arbeitszeit python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Deployment-Befehle

```bash
# Standard-Deploy
cd /opt/infrastruktur/arbeitszeit && git pull origin master && docker compose restart arbeitszeit

# Migrations ausführen
docker exec arbeitszeit python manage.py migrate

# Superuser anlegen (falls noch keiner vorhanden)
docker exec -it arbeitszeit python manage.py createsuperuser

# Logs (nur Startup, kein Access-Log konfiguriert)
docker logs arbeitszeit --tail 50
```

## Bekannte Bugs (behoben)

| Bug | Fix |
|---|---|
| `/absences/new/` Dropdown leer | Data-Migration `0002_seed_leavetypes.py` |
| Login-Template ungestylt | `templates/account/login.html` mit Tailwind |
| `|split`-Filter in `employee_detail.html` → 500 | Hardcodierte `<option>`-Tags |
| Nextcloud-Button falsche URL | Direktlink `/accounts/oidc/nextcloud/login/` |
| `UserRoleInline` falscher FK | `fk_name="user"` auf `CustomUserAdmin` |
