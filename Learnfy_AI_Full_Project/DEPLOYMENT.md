# Learnfy AI Deployment

## Recommended split deployment

- Frontend: Netlify
- Backend: Railway, Koyeb, Northflank, or another Docker/Python host
- Database: managed MySQL

## Backend

Deploy the `backend` directory and use:

```text
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables on the backend host:

```text
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/learnfy_ai
JWT_SECRET_KEY=long-random-production-secret
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
FRONTEND_URL=https://your-site.netlify.app
CORS_ORIGINS=https://your-site.netlify.app
UPLOAD_DIR=app/uploads
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=no-reply@your-domain.example
BACKEND_PUBLIC_URL=https://your-backend-domain.example
STRIPE_SECRET_KEY=configure-only-in-host-secret-manager
STRIPE_WEBHOOK_SECRET=configure-only-in-host-secret-manager
PDF_UNICODE_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf
```

Run `database/schema.sql` once for a new database. For an existing database, apply the non-destructive payment migration from the project root:

```powershell
Get-Content .\database\migrations\002_payhere_payments.sql | & "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -h YOUR_HOST -u YOUR_USER -p YOUR_DATABASE
Get-Content .\database\migrations\003_flashcards.sql | & "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -h YOUR_HOST -u YOUR_USER -p YOUR_DATABASE
```

## Stripe test mode

1. Copy a Stripe test secret key into `STRIPE_SECRET_KEY`.
2. Run `stripe listen --forward-to localhost:8000/payments/webhook` for local webhook forwarding.
3. Copy the CLI's `whsec_...` signing secret into `STRIPE_WEBHOOK_SECRET`.
4. Complete Checkout with a Stripe test card and verify Premium activates only after the webhook arrives.

## Stripe live payments

1. Set the live Stripe secret key in `STRIPE_SECRET_KEY`.
2. Create `https://your-backend-domain.example/payments/webhook` in Stripe Workbench.
3. Subscribe to `checkout.session.completed`, asynchronous payment success/failure, and expiration events.
4. Store that endpoint's signing secret in `STRIPE_WEBHOOK_SECRET`.
5. Run a low-value live transaction and verify the payment becomes successful only after the signed webhook.

The return URL is a browser convenience only. Premium activation occurs exclusively after the backend verifies the Stripe webhook signature, order, server-stored amount, and currency.

## Frontend (Netlify)

Use `frontend` as the base directory. The included `netlify.toml` runs `npm run build` and configures React Router redirects.

Set:

```text
VITE_API_URL=https://your-backend-domain.example
```

Deploy the backend first, add its URL to Netlify, then add the final Netlify URL to the backend's `FRONTEND_URL` and `CORS_ORIGINS`.

## Docker on a local computer

From the project root:

```powershell
$env:GEMINI_API_KEY="your-key"
$env:JWT_SECRET_KEY="replace-with-a-long-random-value"
docker compose up --build
```

Frontend: `http://localhost:5173`  
Backend docs: `http://localhost:8000/docs`

## Production checklist

- Never upload `backend/.env` or `frontend/.env`.
- Use a new, long `JWT_SECRET_KEY`.
- Rotate any Gemini key that was previously committed or shared publicly.
- Use persistent object storage for uploads; container-local files can disappear during redeployment.
- Configure a real email provider before relying on password-reset emails.
- Keep `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` only in backend secret storage; never use a `VITE_` variable.
- Require HTTPS for frontend, backend, return URL, cancel URL, and the Stripe webhook.
- Restrict production CORS to the final frontend domain and rotate any exposed credentials.
- Monitor failed signatures, amount mismatches, chargebacks, and duplicate callback volume.
- Back up MySQL before migrations and before every production deployment.
- Install a Tamil/Sinhala-capable TrueType font and configure `PDF_UNICODE_FONT_PATH` for multilingual flashcard PDFs.
- Keep generated flashcard images in persistent object storage when the hosting filesystem is ephemeral.
