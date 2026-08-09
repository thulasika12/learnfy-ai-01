# Legacy SQL migrations

The numbered SQL files in `database/migrations` are retained as historical input only.
They must not be run on new deployments. Alembic is the sole active migration system.
The former `002_payhere_payments.sql` is retained for history but is not part of the
active migration chain. The current PayHere integration is tracked by Alembic.
