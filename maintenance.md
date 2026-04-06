# Code Maintenance Report

## Code-Analyse: Redundanzen & Spaghetti-Code

### StatISTIK

- **Python-Code (apps/):** 4.826 Zeilen
- **Templates (HTML):** 2.167 Zeilen
- **Gesamt:** ~7.000 Zeilen

---

## Redundanzen (Wiederholungen)

| Kategorie | Fundstellen | Aufwand zur Behebung |
|-----------|-------------|---------------------|
| `max_length=20` | 6+ Felder in verschiedenen Apps | Niedrig |
| FEDERAL_STATES | accounts/ und core/ (inkonsistent) | Niedrig |
| Last day of month | hr/services.py:242 + hr/services.py:433 | Niedrig |
| WorkSchedule queries | 4 Stellen in hr/overtime/absences | Mittel |
| OvertimeBalance Berechnung | absences/services.py:112 + overtime/services.py | Mittel |
| Federal state extraction | 4x identisches getattr-Pattern | Niedrig |

### Detaillierte Fundstellen

#### 1. Duplicate Field Definitions
- `absences/models.py:47` — status max_length=20
- `timesessions/models.py:25` — status max_length=20
- `accounts/models.py:35` — employment_type max_length=20
- `accounts/models.py:42` — role max_length=20
- `core/models.py:31` — actor_role max_length=20

#### 2. Federal State Extraction Pattern
```python
getattr(getattr(user, "userprofile", None), "federal_state", "BY")
```
- hr/services.py:234, 429
- overtime/services.py:24
- absences/services.py:78

#### 3. WorkSchedule Query Pattern
```python
.filter(effective_from__year__lte=year, effective_to__isnull=True)
.filter(effective_from__year__lte=year, effective_to__year__gte=year)
```
- hr/services.py:297-308, 468-475
- overtime/services.py:29-34
- absences/services.py:18-24

#### 4. TimeEntry Status Filtering
```python
status__in=["COMPLETED", "AUTO_CLOSED", "MANUAL"]
```
- hr/services.py:342-348
- overtime/services.py:50-56

---

## Spaghetti-Code (Handlungsbedarf)

| File | Problem | Zeilen |
|------|---------|--------|
| hr/views.py | hr_dashboard - 78 Zeilen, mischt Business-Logik mit Presentation | 42-119 |
| hr/views.py | Wiederholt OvertimeCalculator, calculate_vacation_entitlement 6+ mal | 77, 181, 702 |
| timesessions/views.py | dashboard - berechnet vacation/overtime inline | 14-28 |
| timesessions/views.py | correct_entry - Time-Validation im View | 110-154 |
| api/v1/views.py | Redundante Service-Imports | mehrfach |

### Nested Conditionals (> 3 Ebenen)
- hr/views.py:hr_dashboard — for loop + if/elif/else
- hr/views.py:employee_create — POST + form.is_valid() + while loop

### Business Logic in Views
- hr/views.py:66-104 — Balance-Berechnung inline
- hr/views.py:139-146 — Username-Generierung
- hr/views.py:180-199 — Inline Balance-Berechnung

---

## Empfohlene Refactorings

### 1. Zentralisierung (Kurzfristig)
- [ ] `MAX_LENGTH_STATUS = 20` als Konstante in `core/constants.py`
- [ ] `FEDERAL_STATES` nach `core/constants.py` verschieben
- [ ] `get_federal_state(user)` Utility-Funktion erstellen
- [ ] `get_last_day_of_month(year, month)` Utility-Funktion

### 2. Service-Extraktion (Mittelfristig)
- [ ] `hr/views.py:hr_dashboard` → `EmployeeOverviewService` extrahieren
- [ ] `User.get_overtime_balance()` als Model-Methode
- [ ] `User.get_vacation_status()` als Model-Methode

### 3. Query-Methoden (Mittelfristig)
- [ ] `AbsenceRequest.objects.current_today()`
- [ ] `AbsenceRequest.objects.pending_for_user(user)`
- [ ] `TimeEntry.objects.currently_clocked_in()`
- [ ] `TimeEntry.objects.completed_in_range(start, end)`

### 4. Model Manager (Langfristig)
- [ ] WorkScheduleManager mit `at_date(date)` Methode
- [ ] OvertimeAccountManager mit `get_or_create_for_user(user)`

---

## Geschätzter Aufwand

| Refactoring | Aufwand |
|-------------|---------|
| Konstanten zentralisieren | 2-4 Stunden |
| Utility-Funktionen | 4-6 Stunden |
| Query-Methoden | 6-8 Stunden |
| Service-Extraktion hr/views | 8-12 Stunden |
| **Gesamt** | **20-30 Stunden** |

---

## Priorisierung

1. **Sofort:** Federal state extraction Utility (wird 4x wiederholt)
2. **Kurzfristig:** Konstanten zentralisieren
3. **Mittelfristig:** Query-Methoden in Manager auslagern
4. **Langfristig:** hr/views.py refaktorisieren

---

## Erstellt am

April 2026
