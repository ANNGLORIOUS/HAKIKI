# Scam Watch Kenya: Backend (Part 1)

Django + DRF + PostgreSQL + Celery/Redis. Part 1 = project setup, database schema, admin, core logic.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # Windows: copy .env.example .env
```

Generate the two secrets and paste them into `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # FIELD_ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"                                # HMAC_SECRET and SECRET_KEY
```

Database: either install PostgreSQL and create a database, or, for quick local testing, delete the
`DATABASE_URL` line from `.env` and Django will use SQLite.

```sql
CREATE USER scamwatch WITH PASSWORD 'scamwatch';
CREATE DATABASE scamwatch OWNER scamwatch;
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver          # admin at http://localhost:8000/admin/
python manage.py test apps          # 8 tests should pass
```

Redis + Celery are configured but not needed until Part 2 (tasks). Run later with:
`celery -A config worker -l info`

## What is in here

- `apps/core/utils.py`: Kenyan phone normalization, handle/link parsing, HMAC hashing, masking, encryption
- `apps/accounts`: User (phone/email verified flags, role, reputation)
- `apps/listings`: Page, PageLabelHistory, PaymentIdentifier (encrypted + hashed), PagePayment, `compute_label()`
- `apps/submissions`: Report, Evidence (separate status), Vouch, CheckRequest, CopyrightComplaint
- `apps/moderation`: ModerationAction (append-only audit log), Dispute, Appeal

---

# Part 2: API

All endpoints are under `/api/`. Authenticated calls send `Authorization: Token <token>`.

## Auth
| Method | Path | Notes |
|---|---|---|
| POST | `auth/register/` | `{email, password}`. Sends an email code. Returns `{token, user}` |
| POST | `auth/login/` | `{email, password}` |
| POST | `auth/logout/` | |
| GET | `auth/me/` | phone is masked |
| POST | `auth/email/send/`, `auth/email/verify/` | `{code}` |
| POST | `auth/phone/send/`, `auth/phone/verify/` | `{phone}` then `{code}` |

A user must verify **both** phone and email before submitting reports, vouches or copyright complaints.

## Public
| Method | Path | Notes |
|---|---|---|
| GET | `search/?q=` | Handle, profile link, phone, Till, Paybill or account number. Optional `&platform=` |
| GET | `pages/<platform>/<handle>/` | Public profile with label, counts, explanation, safety tips |

Search by number is **exact match only** and returns published-report counts, never the number itself.
Unpublished reports are never counted or shown.

## Submissions (login required)
| Method | Path | Fields |
|---|---|---|
| POST | `reports/` | multipart: `platform, handle, category, description, amount_kes, incident_date, payment_type, payment_value, registered_name, whatsapp_number, files[] (1-6), kinds[]` |
| GET | `me/reports/` | Track your reports |
| POST | `vouches/` | multipart: `platform, handle, comment, proof` |
| POST | `check-requests/` | `{platform, handle, note}` (any logged-in user) |
| POST | `copyright-complaints/` | `{platform, handle, original_url, infringing_url, description}` |
| POST | `pages/<platform>/<handle>/claim/` | Returns a code to put in the bio. A moderator approves it in admin |

Files: JPG/PNG/WebP up to 10 MB (reports also allow MP4 up to 25 MB). Images are re-encoded to remove
EXIF/GPS data and renamed randomly.

## Disputes and moderation
| Method | Path | Who |
|---|---|---|
| POST | `reports/<id>/dispute/` | Verified page owner |
| POST | `disputes/<id>/appeal/` | Same owner, once |
| POST | `moderation/disputes/<id>/decide/` | Moderator: `{decision: remains|modified|removed, note}` |
| POST | `moderation/appeals/<id>/decide/` | A **different** moderator |

Everything else moderators do (publish/reject reports, review evidence, approve vouches and claims) is in
`/admin/` and is written to the audit log.

## Making a moderator
`python manage.py shell`, then:
```python
from apps.accounts.models import User
u = User.objects.get(email="you@example.com"); u.role = "moderator"; u.is_staff = True; u.save()
```

## Trying it locally
```bash
python manage.py migrate
python manage.py runserver
```
Verification codes print in the terminal running `runserver` (console email/SMS backends).
With `CELERY_EAGER=True` in `.env`, background tasks run inline, so Redis isn't needed yet.
For real Celery: `celery -A config worker -l info`.

## Not built yet (later parts)
Real SMS in production (Africa's Talking code is written but untested), the moderator web dashboard
(Django admin is used for now), signed evidence URLs in a moderator view, periodic re-review task.
