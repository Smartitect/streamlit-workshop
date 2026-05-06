import atexit

import duckdb
import polars as pl
from pathlib import Path

WORLD_BANK_DATABASE_PATH = Path("../../databases/world_bank.db")


class WorldBankDataWrangler:

    def __init__(self, database_path: Path = WORLD_BANK_DATABASE_PATH):
        assert database_path.exists(), f"Database file does not exist: {database_path}"
        self.db = duckdb.connect(database=str(database_path), read_only=True)
        atexit.register(self.db.close)

    def get_wealth_and_health_data(self) -> pl.DataFrame:
        query = self.db.sql(
            """
            SELECT d.country_code, c.country_name, c.region, d.year, d.indicator_code, d.value, c.longitude, c.latitude
            FROM silver.data d
            JOIN silver.countries c ON d.country_code = c.country_code
            WHERE d.indicator_code IN ('WB_WDI_SP_POP_TOTL', 'WB_WDI_SP_DYN_LE00_IN', 'WB_WDI_NY_GDP_PCAP_CD')
            """
        ).pl()

        return (
            query
            .pivot(
                on=["indicator_code"],
                index=["country_code", "country_name", "region", "year", "longitude", "latitude"],
                values="value"
            )
            .rename(
                {
                    "WB_WDI_NY_GDP_PCAP_CD": "gdp_usd_per_capita",
                    "WB_WDI_SP_DYN_LE00_IN": "life_expectancy",
                    "WB_WDI_SP_POP_TOTL": "population"
                }
            )
            .sort(["country_code", "year"])
            .with_columns(
                pl.col("gdp_usd_per_capita").forward_fill().over("country_code"),
                pl.col("life_expectancy").forward_fill().over("country_code"),
                pl.col("population").forward_fill().over("country_code"),
            )
            .drop_nulls(subset=["gdp_usd_per_capita", "life_expectancy", "population"])
            .with_columns(
                (pl.col("population") / 1_000_000).round(2).alias("population_in_millions"),
            )
        )

    def get_population_analysis(self, country_name: str) -> pl.DataFrame:
        data = self.get_wealth_and_health_data()

        return (
            data
            .filter(pl.col("country_name") == country_name)
            .sort("year")
            .with_columns(
                (
                    (pl.col("population_in_millions") - pl.col("population_in_millions").shift(1))
                    / pl.col("population_in_millions").shift(1)
                    * 100
                ).alias("population_change_percentage")
            )
            .with_columns(
                pl.when(pl.col("population_change_percentage") > 0)
                .then(pl.lit("green"))
                .otherwise(pl.lit("red"))
                .alias("color")
            )
            .select(["year", "population_in_millions", "population_change_percentage", "color"])
        )

    def get_min_max_years(self) -> tuple[int, int]:
        min_year, max_year = self.db.sql(
            "SELECT MIN(year), MAX(year) FROM silver.data"
        ).fetchone()
        return min_year, max_year

    def get_indicators(self) -> pl.DataFrame:
        return self.db.sql(
            """
            SELECT *
            FROM silver.indicators
            ORDER BY indicator_code
            """
        ).pl()
