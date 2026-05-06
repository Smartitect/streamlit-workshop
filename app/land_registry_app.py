import streamlit as st
from pathlib import Path

from data_wranglers import LandRegistryDataWrangler
from charting_helpers import LandRegistryChartingHelper

st.set_page_config(page_title="Property Price Analysis")
st.title("Property Price Analysis")

MAX_DATA_POINTS_TO_MAP = 50000

LAND_REGISTRY_DATABASE_PATH = Path("../databases/land_registry.db")
land_registry_data_wrangler = LandRegistryDataWrangler(LAND_REGISTRY_DATABASE_PATH)

@st.cache_data
def get_min_max_dates():
    return land_registry_data_wrangler.get_min_max_dates()

min_date, max_date = get_min_max_dates()

@st.cache_data
def get_property_types():
    return land_registry_data_wrangler.get_property_types()

property_types = get_property_types()

# Enter postcode to explore
postcode = st.text_input("Enter the postcode (or part of postcode) you want to explore:", value="NP19")

property_type = st.selectbox(
    "Select a property type to filter by (optional):",
    options=["All"] + property_types,
    index=0
)

if property_type == "All":
    property_type = None

min_date = st.date_input(
    "Select a minimum date to filter by (optional):",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

max_date = st.date_input(
    "Select a maximum date to filter by (optional):",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

summary_statistics_for_postcode = land_registry_data_wrangler.generate_summary_statistics_for_postcode(
    postcode=postcode,
    property_type=property_type,
    min_date=min_date,
    max_date=max_date,
    ).pl()

total_sales = summary_statistics_for_postcode["number_of_sales"].sum()

st.metric(label="Total Sales", value=total_sales)

st.dataframe(summary_statistics_for_postcode)

insights_for_postcode = land_registry_data_wrangler.generate_insights_for_postcode(
    postcode=postcode,
    property_type=property_type,
    min_date=min_date,
    max_date=max_date,
    )

st.plotly_chart(LandRegistryChartingHelper.chart_median_price_by_month_and_property_type(insights_for_postcode))

st.plotly_chart(LandRegistryChartingHelper.chart_number_of_sales_by_month_and_property_type(insights_for_postcode))

if total_sales < MAX_DATA_POINTS_TO_MAP:
    
    indivial_property_sales = land_registry_data_wrangler.get_all_matching_properties(
        postcode=postcode,
        property_type=property_type,
        min_date=min_date,
        max_date=max_date,
    )
    
    st.plotly_chart(LandRegistryChartingHelper.map_individual_property_sales(indivial_property_sales))
else:
    st.write(f"Too many sales to map individual property sales. Please apply more filters to reduce the number of sales below {MAX_DATA_POINTS_TO_MAP} to see the map.")