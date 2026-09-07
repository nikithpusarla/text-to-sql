from __future__ import annotations

SCHEMA = {
    "customers": ["id", "name", "signup_date", "status"],
    "orders": ["id", "customer_id", "order_date", "total_amount", "net_amount"],
    "employees": ["id", "name", "department", "hire_date"],
    "sales": ["id", "employee_id", "order_id", "sale_date", "commission"],
}