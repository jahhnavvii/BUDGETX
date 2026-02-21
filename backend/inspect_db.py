from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./budgetx.db")

with engine.connect() as conn:
    print("Tables in database:")
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    for table in tables:
        print(table[0])

    print("\nUsers table data:")
    result = conn.execute(text("SELECT * FROM users"))
    for row in result:
        print(row)