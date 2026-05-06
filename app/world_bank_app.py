import streamlit as st
import polars as pl

from pathlib import Path

from data_wranglers import WorldBankDataWrangler
from charting_helpers import WorldBankChartingHelper

st.set_page_config(page_title="World Health and Wealth")
st.title("World Health and Wealth Analysis")

WORLD_BANK_DATABASE_PATH = Path("../databases/world_bank.db")
world_bank_data_wrangler = WorldBankDataWrangler(WORLD_BANK_DATABASE_PATH)

@st.cache_data
def get_wealth_and_health_data() -> pl.DataFrame:
    return world_bank_data_wrangler.get_wealth_and_health_data()

world_wealth_and_health = get_wealth_and_health_data()

@st.cache_data
def get_min_max_years():
    return world_bank_data_wrangler.get_min_max_years()

min_year, max_year = get_min_max_years()

@st.cache_data
def get_countries():
    return world_wealth_and_health["country_name"].unique().to_list()

countries = get_countries()

# Select countries to explore
countries = st.multiselect("Select countries to explore:", options=countries, default=countries[0:])

selected_min_year, selected_max_year = st.slider("Select a range of years", min_year, max_year, (min_year, max_year))

filtered_world_wealth_and_health = (
    world_wealth_and_health
    .filter(
        pl.col("country_name").is_in(countries)
        & pl.col("year").is_between(selected_min_year, selected_max_year)
    )
    .sort(["country_name", "year"])
)

number_of_countries = len(countries)

st.metric(label="Number of Countries", value=number_of_countries)

if filtered_world_wealth_and_health.is_empty():
    st.warning("No data available for the selected filters.")
else:
    st.plotly_chart(WorldBankChartingHelper.chart_wealth_and_health(filtered_world_wealth_and_health))

    chosen_metric = st.selectbox("Select a metric to explore:", options=["life_expectancy", "gdp_usd_per_capita", "population"])

    st.dataframe(filtered_world_wealth_and_health.pivot(index="country_name", on="year", values=chosen_metric))

    st.plotly_chart(WorldBankChartingHelper.chart_metric_by_country(filtered_world_wealth_and_health, chosen_metric))

