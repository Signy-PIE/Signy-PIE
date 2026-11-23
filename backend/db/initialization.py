from db.connection import engine
from db.migrations import remove_reference_videos
from db.models import Base


# Applique la migration et crée les tables manquantes sans ajouter de données.
def initialize_database() -> None:
    remove_reference_videos(engine)
    Base.metadata.create_all(bind=engine)
