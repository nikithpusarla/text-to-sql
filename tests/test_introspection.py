from pathlib import Path


def test_seed_file_contains_expected_tables_and_readonly_role():
    seed = Path(__file__).parents[1] / "app" / "db" / "seed_data.sql"
    text = seed.read_text(encoding="utf-8")
    for table in ("customers", "orders", "employees", "sales"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in text
    assert "CREATE ROLE readonly_user" in text
    assert "GRANT SELECT ON ALL TABLES" in text
