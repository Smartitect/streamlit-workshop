import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots
import polars as pl


class WorldBankChartingHelper:

    WIDTH = 800
    HEIGHT = 600

    @classmethod
    def chart_wealth_and_health(cls, df: pl.DataFrame) -> Figure:
        fig = px.scatter(
            df.drop_nulls(subset=["population_in_millions"]),
            x="gdp_usd_per_capita",
            y="life_expectancy",
            animation_frame="year",
            animation_group="country_name",
            size="population_in_millions",
            color="region",
            text="country_code",
            hover_name="country_name",
            log_x=True,
            size_max=120,
            range_x=[100, 100000],
            range_y=[25, 90],
            title="World Wealth and Health Over Time",
            labels={
                "gdp_usd_per_capita": "Wealth (GDP Per Capita in USD)",
                "life_expectancy": "Health (Life Expectancy in Years)"
            }
        )

        fig.update_layout(
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )

        return fig

    @classmethod
    def chart_country_locations(cls, df: pl.DataFrame) -> Figure:
        fig = px.scatter_geo(
            df,
            lat="latitude",
            lon="longitude",
            hover_name="country_name",
            color="region",
            projection="natural earth",
            title="World Bank Data - Country Locations"
        )

        fig.update_layout(
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )

        return fig

    @classmethod
    def chart_population_analysis(cls, df: pl.DataFrame, country_name: str) -> Figure:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Total Population (Millions)", "Year-on-Year Growth (%)")
        )

        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["population_in_millions"],
                mode="lines+markers",
                name="Population",
                line=dict(width=3)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(
                x=df["year"],
                y=df["population_change_percentage"],
                marker_color=df["color"],
                name="Change %"
            ),
            row=2, col=1
        )

        fig.update_layout(
            title_text=f"{country_name} Population Analysis",
            showlegend=False,
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )

        return fig

    @classmethod
    def chart_metric_by_country(cls, df: pl.DataFrame, metric: str) -> Figure:
        fig = px.line(
            df,
            x="year",
            y=metric,
            color="country_name",
            markers=True,
            title=f"{metric} by Country",
            labels={
                "year": "Year",
                metric: metric,
                "country_name": "Country"
            }
        )

        fig.update_layout(
            width=cls.WIDTH,
            height=cls.HEIGHT,
        )

        return fig
