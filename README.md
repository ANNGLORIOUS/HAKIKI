# Hakiki

Hakiki is a scam-reporting and seller-verification platform built to help people check whether a social media seller, payment handle, or business profile is associated with scam reports, evidence, or moderation activity.

The project is split into two main parts:

- Backend: Django + Django REST Framework API
- Frontend: Next.js app for browsing profiles, submitting reports, and managing user flows

The platform allows users to search seller handles, review public profiles, submit reports with evidence, verify identities, and participate in moderation workflows.

## Project overview

Hakiki combines public profile discovery with a review system that supports:

- Search across known handles and payment identifiers
- Public seller pages with labels and safety context
- Report submissions with evidence uploads
- User verification via email and phone OTP
- Claims, vouches, and disputes
- Moderation and audit logging

## Tech stack

### Backend
- Python 3
- Django 5.x
- Django REST Framework
- PostgreSQL (default in production setup)
- SQLite for quick local development
- Celery + Redis for async tasks
- Django storage support for local or S3-compatible object storage
- Cryptography for field encryption and HMAC hashing

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

## Repository structure

```text
HAKIKI/
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── core/
│   │   ├── listings/
│   │   ├── moderation/
│   │   └── submissions/
│   ├── config/
│   ├── media/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   ├── manage.py
│   └── db.sqlite3
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   ├── next.config.mjs
│   └── tailwind.config.ts
├── README.md
└── .gitignore
```

## Backend architecture

The backend is organized into Django apps that model the platform's core flows:

- `apps/accounts`: authentication, verification, user accounts, and roles
- `apps/core`: shared utilities, API helpers, normalization logic, SMS/email handling, and platform-wide services
- `apps/listings`: public pages, labels, payment identifiers, and seller profiles
- `apps/submissions`: reports, evidence, checks, vouches, and complaints
- `apps/moderation`: moderation actions, disputes, appeals, and review workflows

Key behaviors in the backend include:

- normalization of Kenyan phone numbers and social handles
- HMAC hashing for matching identifiers without exposing raw values
- optional encryption of sensitive payment details
- moderation thresholds and audit logs
- public API routes for listing and search behavior

## Frontend architecture

The frontend is a Next.js application that exposes customer-facing workflows such as:

- home and search experience
- profile pages for known sellers
- claim and verification flows
- reporting forms
- login and registration flows
- account pages for submitted reports

The app uses a backend proxy and a small API wrapper layer to communicate with the Django API.

## Local development setup

### 1) Clone the project

```bash
git clone <your-repo-url>
cd HAKIKI
```

### 2) Set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then update `.env` with your local values.

At minimum, set the following secrets:

```env
SECRET_KEY=change-me
FIELD_ENCRYPTION_KEY=<generated key>
HMAC_SECRET=change-me-too
DATABASE_URL=postgres://scamwatch:scamwatch@localhost:5432/scamwatch
REDIS_URL=redis://localhost:6379/0
```

For the encryption key, run:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

A quick local development alternative is to leave the default SQLite setting in place or use the local SQLite database already included in the repo.

### 3) Run database migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API will be available at:

- http://localhost:8000
- admin: http://localhost:8000/admin/

### 4) Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

- http://localhost:3000

## Environment configuration

The backend reads environment variables from `backend/.env` using `django-environ`.

Common settings include:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_URL`
- `REDIS_URL`
- `FIELD_ENCRYPTION_KEY`
- `HMAC_SECRET`
- `REPORT_THRESHOLD`
- `EMAIL_BACKEND`
- `SMS_BACKEND`
- `CELERY_EAGER`
- optional S3 variables for cloud file storage

For local development, the app is configured to print verification emails and SMS codes to the terminal unless a real provider is configured.

## Running background tasks

Celery is enabled for asynchronous jobs such as report processing and queued moderation work.

Start the worker with:

```bash
cd backend
source venv/bin/activate
celery -A config worker -l info
```

In development, `CELERY_EAGER=True` can be used to run tasks inline without requiring Redis.

## API overview

The backend exposes most endpoints under `/api/`.

### Public routes
- search for known sellers and identifiers
- fetch public seller pages and report summaries
- access profile metadata and moderation information

### Authenticated routes
- user registration and login
- email and phone OTP verification
- report creation and review
- vouching and dispute workflows

### Moderation routes
- approve or reject reports
- resolve disputes and appeals
- review audit history through the Django admin interface

## Useful commands

### Backend

```bash
cd backend
source venv/bin/activate
python manage.py migrate
python manage.py makemigrations
python manage.py test
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
npm run dev
```

## Project status

This project is actively under development and includes the main workflow for user verification, public seller lookup, reports, and moderation features. Some aspects such as production SMS integrations, enhanced moderation dashboards, and further operational automation are still being expanded.

## Notes for contributors

- Keep the backend and frontend configuration separate.
- Store secrets in `backend/.env` and do not commit them to source control.
- Use the Django admin for moderation review and audit workflows during development.
- Prefer working through the existing app boundaries (`accounts`, `core`, `listings`, `submissions`, `moderation`) rather than creating new cross-cutting logic in ad hoc places.

## License

This project does not currently declare a specific license in the repository. If you plan to share or deploy it publicly, add a license file and document the intended usage rights before distribution.
