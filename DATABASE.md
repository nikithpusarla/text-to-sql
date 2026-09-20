# Database Guide

Queryline uses PostgreSQL 16 for its local analytics workspace. The repository includes the schema, seed data, Docker Compose configuration, and an application-level initializer so a new developer can reproduce the same environment.

## Local configuration

| Setting | Local value |
|---|---|
| Engine | PostgreSQL 16 Alpine |
| Database | `companies` |
| Host port | `5433` |
| Container port | `5432` |
| Bootstrap role | `app_user` |
| Query role | `readonly_user` |
| Query access | Read-only `SELECT` |

Port `5433` avoids colliding with a native PostgreSQL installation that may already use `5432`.

## Start the database

From the repository root:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
docker compose up -d
docker compose ps
```

On Windows PowerShell, use `Copy-Item .env.example .env` for the second command.

The Compose service mounts `app/db/seed_data.sql` into PostgreSQL's initialization directory. The seed script runs only when the PostgreSQL data volume is created.

## Schema and sample data

The database contains four tables:

### `customers`

```sql
id SERIAL PRIMARY KEY
name TEXT NOT NULL
signup_date DATE
status TEXT CHECK (status IN ('active', 'churned', 'pending'))
```

### `orders`

```sql
id SERIAL PRIMARY KEY
customer_id INT REFERENCES customers(id)
order_date DATE
total_amount NUMERIC(10,2)
net_amount NUMERIC(10,2)
```

### `employees`

```sql
id SERIAL PRIMARY KEY
name TEXT NOT NULL
department TEXT
hire_date DATE
```

### `sales`

```sql
id SERIAL PRIMARY KEY
employee_id INT REFERENCES employees(id)
order_id INT REFERENCES orders(id)
sale_date DATE
commission NUMERIC(10,2)
```

The seed creates approximately 50 customers, 300 orders, 10 employees, and 300 sales records. A fixed PostgreSQL random seed makes generated amounts reproducible on a fresh volume.

`app/db/schema.sql` contains idempotent table and index creation. `app/db/initialize.py` applies that schema and grants the configured read-only role without truncating or reseeding existing data. The API runs it on startup only when `DATABASE_INIT_ON_STARTUP=true` and `APP_ENV` is not `test`.

## Roles and permissions

The bootstrap role is used only for initialization. Query execution uses `POSTGRES_READONLY_USER` and `POSTGRES_READONLY_PASSWORD` from `.env`.

The initializer grants:

- `CONNECT` on the database.
- `USAGE` on the `public` schema.
- `SELECT` on current tables.
- Default `SELECT` privileges for future tables.

Database permissions complement, but do not replace, application SQL validation.

## Verify the live schema

```bash
python -m app.db.introspect
```

Expected tables and columns:

```json
{
  "customers": ["id", "name", "signup_date", "status"],
  "employees": ["id", "name", "department", "hire_date"],
  "orders": ["id", "customer_id", "order_date", "total_amount", "net_amount"],
  "sales": ["id", "employee_id", "order_id", "sale_date", "commission"]
}
```

The executor sets `statement_timeout` to five seconds before each query.

## Recreate the sample database

To discard the local volume and reseed from scratch:

```bash
docker compose down -v
docker compose up -d
python -m app.db.introspect
```

The `-v` flag permanently removes local database changes. Do not use it when preserving development data matters.

## Production guidance

Do not use the sample credentials in a hosted deployment. Provision PostgreSQL separately, store secrets in the platform's secret manager, run schema migrations as a release step, and set `DATABASE_INIT_ON_STARTUP=false` for web workers. Use a managed PostgreSQL or Redis session repository when running more than one application instance.
