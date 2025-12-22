from datetime import datetime
from sqlalchemy import create_engine, text

def setup_database():
    """Setup database connection to Supabase"""
    DATABASE_URL = (
        "postgresql+psycopg2://"
        "postgres.jyklspgdmztzcuwvqyom:"
        "sCezA1B7m2jrekxA"
        "@aws-1-eu-central-2.pooler.supabase.com:6543/postgres"
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"},
    )

    with engine.connect():
        print("✅ Connected to Supabase Postgres\n")

    return engine

def store_email(engine, email):
    """Store email in database"""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO emails (sender_email, sender_name, subject, body, received_at)
                VALUES (:sender_email, :sender_name, :subject, :body, :received_at)
                RETURNING id
                """
            ),
            {**email, "received_at": datetime.utcnow()},
        )
        email_id = result.fetchone()[0]

    print(f"💾 Stored email ID {email_id}")
    return email_id