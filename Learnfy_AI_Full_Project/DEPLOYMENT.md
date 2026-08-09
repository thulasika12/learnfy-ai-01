# Learnfy AI deployment runbook

This is an operational template. Deploy to staging and complete the launch checklist before production.

## Database migrations

Alembic is the only active schema manager. Never run `database/schema.sql` or the legacy SQL migration files on a new deployment.

Fresh database:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m alembic current
```

Existing development database: make a verified backup, set `DATABASE_URL`, then run the read-only check:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe .\scripts\check_schema.py
```

Do not stamp when the checker reports missing tables or columns. Create and review a data-preserving Alembic upgrade instead. If it reports a complete match, an operator may, after reviewing the backup, run `python -m alembic stamp 20260806_0001` followed by `python -m alembic upgrade head`. Stamping the baseline instead of the head ensures later data-preserving constraints are still applied. Stamping is never automatic.

Development fixtures are explicit only:

```powershell
Get-Content .\database\seed_data.sql | mysql.exe -h localhost -u root -p learnfy_ai
```

Never install those demonstration accounts in production.

## Staging sequence

1. Configure production-like MySQL, Redis, private S3-compatible storage, SMTP, Gemini, and PayHere Sandbox; leave legacy Stripe disabled unless a rollback exercise specifically needs it.
2. Back up the database and object storage; run `alembic upgrade head` as a one-off release job.
3. Start the API and verify `/health/live` and `/health/ready`.
4. Run authentication, upload, moderation, quota, localization, responsive, and signed PayHere-notification tests.
5. Review legal placeholders, logs, alerts, retention rules, and rollback steps before promoting the same artifact.

PayHere is the primary Sri Lankan payment provider and grants one-time 30-day or 365-day Premium access; it does not automatically renew. Keep `PAYHERE_ENABLED=false` until an approved PayHere Business account, domain-specific Merchant Secret, and public HTTPS callback URL are configured. Legacy Stripe code remains isolated for rollback. Learnfy AI does not store card details.

## PayHere Sandbox setup

1. Create a PayHere Sandbox merchant account and obtain the Sandbox Merchant ID and the Merchant Secret approved for your tunnel/domain.
2. Set `PAYMENT_PROVIDER=payhere`, `PAYHERE_ENABLED=true`, `PAYHERE_SANDBOX=true`, the merchant credentials, and LKR plan amounts in `backend/.env`.
3. PayHere cannot notify localhost. Start a secure HTTPS tunnel, for example `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`, and set `BACKEND_PUBLIC_URL` to the generated HTTPS origin.
4. The application supplies these URLs; never accept them from a browser:
   - return: `FRONTEND_URL/payments/result?order_id=...`
   - cancel: `FRONTEND_URL/payments/result?order_id=...&cancelled=1`
   - notification: `BACKEND_PUBLIC_URL/payments/payhere/notify`
5. Complete a Sandbox payment and verify the transaction becomes successful only after the signed server notification. A browser return alone must remain pending.

For production, obtain PayHere Business approval and a Merchant Secret for the exact production domain, set `PAYHERE_SANDBOX=false`, use HTTPS frontend/backend origins, verify backups and webhook logs in staging, and only then enable PayHere. Never reuse Sandbox or placeholder credentials.

## Backup and restore templates

```powershell
mysqldump.exe --single-transaction --routines --triggers -h DB_HOST -u DB_USER -p DB_NAME > learnfy-backup.sql
mysql.exe -h RESTORE_HOST -u RESTORE_USER -p RESTORE_DATABASE < learnfy-backup.sql
```

Restore into a separate database first, verify record counts and application behavior, and only then plan a controlled cutover. Back up the S3 bucket separately with the storage provider's versioned tooling.

## External services

- Redis is mandatory in production; memory rate limiting is development/test only.
- S3-compatible private storage is mandatory in production. Verification documents must never be placed under `/uploads`.
- Configure ClamAV and set `ANTIVIRUS_REQUIRED=true` when the production policy requires uploads to fail closed.
- PayHere notification endpoint: `/payments/payhere/notify`; it must be publicly reachable over HTTPS.
- Gemini, PayHere, and legacy Stripe calls must be mocked in CI. Validate real Sandbox flows only in staging.
