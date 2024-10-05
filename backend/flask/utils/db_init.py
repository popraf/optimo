import sys
from sqlalchemy import inspect


def initialize_database(db, required_tables):
    """
    Check if required tables exist in the database.
    If a table does not exist, create it.
    """
    engine = db.engine
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    missing_tables = [table for table in required_tables if table not in existing_tables]

    if missing_tables:
        print("Missing tables detected: {}".format(", ".join(missing_tables)))
        try:
            db.create_all()  # This will create all tables defined by SQLAlchemy models
            print("Missing tables have been created.")
        except Exception as e:
            print("Error creating tables: {}".format(e))
            sys.exit(1)
    else:
        print("All required tables are present.")
