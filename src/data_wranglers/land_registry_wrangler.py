import atexit

import duckdb
from datetime import date
from pathlib import Path

LAND_REGISTRY_DATABASE_PATH = Path("../../databases/land_registry.db")

class LandRegistryDataWrangler:

    def __init__(self, database_path: Path = LAND_REGISTRY_DATABASE_PATH):
        assert database_path.exists(), f"Database file does not exist: {database_path}"
        self.db = duckdb.connect(database=str(database_path), read_only=True)
        atexit.register(self.db.close)

    def _date_to_string(self, date: date) -> str:
        return date.strftime("%Y-%m-%d")

    def generate_insights_for_postcode(
        self,
        postcode: str,
        property_type: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> duckdb.DuckDBPyRelation:

        query = self.db.sql("SELECT * FROM gold.price_paid_geocoded")

        query = self.db.sql(f"SELECT * FROM query WHERE postcode LIKE '{postcode}%'")

        if property_type:
            query = self.db.sql(f"SELECT * FROM query WHERE property_type = '{property_type}'")

        if min_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date >= '{self._date_to_string(min_date)}'")

        if max_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date <= '{self._date_to_string(max_date)}'")

        query = self.db.sql("""
            SELECT
                property_type,
                month_of_sale,
                MAX(price) AS max_price,
                MIN(price) AS min_price,
                MEDIAN(price) AS median_price,
                COUNT(*) AS number_of_sales
            FROM query
            GROUP BY ALL
            ORDER BY month_of_sale, property_type
        """)

        return query

    def generate_summary_statistics_for_postcode(
        self,
        postcode: str,
        property_type: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> duckdb.DuckDBPyRelation:

        query = self.db.sql("SELECT * FROM gold.price_paid_geocoded")

        query = self.db.sql(f"SELECT * FROM query WHERE postcode LIKE '{postcode}%'")

        if property_type:
            query = self.db.sql(f"SELECT * FROM query WHERE property_type = '{property_type}'")

        if min_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date >= '{self._date_to_string(min_date)}'")

        if max_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date <= '{self._date_to_string(max_date)}'")


        query = self.db.sql("""
            SELECT
                property_type,
                MAX(price) AS max_price,
                MIN(price) AS min_price,
                MEDIAN(price) AS median_price,
                COUNT(*) AS number_of_sales
            FROM query
            GROUP BY ALL
            ORDER BY property_type
        """)

        return query
    
    def get_all_matching_properties(
        self,
        postcode: str,
        property_type: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> duckdb.DuckDBPyRelation:

        query = self.db.sql("SELECT * FROM gold.price_paid_geocoded")

        query = self.db.sql(f"SELECT * FROM query WHERE postcode LIKE '{postcode}%'")

        if property_type:
            query = self.db.sql(f"SELECT * FROM query WHERE property_type = '{property_type}'")

        if min_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date >= '{self._date_to_string(min_date)}'")

        if max_date:
            query = self.db.sql(f"SELECT * FROM query WHERE date <= '{self._date_to_string(max_date)}'")


        query = self.db.sql("""
            SELECT
                id,
                postcode,
                longitude,
                latitude,
                property_type,
                date,
                price
            FROM query
        """)

        return query
    
    def get_min_max_dates(self) -> tuple[date, date]:
        
        results = self.db.sql("SELECT * FROM gold.date_range")
        
        min_date, max_date = results.fetchone()
        
        return min_date.date(), max_date.date()
    
    def get_property_types(self) -> list[str]:
        
        results = self.db.sql("SELECT * FROM gold.property_types")
        
        property_types = [row[0] for row in results.fetchall()]
        
        return property_types
    