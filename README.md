# AI Resume Screening & Job Matching

FastAPI + SQLAlchemy + PostgreSQL backend, React + TypeScript + Vite
frontend. Deterministic AI pipeline (canonicalization → eligibility →
ranking → threshold decision → gap analysis → explanation → evidence)
behind a recruiter/candidate portal.

## Running locally

### Backend

```
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # fill in DATABASE_URL, JWT_SECRET_KEY, etc.
alembic upgrade head
uvicorn main:app --reload
```

The API serves on `http://localhost:8000` (docs at `/docs`).

### Frontend

```
cd frontend
npm install
cp .env.example .env           # fill in VITE_API_BASE_URL, VITE_GOOGLE_CLIENT_ID
npm run dev
```

The app serves on `http://localhost:5173`.

## Authentication

Password auth (email + password, JWT access tokens) and Google
Sign-In are both supported side by side - a user can be created
through either path, and the existing password flow keeps working
unchanged whether or not Google auth is configured.

### Google Sign-In setup

Google auth is **off by default** (password login/registration keeps
working with no configuration). To turn it on:

1. In [Google Cloud Console](https://console.cloud.google.com/) →
   **APIs & Services → Credentials**, create an **OAuth 2.0 Client
   ID** of type **Web application**.
2. Under **Authorized JavaScript origins**, add your frontend origin
   for local development:
   - `http://localhost:5173`
3. No **Authorized redirect URI** is needed - this app uses Google
   Identity Services' token/popup flow (`ux_mode: "popup"`), not the
   redirect-based OAuth flow.
4. Copy the generated **Client ID** (it ends in
   `.apps.googleusercontent.com`). This is a public identifier, not a
   secret - no client secret is used or required anywhere in this
   flow.
5. Set the **same Client ID** in both places:
   - Backend `.env`: `GOOGLE_CLIENT_ID=...`
   - Frontend `frontend/.env`: `VITE_GOOGLE_CLIENT_ID=...`
6. Restart both the backend and the Vite dev server.

Never commit `.env` or `frontend/.env` - both are git-ignored. Only
`.env.example` / `frontend/.env.example` (placeholders only) are
tracked.

### How Google Sign-In works here

```
Frontend (Google Identity Services button)
    -> Google ID token ("credential")
    -> POST /api/auth/google { credential, role? }
    -> backend verifies the token with Google's own client library
       (signature, audience, issuer, expiry - see
       app/auth/google_oauth.py)
    -> find-or-create local User, keyed on Google's `sub` claim
       (never on email)
    -> backend issues the application's own JWT (same shape/endpoint
       response as password login)
    -> frontend stores it in localStorage exactly like password login
```

- `role` (`recruiter` or `candidate`) is only used the first time a
  Google account signs in, to create the local user. It is validated
  against the same closed role enum as password registration -
  `admin` can never be requested. An existing Google-linked account's
  stored role is never changed by a later login.
- If a Google account's email already belongs to an existing
  password account, sign-in is rejected with a 409 rather than
  silently linking the accounts - the existing password login must be
  used instead.

## Tests

```
# Backend (from the repo root, with venv active)
pytest tests/ -v

# Frontend
cd frontend
npm test -- --run
npx tsc --noEmit
npm run build
npx playwright test          # backend must be running on :8000
```

`alembic check` should report no pending migrations after `alembic
upgrade head`.
