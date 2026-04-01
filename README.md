# Arbeitszeit — Self-Hosted Time Tracking for Alhambra

A Django-based time tracking and absence management system built for the Alhambra team as a self-hosted replacement for Kimai. It runs on a Hetzner CPX31 server (Ubuntu 24.04) behind Nginx and is embedded as an iFrame in the team's Nextcloud instance.

---

## Features

- **Live timer** — clock in / pause / resume / clock out with real-time elapsed display (HTMX + Alpine.js)
- **Manual time entries** — add, edit, and delete past entries with full audit trail
- **Absence management** — vacation, sick leave, special leave, overtime compensation; multi-step approval workflow with email notifications
- **Overtime accounting** — automatic monthly settlement (actual vs. target minutes); year-end carry-over
- **Public-holiday awareness** — per-federal-state holiday calendar seeded via `workalendar`; target-hours calculation skips holidays
- **ArbZG compliance** — §3/§4/§5 checks enforced on every clock-out (break auto-correction, daily max, 11 h rest period)
- **Reports** — PDF (WeasyPrint) and Excel (openpyxl) monthly export per user
- **REST API** — token + session auth, rate-limited endpoints for timer and report actions
- **SSO** — Nextcloud OIDC via `django-allauth`; existing users auto-linked by e-mail
- **Audit log** — every state change stored with actor, old/new values, and IP address
- **Background tasks** — Celery + Celery Beat with 6 scheduled jobs (see below)
- **Multilingual UI** — German (default), English, Turkish

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Django 5.1 |
| REST API | Django REST Framework |
| Frontend interaction | HTMX + Alpine.js |
| Database | MariaDB 10.11 |
| Cache / sessions | Redis 7 |
| Authentication | django-allauth (OIDC / OpenID Connect) |
| Task queue | Celery + Celery Beat + django-celery-beat |
| PDF export | WeasyPrint |
| Excel export | openpyxl |
| Holiday data | workalendar |
| Application server | Gunicorn (3 workers) |
| Containerisation | Docker |
| Runtime | Python 3.12-slim |

---

## Project Structure

```
arbeitszeit-app/
├── apps/
│   ├── accounts/          # UserProfile, WorkSchedule, OIDC adapter
│   ├── absences/          # AbsenceRequest, LeaveType, approval service, tasks
│   ├── api/
│   │   └── v1/            # DRF views and URL routing
│   ├── core/              # TimestampedModel, AuditLog, Holiday, middleware
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_holidays.py
│   │   ├── tests/
│   │   │   └── test_german_law.py
│   │   └── utils/
│   │       ├── german_law.py   # §3/§4/§5 ArbZG logic
│   │       └── holiday_utils.py
│   ├── overtime/          # OvertimeAccount, OvertimeTransaction, calculator, tasks
│   ├── projects/          # Project model (FK on TimeEntry)
│   ├── reports/
│   │   └── services/
│   │       ├── pdf_service.py
│   │       └── excel_service.py
│   └── timesessions/      # TimeEntry, TimerService, tasks
├── config/
│   ├── celery.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── base.py
│       ├── development.py
│       └── production.py
├── locale/                # i18n PO/MO files (de, en, tr)
├── templates/
├── static/
├── Dockerfile
├── docker-compose.dev.yml     # Local development stack
├── docker-compose.yml         # Production reference (merged into /opt/infrastruktur)
└── .env.example
```

---

## Local Development

### Prerequisites

- Docker and Docker Compose (v2)
- A copy of `.env` based on `.env.example`

### Setup

```bash
# 1. Clone and enter the project
cd ~/Dokumente/.../Arbeitszeit/arbeitszeit-app

# 2. Create local environment file
cp .env.example .env
# Edit .env — leave OIDC_* empty for local dev (password login works without SSO)

# 3. Start all services
docker compose -f docker-compose.dev.yml up --build

# 4. Apply migrations (first run only)
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# 5. Seed public holidays (first run only)
docker compose -f docker-compose.dev.yml exec web python manage.py seed_holidays

# 6. Create a superuser
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

The application is then available at **http://localhost:8000**.
Django Admin: **http://localhost:8000/admin/**.

### docker-compose.dev.yml — Services

| Service | Image / Command | Port |
|---|---|---|
| `db` | mariadb:10.11 | (internal) |
| `redis` | redis:7-alpine | (internal) |
| `web` | `python manage.py runserver 0.0.0.0:8000` | 8000 |
| `celery` | `celery -A config worker -l info --concurrency=2` | — |
| `celery_beat` | `celery -A config beat -l info --scheduler django_celery_beat...` | — |

The `web` service mounts the project directory as a volume so code changes are reflected immediately without rebuilding.

---

## Deployment on Server

**Server:** `admin@alhambra.cloud`
**Production directory:** `/opt/infrastruktur/`
**Exposed port:** `8040` (mapped to Gunicorn's 8000 internally)

The production stack is part of a shared `docker-compose.yml` at `/opt/infrastruktur/`. The `docker-compose.yml` in this repository is a reference snippet to be merged into that file.

### Step-by-Step

```bash
# 1. SSH into the server
ssh admin@alhambra.cloud

# 2. Navigate to the infrastructure directory
cd /opt/infrastruktur

# 3. Pull latest application code
cd arbeitszeit
git pull origin master

# 4. Rebuild and restart only the Arbeitszeit containers
docker compose build arbeitszeit arbeitszeit_celery arbeitszeit_celery_beat
docker compose up -d arbeitszeit arbeitszeit_celery arbeitszeit_celery_beat

# 5. Run migrations
docker compose exec arbeitszeit python manage.py migrate

# 6. Collect static files (also runs during image build, but safe to repeat)
docker compose exec arbeitszeit python manage.py collectstatic --noinput

# 7. Verify health endpoint
curl http://localhost:8040/health/
# Expected: {"status": "ok"}
```

### Production Container Overview

| Container | Role |
|---|---|
| `arbeitszeit` | Gunicorn — 3 workers, port 8040 |
| `arbeitszeit_celery` | Celery worker — concurrency 2 |
| `arbeitszeit_celery_beat` | Celery Beat (database scheduler) |

Watchtower auto-updates are disabled (`com.centurylinklabs.watchtower.enable=false`) — deployments are always manual.

Static and media files are bind-mounted from the host:

```
/opt/infrastruktur/data/arbeitszeit/static  →  /app/static
/opt/infrastruktur/data/arbeitszeit/media   →  /app/media
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values before starting any container.

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.development` or `config.settings.production` |
| `DJANGO_SECRET_KEY` | yes | Long random string — generate with `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DJANGO_ALLOWED_HOSTS` | yes (prod) | Comma-separated hostnames, e.g. `alhambra.cloud,localhost` |
| `DB_HOST` | yes | Database hostname (Docker service name or IP) |
| `DB_NAME` | yes | Database name (default: `arbeitszeit`) |
| `DB_USER` | yes | Database user |
| `DB_PASSWORD` | yes | Database password |
| `REDIS_URL` | yes | Redis URL for cache and result backend, e.g. `redis://redis:6379/1` |
| `CELERY_BROKER_URL` | yes | Redis URL for Celery broker, e.g. `redis://redis:6379/2` |
| `OIDC_CLIENT_ID` | prod | Client ID registered in Nextcloud OAuth2 |
| `OIDC_CLIENT_SECRET` | prod | Client secret from Nextcloud |
| `OIDC_SERVER_URL` | prod | Nextcloud base URL, e.g. `https://cloud.alhambra-gesellschaft.de` |
| `NEXTCLOUD_BASE_URL` | prod | Same as `OIDC_SERVER_URL` |
| `COMPANY_NAME` | no | Shown in reports (default: `Alhambra`) |
| `FEDERAL_STATE` | no | Two-letter state code for holidays (default: `BY` = Bavaria) |
| `EMAIL_HOST` | no | SMTP host (default: `localhost`) |
| `EMAIL_PORT` | no | SMTP port (default: `25`) |
| `EMAIL_HOST_USER` | no | SMTP user |
| `EMAIL_HOST_PASSWORD` | no | SMTP password |
| `DEFAULT_FROM_EMAIL` | no | Sender address for system mails |

---

## Celery Tasks

All tasks are discovered automatically via `app.autodiscover_tasks()`. Schedules are stored in the database and managed through Django Admin > Periodic Tasks (django-celery-beat).

| Task | Module | Cron / Trigger | Description |
|---|---|---|---|
| `auto_clock_out_forgotten` | `apps.timesessions.tasks` | Daily 23:50 | Closes all `RUNNING`/`PAUSED` entries at 23:55; sends notification e-mail to affected users |
| `notify_manager_new_request` | `apps.absences.tasks` | On demand (`.delay()`) | E-mails the manager when an employee submits an absence request |
| `notify_user_approved` | `apps.absences.tasks` | On demand (`.delay()`) | E-mails the employee when their absence request is approved or rejected |
| `check_medical_cert_required` | `apps.absences.tasks` | Daily 08:00 | Warns manager and employee when a sick-leave absence reaches day 4 without a medical certificate |
| `vacation_expiry_warning` | `apps.absences.tasks` | 1 February, yearly | Calculates remaining vacation days from the previous year and warns users about imminent expiry (beyond the configured carry-over limit) |
| `settle_monthly_overtime` | `apps.overtime.tasks` | 1st of each month 06:00 | Computes actual vs. target working minutes for all active users for the previous month and writes an `OvertimeTransaction`; idempotent via `get_or_create` |
| `year_end_overtime_carryover` | `apps.overtime.tasks` | 1 January 05:00 | Records the carry-over of the previous year's overtime balance; idempotent via `get_or_create` on `reference_month` |

---

## API Endpoints

Base path: `/api/v1/`
Authentication: session cookie or `Authorization: Token <token>` header.
Rate limit: 30 requests/minute per user on write endpoints; 10/minute on report endpoints.

| Method | Path | Description |
|---|---|---|
| `POST` | `timer/clock-in/` | Start a new time entry for the authenticated user |
| `POST` | `timer/pause/` | Pause the currently running entry |
| `POST` | `timer/resume/` | Resume a paused entry |
| `POST` | `timer/clock-out/` | Stop the active entry; runs ArbZG checks and triggers overtime task |
| `GET` | `timer/status/` | Return whether the user has an active entry, its status, and elapsed minutes |
| `GET` | `time-entries/` | List the user's time entries (latest 100); filter by `?date=YYYY-MM-DD` |
| `GET` | `absences/` | List the user's absence requests (latest 50) |
| `POST` | `absences/` | Submit a new absence request (`leave_type_code`, `start_date`, `end_date`, `reason`) |
| `POST` | `absences/<id>/approve/` | Approve an absence request (manager or staff only) |
| `POST` | `absences/<id>/reject/` | Reject an absence request (manager or staff only) |
| `GET` | `overtime/balance/` | Return the user's current overtime balance in minutes and hours |
| `GET` | `reports/monthly/` | Download a PDF monthly report; params: `?year=YYYY&month=M` |

Additional system endpoints (no auth required):

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/` | Liveness check — returns `{"status": "ok"}` |
| `GET/POST` | `/admin/` | Django admin interface |
| `*` | `/accounts/` | django-allauth login / OIDC callback routes |

---

## Running Tests

```bash
# Inside the dev stack
docker compose -f docker-compose.dev.yml exec web python manage.py test

# Run only the ArbZG law tests
docker compose -f docker-compose.dev.yml exec web python manage.py test apps.core.tests.test_german_law

# With verbosity
docker compose -f docker-compose.dev.yml exec web python manage.py test --verbosity=2
```

Tests use Django's standard `TestCase`. No pytest is required. The test suite currently covers:

- `apps.core.tests.test_german_law` — §3/§4/§5 ArbZG boundary values (14 test cases)

---

## Important Design Decisions

### ArbZG Limits (German Working Hours Act)

The file `apps/core/utils/german_law.py` is the single source of truth for all statutory limits:

| Rule | Threshold | Effect |
|---|---|---|
| §4 ArbZG — minimum break | Work > 6 h: 30 min; Work > 9 h: 45 min | `clock_out` auto-corrects `break_minutes` if below the required minimum; an `AuditLog` entry records the correction |
| §3 ArbZG — daily maximum | Warning at > 8 h net; Error at > 10 h net | Violation stored as JSON in `TimeEntry.violations_json`; shown in UI |
| §5 ArbZG — rest period | < 11 h between consecutive days | Warning violation generated when consecutive entries are checked |

Violations are never blocking for the user — they are stored and displayed as warnings/errors after the fact so compliance can be audited.

### iFrame Settings (Nextcloud Embed)

The application is embedded in Nextcloud via an iFrame. To allow cross-origin framing:

- `X_FRAME_OPTIONS` is set to `""` (empty string — Django does not emit the header)
- `SECURE_FRAME_DENY = False`
- `CSRF_TRUSTED_ORIGINS` includes `https://cloud.alhambra-gesellschaft.de`
- `SESSION_COOKIE_SAMESITE = "Lax"` — allows the cookie to be sent on top-level navigations from Nextcloud

SSL termination is handled by Nginx on the host; `SECURE_SSL_REDIRECT = False` and `SECURE_PROXY_SSL_HEADER` is set to trust the `X-Forwarded-Proto` header.

### Idempotency of Celery Tasks

Recurring financial/accounting tasks (`settle_monthly_overtime`, `year_end_overtime_carryover`) use `OvertimeTransaction.objects.get_or_create(... reference_month=ref ...)`. Re-running the task for the same month or year produces no duplicate records. This makes it safe to manually re-trigger tasks or restart a failed Celery Beat without corrupting balances.

---

## Nextcloud Integration

### OIDC Single Sign-On Setup

1. **In Nextcloud Admin** — go to *Security > OAuth 2.0 Clients* and add a new client:
   - **Redirect URI:** `https://<your-domain>:8040/accounts/oidc/nextcloud/login/callback/`
   - Note the generated **Client ID** and **Client Secret**.

2. **In the Django `.env`** — set:
   ```
   OIDC_CLIENT_ID=<client-id>
   OIDC_CLIENT_SECRET=<client-secret>
   OIDC_SERVER_URL=https://cloud.alhambra-gesellschaft.de
   ```

3. **In Django Admin** — ensure a `Site` record exists for your domain under *Sites*.

4. The `OIDCAccountAdapter` (`apps/accounts/adapters.py`) automatically links an incoming OIDC login to an existing Django user if the e-mail address matches (`pre_social_login`). New users are provisioned automatically (`SOCIALACCOUNT_AUTO_SIGNUP = True`) with `given_name` and `family_name` populated from the OIDC token.

5. The login button on the login page redirects to `/accounts/oidc/nextcloud/login/` which initiates the PKCE-enabled authorization code flow.

### iFrame Embed in Nextcloud

Use the **Nextcloud "External Sites" app** or a custom dashboard widget:

1. Install the *External Sites* app from the Nextcloud app store.
2. Add a new site:
   - **Name:** Arbeitszeit
   - **URL:** `https://alhambra.cloud:8040/` (or the domain if behind a reverse proxy without port)
   - **Icon:** choose a clock icon
   - **Show in:** Navigation / Dashboard as preferred
3. Because `X-Frame-Options` is suppressed on the Django side, the iFrame will load without browser security errors.
4. Users must be logged in via OIDC first; the session cookie (`SameSite=Lax`) is carried into the iFrame on same-origin navigations.

> **Note:** If users experience login loops inside the iFrame, ensure Nginx passes `X-Forwarded-Proto: https` and that `SESSION_COOKIE_SECURE = True` in production settings.
