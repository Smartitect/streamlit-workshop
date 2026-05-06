import plotly.express as px
from plotly.graph_objects import Figure
import polars as pl
import duckdb

class LandRegistryChartingHelper:

    COLOUR_SEQUENCE = ["#8CC600", "black", "#41b6e6", "#EE7423"]
    WIDTH = 800
    HEIGHT = 600


    @classmethod
    def chart_median_price_by_month_and_property_type(cls, query: duckdb.DuckDBPyRelation) -> Figure:
        
        fig = px.line(
            query.pl(),
            x="month_of_sale",
            y="median_price",
            color="property_type",
            line_dash="property_type",
            color_discrete_sequence=cls.COLOUR_SEQUENCE,
            line_dash_sequence=["solid", "dash", "dot", "dashdot"],
            title="Median Price by Month and Property Type"
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Median Price",
            legend_title="Property Type",
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )
        
        return fig
        
    @classmethod
    def chart_number_of_sales_by_month_and_property_type(cls, query: duckdb.DuckDBPyRelation) -> Figure:

        fig = px.bar(
            query.pl(),
            x="month_of_sale",
            y="number_of_sales",
            color="property_type",
            color_discrete_sequence=cls.COLOUR_SEQUENCE,
            title="Number of Sales by Month and Property Type"
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Sales",
            legend_title="Property Type",
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )
        
        return fig

    @classmethod
    def map_individual_property_sales(cls, query: duckdb.DuckDBPyRelation) -> Figure:

        df = query.pl()

        fig = px.scatter_map(
            df,
            lat="latitude",
            lon="longitude",
            color="property_type",
            size="price",
            color_discrete_sequence=cls.COLOUR_SEQUENCE,
            size_max=15,
            title="Map of Individual Property Sales",
        )

        padding = 0.01
        fig.update_layout(
            map_style="open-street-map",
            map_bounds_west=df["longitude"].min() - padding,
            map_bounds_east=df["longitude"].max() + padding,
            map_bounds_south=df["latitude"].min() - padding,
            map_bounds_north=df["latitude"].max() + padding,
            width=cls.WIDTH,
            height=cls.WIDTH,
        )

        return fig