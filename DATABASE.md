# Queryline Test Database

This project uses a local PostgreSQL 16 database for development and testing. The database is packaged as reproducible project code, not as a private or binary database dump.

## Database Configuration

| Setting | Value |
|---|---|
| Engine | PostgreSQL 16 Alpine |
| Database | `companies` |
| Docker container | `text2sql-postgres` |
| Host | `localhost` |
| Host port | `5433` |
| Container port | `5432` |
| Application role | `readonly_user` |
| Access | Read-only `SELECT` access |

Port `5433` is used because port `5432` can be occupied by a native PostgreSQL installation on Windows.

## Tables

### `customers`

Stores customer identity and lifecycle information.

```sql
id SERIAL PRIMARY KEY
name TEXT NOT NULL
signup_date DATE
status TEXT CHECK (status IN ('active', 'churned', 'pending'))
```

### `orders`

Stores customer purchases and monetary values.

```sql
id SERIAL PRIMARY KEY
customer_id INT REFERENCES customers(id)
order_date DATE
total_amount NUMERIC(10,2)
net_amount NUMERIC(10,2)
```

### `employees`

Stores employees and departments.

```sql
id SERIAL PRIMARY KEY
name TEXT NOT NULL
department TEXT
hire_date DATE
```

### `sales`

Connects employees to orders and stores commissions.

```sql
id SERIAL PRIMARY KEY
employee_id INT REFERENCES employees(id)
order_id INT REFERENCES orders(id)
sale_date DATE
commission NUMERIC(10,2)
```

## Seeded Test Data

The seed script creates:

- 50 customers
- 300 orders
- 10 employees
- 300 sales records

The seed uses a fixed PostgreSQL random seed (`0.42`) so generated monetary values are reproducible when the database volume is initialized. The data includes different customer and employee performance patterns for testing ambiguous questions such as:

- `Who is our best customer?`
- `Which employee is performing best?`
- `Show customers with the most orders.`

## How the Database Is Created

Docker Compose mounts `app/db/seed_data.sql` into PostgreSQL's initialization directory:

```text
./app/db/seed_data.sql:/docker-entrypoint-initdb.d/01_seed.sql:ro
```

On a fresh volume, PostgreSQL automatically:

1. Creates the four tables.
2. Inserts the sample rows.
3. Creates the `readonly_user` role.
4. Grants that role connection, schema usage, and table `SELECT` privileges.

Start the database from the repository root:

```powershell
docker compose up -d
docker compose ps
```

Expected container:

```text
text2sql-postgres   postgres:16-alpine   healthy   0.0.0.0:5433->5432/tcp
```

## Verify the Database

Run the application introspector:

```powershell
python -m app.db.introspect
```

Expected tables:

```json
{
  "customers": ["id", "name", "signup_date", "status"],
  "employees": ["id", "name", "department", "hire_date"],
  "orders": ["id", "customer_id", "order_date", "total_amount", "net_amount"],
  "sales": ["id", "employee_id", "order_id", "sale_date", "commission"]
}
```

The application connects using the read-only credentials from `.env` and sets a five-second `statement_timeout` before executing queries.

## Recreate the Database

Initialization scripts run only when PostgreSQL creates a new data directory. To fully recreate the test database and reseed it:

```powershell
docker compose down -v
docker compose up -d
python -m app.db.introspect
```

The `-v` flag deletes the local Docker database volume. Do not use it if you need to preserve local database changes.

## Why the Database Is in the Repository

The repository includes the schema and seed SQL so every developer and CI environment can create the same test database. The live database credentials and Docker volume are not committed. The `.env` file is ignored by Git, while `.env.example` provides safe development defaults.
