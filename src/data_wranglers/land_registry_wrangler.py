import duckdb
from pathlib import Path

LAND_REGISTRY_DATABASE_PATH = Path("../../databases/land_registry.db")

class LandRegistryDataWrangler:

    def __init__(self, database_path: Path = LAND_REGISTRY_DATABASE_PATH):
        assert database_path.exists(), f"Database file does not exist: {database_path}"

    def _create_database_connection(self):
        with duckdb.connect(database=str(LAND_REGISTRY_DATABASE_PATH), read_only=True) as connection:
            return connection

    