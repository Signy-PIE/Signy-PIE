from sqlalchemy import inspect


# Supprime les anciennes références vidéo en conservant les mots et leurs associations.
def remove_reference_videos(engine):
    inspector = inspect(engine)
    has_video_id = inspector.has_table("words") and any(
        column["name"] == "video_id" for column in inspector.get_columns("words")
    )
    if has_video_id and engine.dialect.name == "sqlite":
        with engine.connect() as connection:
            foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
            try:
                with connection.begin():
                    connection.exec_driver_sql("BEGIN IMMEDIATE")
                    connection.exec_driver_sql(
                        "CREATE TABLE words_without_video (id INTEGER PRIMARY KEY, string VARCHAR NOT NULL)"
                    )
                    connection.exec_driver_sql(
                        "INSERT INTO words_without_video (id, string) SELECT id, string FROM words"
                    )
                    connection.exec_driver_sql("DROP TABLE words")
                    connection.exec_driver_sql("ALTER TABLE words_without_video RENAME TO words")
                    connection.exec_driver_sql("CREATE INDEX ix_words_id ON words (id)")
            finally:
                connection.exec_driver_sql(f"PRAGMA foreign_keys={int(foreign_keys)}")
                connection.commit()
    elif has_video_id:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE words DROP COLUMN video_id")
    if inspector.has_table("videos"):
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE videos")
