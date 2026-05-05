import polars as pl
import time
from pathlib import Path

class TitanicWrangler:

    @staticmethod
    def load_titanic_data(data_path: Path = Path("data/input/titanic_passengers.csv"), delay_seconds: int = 1) -> pl.DataFrame:
        """
        Load Titanic passenger data from CSV with a simulated delay for demo purposes.
        
        Parameters:
        -----------
        data_path : str
            Path to the Titanic CSV file (default: "data/input/titanic_passengers.csv")
        delay_seconds : int
            Number of seconds to delay (default: 5 for demo purposes)

        Returns:
        --------
        pl.DataFrame
            Raw Titanic passenger data as Polars DataFrame
        """
        # Simulate long-running operation with delay
        time.sleep(delay_seconds)
                
        # Load CSV using Polars
        try:
            df = pl.read_csv(data_path)
            return df
        except Exception as e:
            raise RuntimeError(f"Error loading Titanic data from {data_path}: {str(e)}")

    @classmethod
    def prepare_data(cls, titanic_passengers):

        return titanic_passengers \
            .pipe(cls._coerce_numeric_columns) \
            .pipe(cls._fillna_cabin) \
            .pipe(cls._fillna_fare) \
            .pipe(cls._fillna_embarked) \
            .pipe(cls._extract_title_from_name) \
            .pipe(cls._consolidate_titles) \
            .pipe(cls._add_cabin_occupancy) \
            .pipe(cls._add_ticket_sharing_count) \
            .pipe(cls._extract_cabin_level) \
            .pipe(cls._add_log10_of_fare) \
            .pipe(cls._impute_missing_age_based_on_title) \
            .pipe(cls._calculate_decade_from_age) \
            .pipe(cls._resolve_level_t) \
            .pipe(cls._convert_float_to_int) \
            .pipe(cls._convert_survived_to_string) \
            .pipe(cls._convert_embarked_to_location_names)

    @staticmethod
    def _coerce_numeric_columns(titanic_passengers):
        
        numeric_columns = ['PassengerId', 'Survived', 'Age', 'SibSp', 'Parch', 'Fare']

        return titanic_passengers.with_columns([
            pl.col(column).cast(pl.Float64, strict=False) for column in numeric_columns
        ])

    @staticmethod
    def _fillna_cabin(titanic_passengers):
        return titanic_passengers.with_columns(
            pl.col("Cabin").fill_null("None")
        )

    @staticmethod
    def _fillna_fare(titanic_passengers):
        return titanic_passengers.with_columns(
            pl.col("Fare").fill_null(0.0)
        )

    @staticmethod
    def _fillna_embarked(titanic_passengers):
        """
        The majority of passengers embarked in Southampton (S) so fill in missing values with that.
        """
        return titanic_passengers.with_columns(
            pl.col("Embarked").fill_null("S")
        )

    @staticmethod
    def _extract_title_from_name(titanic_passengers):
        """
        Pulling "Title" from the full name of each passenger looking at samples below, it is possible to use regex to do this.
        """
        return titanic_passengers.with_columns(
            pl.col("Name").str.extract(r"^.* (.*?)\..*$", 1).alias("Title")
        )

    @staticmethod
    def _consolidate_titles(titanic_passengers):
        """
        Consolidates the title column so that only titles with 5 or 
        more examples in the data are retained, the rest are 
        consolidated into an "Other" category.
        """

        title_counts = titanic_passengers.group_by("Title").len().rename({"len": "Count"})
        
        titles_to_consolidate = title_counts.filter(pl.col("Count") < 5).select("Title").to_series().to_list()

        return titanic_passengers.with_columns(
            pl.when(pl.col("Title").is_in(titles_to_consolidate))
            .then(pl.lit("Other"))
            .otherwise(pl.col("Title"))
            .alias("Title")
        )

    @staticmethod
    def _add_cabin_occupancy(titanic_passengers):
        """
        Counting cabin occupancy and passengers who also shared the same ticket.
        """
        cabin_occupancy = titanic_passengers.group_by("Cabin").len().rename({"len": "CabinOccupancy"})
        cabin_occupancy = cabin_occupancy.with_columns(
            pl.when(pl.col("Cabin") == "None")
            .then(pl.lit(0))
            .otherwise(pl.col("CabinOccupancy"))
            .alias("CabinOccupancy")
        )
        
        return titanic_passengers.join(cabin_occupancy, on="Cabin")

    @staticmethod
    def _add_ticket_sharing_count(titanic_passengers):
        ticket_sharing_count = titanic_passengers.group_by("Ticket").len().rename({"len": "TicketShareCount"})
        return titanic_passengers.join(ticket_sharing_count, on="Ticket")

    @staticmethod
    def _extract_cabin_level(titanic_passengers):
        """
        Pulling the "Level" from the cabin (if indeed the passenger had a cabin).  We can use simple string function to pluck this out as it is always the first character.
        """
        return titanic_passengers.with_columns(
            pl.col("Cabin").str.slice(0, 1).alias("Level")
        )

    @staticmethod
    def _add_log10_of_fare(titanic_passengers):
        """
        Can only apply log to values that are non-zero. Log 0 = -infinity!
        """
        return titanic_passengers.with_columns(
            pl.when(pl.col("Fare") > 0)
            .then(pl.col("Fare").log10())
            .otherwise(pl.lit(0.0))
            .alias("FareLog10")
        )

    @staticmethod
    def _impute_missing_age_based_on_title(titanic_passengers):
        """
        This function uses the Title feature to compute an average age for different
        titles. For example we see a marked difference between Mr versus Master and
        Mrs versus Miss.  So we exploit this to fill in missing values with a bit
        more intelligence.
        """
        average_age_by_title = titanic_passengers.group_by("Title").agg(
            pl.col("Age").mean().cast(pl.Int32).alias("AverageAge")
        )

        # Join with the average ages and fill nulls
        return titanic_passengers.join(average_age_by_title, on="Title").with_columns(
            pl.when(pl.col("Age").is_null())
            .then(pl.col("AverageAge"))
            .otherwise(pl.col("Age"))
            .alias("Age")
        ).drop("AverageAge")
    
    @staticmethod
    def _resolve_level_t(titanic_passengers):
        """
        There is only one passenger who had a cabin on level T (the boat deck). This
        is resolved to the nearest deck (A).
        """
        return titanic_passengers.with_columns(
            pl.when(pl.col("Level") == "T")
            .then(pl.lit("A"))
            .otherwise(pl.col("Level"))
            .alias("Level")
        )
    
    @staticmethod
    def _calculate_decade_from_age(titanic_passengers):
        return titanic_passengers.with_columns(
            (pl.col("Age") // 10).alias("AgeInDecades")
        )
    
    @staticmethod
    def _convert_float_to_int(titanic_passengers):
        columns_to_convert = ["AgeInDecades", "Pclass"]
        return titanic_passengers.with_columns([
            pl.col(column).cast(pl.Int32) for column in columns_to_convert
        ])
    
    @staticmethod
    def _convert_survived_to_string(titanic_passengers):
        return titanic_passengers.with_columns(
            pl.when(pl.col("Survived") == 1)
            .then(pl.lit("Survived"))
            .when(pl.col("Survived") == 0)
            .then(pl.lit("Died"))
            .otherwise(pl.col("Survived"))
            .alias("Survived")
        )
    
    @staticmethod
    def _convert_embarked_to_location_names(titanic_passengers):
        return titanic_passengers.with_columns(
            pl.col("Embarked").map_elements(
                lambda x: {
                    'S': 'Southampton',
                    'C': 'Cherbourg', 
                    'Q': 'Queenstown'
                }.get(x, x),
                return_dtype=pl.Utf8
            )
        )
    
    @staticmethod
    def calculate_survival_rate(data: pl.DataFrame, group_by_column: str = None) -> pl.DataFrame:
        """
        Calculate survival rate for passengers in the dataframe.
        
        Parameters:
        -----------
        data : pl.DataFrame
            Input data (must include 'Survived' column with "Survived"/"Died" values)
        group_by_column : str, optional
            Column to group by for category-wise survival rates
            
        Returns:
        --------
        pl.DataFrame
            DataFrame with survival statistics including count, survived count, and survival rate
        """
        if group_by_column is None:
            # Overall survival rate
            total_count = len(data)
            survived_count = len(data.filter(pl.col("Survived") == "Survived"))
            survival_rate = (survived_count / total_count * 100) if total_count > 0 else 0.0
            
            return pl.DataFrame({
                "Category": ["Overall"],
                "TotalCount": [total_count],
                "SurvivedCount": [survived_count],
                "SurvivalRate": [survival_rate]
            })
        else:
            # Category-wise survival rates
            return (
                data.group_by(group_by_column)
                .agg([
                    pl.len().alias("TotalCount"),
                    pl.col("Survived").filter(pl.col("Survived") == "Survived").len().alias("SurvivedCount")
                ])
                .with_columns(
                    (pl.col("SurvivedCount") / pl.col("TotalCount") * 100).alias("SurvivalRate")
                )
                .rename({group_by_column: "Category"})
                .sort("Category")
            )
