import sqlalchemy as sa
from config.settings import settings


def main():
    engine = sa.create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        query = sa.text(
            """
            select column_name, data_type
            from information_schema.columns
            where table_name = 'model_registry'
            order by ordinal_position
            """
        )
        rows = conn.execute(query).fetchall()
        print(rows)


if __name__ == "__main__":
    main()
