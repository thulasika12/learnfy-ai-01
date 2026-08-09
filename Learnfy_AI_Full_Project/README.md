# Learnfy AI

**Learn • Connect • Grow**

Learnfy AI is a full-stack learning platform where students and teachers share notes and resources, collaborate in study groups, and use Google Gemini for doubt solving, document summaries, quizzes, flashcards, and study plans.

## Technology

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic, JWT |
| Database | MySQL |
| AI | Google Gemini API |
| Deployment | Docker, Netlify frontend, Docker/Python backend |

## Included features

- Student, teacher, and admin accounts
- Strong password validation, access/refresh tokens, logout, reset/change password, account deletion
- Teacher verification and admin user/statistics dashboard
- Notes: upload, search, filter, view, edit, delete, like, bookmark, comment
- Teacher resources: upload, list, download, delete
- Study groups: creator-admin ownership, join requests, approve/reject, leave, and member discussions
- AI doubt solver with chat history
- AI TXT/PDF/DOCX summarizer
- AI quiz generator with answer selection, server-side marking, score/percentage, and answer review
- AI flashcard and study-plan generators
- Persistent light/dark theme
- English, Tamil, and Sinhala interface and quiz generation
- Responsive role-based dashboards and protected routes
- Stripe Premium payments with server-side pricing, verified webhooks, and payment history
- AI flashcard workspaces generated from topics, pasted notes, saved notes, PDF/DOCX/TXT sources
- Private saved sets, favourites, study scoring/history, revision reminders, images, exports, and expiring shares
- MySQL schema, repeat-safe sample data, Docker, and deployment instructions

## Project structure

```text
learnfy-ai-study/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── config/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── uploads/
│   │   └── main.py
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   ├── migrations/
│   ├── schema.sql
│   └── seed_data.sql
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── DEPLOYMENT.md
```

## Run on Windows PowerShell

Use Python 3.12 for this project.

### 1. Create the MySQL database

From the project root:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe -m alembic upgrade head
```

Apply every versioned migration after the base schema, then optionally install development seed data:

```powershell
$mysql = "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe"
Get-ChildItem .\database\migrations\*.sql | Sort-Object Name | ForEach-Object { Get-Content $_.FullName | & $mysql -u root -p learnfy_ai }
Get-Content .\database\seed_data.sql | & $mysql -u root -p learnfy_ai
```

`seed_data.sql` is for local development only. Do not install its demonstration accounts in production.

### PayHere Premium access

PayHere Checkout is the primary provider for one-time LKR 500 / 30-day and LKR 5,000 / 365-day Premium access. It does not automatically renew. Copy `backend/.env.example`, keep `PAYHERE_ENABLED=false` until credentials are ready, and follow `DEPLOYMENT.md` for Sandbox, HTTPS tunnel, signed notification, and production approval steps. The merchant secret is backend-only and must never use a `VITE_` variable.

For an existing database, back it up and apply the migrations in filename order:

```powershell
$mysql = "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe"
Get-ChildItem .\database\migrations\*.sql | Sort-Object Name | ForEach-Object { Get-Content $_.FullName | & $mysql -u root -p learnfy_ai }
```

Schema changes are never applied automatically during backend startup. Migration status can be checked by comparing the ordered filenames in `database\migrations` with the columns/tables in MySQL:

```powershell
Get-ChildItem .\database\migrations\*.sql | Sort-Object Name | Select-Object Name
& $mysql -u root -p -D learnfy_ai -e "SHOW TABLES; DESCRIBE users; DESCRIBE teacher_verifications;"
```

### 2. Start the backend

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` and set the MySQL password, a long `JWT_SECRET_KEY`, and your `GEMINI_API_KEY`.

```powershell
python -m uvicorn app.main:app --reload
```

Using `python -m uvicorn` also avoids the Windows policy issue that can block `uvicorn.exe`.

- Backend: `http://localhost:8000`
- Swagger API docs: `http://localhost:8000/docs`

### 3. Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

### Verification

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v

cd ..\frontend
npm run lint
npm run build
npm run test:e2e
```

The Playwright suite uses Playwright's bundled Chromium and verifies the application at desktop, tablet, and mobile viewports in light and dark themes.

## Environment variables

`backend/.env`:

```text
APP_NAME=Learnfy AI
ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/learnfy_ai
JWT_SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_EXPIRE_MINUTES=30
GEMINI_API_KEY=PASTE_YOUR_GOOGLE_AI_STUDIO_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_TLS=true
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
UPLOAD_DIR=app/uploads
MAX_UPLOAD_SIZE_MB=20
BACKEND_PUBLIC_URL=http://localhost:8000
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
PDF_UNICODE_FONT_PATH=
```

`frontend/.env`:

```text
VITE_API_URL=http://localhost:8000
```

## Sample accounts

Only available after running `database/seed_data.sql`:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@learnfy.ai` | `Admin@123` |
| Teacher | `teacher@learnfy.ai` | `Teacher@123` |
| Student | `student@learnfy.ai` | `Student@123` |

Change or delete these accounts before a public deployment.

## Important API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Account and login |
| POST | `/auth/refresh`, `/auth/logout` | Token rotation and logout |
| POST | `/auth/forgot-password`, `/auth/reset-password` | Password recovery |
| POST | `/auth/change-password` | Change signed-in user's password |
| GET/PUT | `/users/profile` | Profile |
| POST/GET | `/notes/` | Upload/list notes |
| GET/PUT/DELETE | `/notes/{id}` | View/edit/delete note |
| POST | `/notes/{id}/like`, `/notes/{id}/bookmark` | Note reactions |
| POST/GET | `/resources/` | Teacher resources |
| POST | `/groups/create`, `/groups/{id}/join`, `/groups/{id}/leave` | Create group, request membership, or leave |
| DELETE | `/groups/{id}` | Group admin deletes a group |
| GET | `/groups/{id}/join-requests` | Group admin's pending requests |
| POST | `/groups/{id}/join-requests/{request_id}/approve` | Group admin approves membership |
| POST | `/groups/{id}/join-requests/{request_id}/reject` | Group admin rejects membership |
| POST | `/ai/chat` | Doubt solver |
| POST | `/ai/summarize`, `/ai/summarize-file` | Text/document summary |
| POST | `/ai/generate-quiz`, `/ai/flashcards`, `/ai/study-plan` | AI learning tools |
| POST | `/ai/quiz/submit` | Mark selected quiz answers and return score/review |
| GET | `/admin/statistics`, `/admin/users` | Admin dashboard |
| GET | `/payments/plans`, `/payments/me` | Plans and current subscription |
| POST | `/payments/checkout`, `/payments/webhook` | Stripe Checkout and verified webhook |
| GET | `/payments/status/{order_id}` | Server-confirmed payment status |
| GET | `/payments/admin/transactions` | Admin payment audit list |
| POST | `/flashcards/generate`, `/flashcards/generate-from-pdf`, `/flashcards/generate-from-note` | AI flashcard generation |
| POST/GET | `/flashcards/sets` | Save and list private flashcard sets |
| GET/PUT/DELETE | `/flashcards/sets/{id}` | Private set management |
| POST | `/flashcards/sets/{id}/study-sessions` | Save a scored study session |
| POST/DELETE | `/flashcards/sets/{id}/share` | Enable or disable read-only sharing |
| GET | `/flashcards/shared/{token}` | Public read-only shared set |
| GET | `/flashcards/sets/{id}/export/pdf`, `/export/csv` | Owner-only exports |

## Flashcard PDF fonts

PDF exports embed a TrueType font so Tamil and Sinhala remain Unicode. Windows automatically uses `C:\Windows\Fonts\Nirmala.ttc` when available. On Linux hosting, install Noto Sans Tamil/Sinhala and set `PDF_UNICODE_FONT_PATH` to the appropriate Unicode-capable TTF file. PDF export returns a clear configuration error instead of generating a file with missing characters.

## Stripe payments

Prices are controlled only by the backend: Monthly Premium is LKR 500 for 30 days and Yearly Premium is LKR 5,000 for 365 days. The frontend never sends an amount. Card details are entered on Stripe Checkout and are not handled or stored by Learnfy AI.

For testing, use Stripe test-mode keys: set `STRIPE_SECRET_KEY` in `backend/.env`, run `stripe listen --forward-to localhost:8000/payments/webhook`, and set the printed `whsec_...` value as `STRIPE_WEBHOOK_SECRET`.

For live payments, configure a Stripe webhook endpoint at `https://your-backend-domain.example/payments/webhook` and subscribe to Checkout Session completed, asynchronous success/failure, and expiration events. Store the live secret key and endpoint signing secret only in backend secret storage; never expose them through a `VITE_` variable.

## Docker

With Docker Desktop running:

```powershell
$env:GEMINI_API_KEY="your-key"
$env:JWT_SECRET_KEY="replace-with-a-long-random-value"
docker compose up --build
```

See `DEPLOYMENT.md` for Netlify and hosted-backend instructions.

## Production notes

- Real `.env` files, `venv`, `node_modules`, caches, and uploaded user files are intentionally excluded from the clean project ZIP.
- Password-reset emails are logged locally when SMTP is empty; configure the SMTP variables for real delivery.
- Container-local uploads are temporary on many hosting services; use object storage for production.
- Use Alembic migrations when the database schema begins changing after deployment.
