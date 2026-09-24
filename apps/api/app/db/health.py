from sqlalchemy import text

from app.db.session import engine


def check_database_connection() -> dict:
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database();")
        ).scalar_one()

        postgis_version = connection.execute(
            text("SELECT PostGIS_Version();")
        ).scalar_one()

    return {
        "database": database_name,
        "postgis": postgis_version,
    }