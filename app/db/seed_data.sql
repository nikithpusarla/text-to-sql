CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    signup_date DATE,
    status TEXT CHECK (status IN ('active','churned','pending'))
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    order_date DATE,
    total_amount NUMERIC(10,2),
    net_amount NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    hire_date DATE
);

CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id),
    order_id INT REFERENCES orders(id),
    sale_date DATE,
    commission NUMERIC(10,2)
);

TRUNCATE TABLE sales, orders, customers, employees RESTART IDENTITY;

SELECT setseed(0.42);

INSERT INTO customers (name, signup_date, status)
SELECT
    'Customer ' || gs.n,
    DATE '2020-01-01' + (gs.n % 1200),
    CASE
        WHEN gs.n % 10 = 0 THEN 'churned'
        WHEN gs.n % 7 = 0 THEN 'pending'
        ELSE 'active'
    END
FROM generate_series(1, 50) AS gs(n);

INSERT INTO orders (customer_id, order_date, total_amount, net_amount)
SELECT
    ((gs.n - 1) % 50) + 1,
    DATE '2021-01-01' + ((gs.n * 17) % 1500),
    ROUND((random() * 2500 + 15)::numeric, 2),
    ROUND((random() * 2300 + 10)::numeric, 2)
FROM generate_series(1, 300) AS gs(n);

INSERT INTO employees (name, department, hire_date)
SELECT
    'Employee ' || gs.n,
    CASE gs.n % 5
        WHEN 0 THEN 'Sales'
        WHEN 1 THEN 'Marketing'
        WHEN 2 THEN 'Engineering'
        WHEN 3 THEN 'Support'
        ELSE 'Operations'
    END,
    DATE '2018-01-01' + ((gs.n * 47) % 1800)
FROM generate_series(1, 10) AS gs(n);

INSERT INTO sales (employee_id, order_id, sale_date, commission)
SELECT
    ((gs.n - 1) % 10) + 1,
    ((gs.n - 1) % 300) + 1,
    DATE '2021-01-01' + ((gs.n * 19) % 1500),
    ROUND((random() * 550 + 20)::numeric, 2)
FROM generate_series(1, 300) AS gs(n);

CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE companies TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
