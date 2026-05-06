import streamlit as st
from pathlib import Path

from data_wranglers import TitanicWrangler
from charting_helpers import TitanicChartingHelper

st.set_page_config(page_title="Titanic Data Exploration")

st.title("Titanic Data Exploration")


# ## Load and Prepare Passenger Data


RAW_DATA_PATH = Path("../data/titanic/titanic_passengers.csv")
assert RAW_DATA_PATH.exists(), f"Raw data file not found at {RAW_DATA_PATH}"

@st.cache_data()
def load_data():
    return TitanicWrangler.load_titanic_data(RAW_DATA_PATH)

titanic_passengers_raw = load_data()


titanic_passengers_cleaned = TitanicWrangler.prepare_data(titanic_passengers_raw)


with st.sidebar:
    st.markdown("""
    ## Exploratory Data Analysis

    Explore factors that appear to have contributed towards survival rates on the Titanic 🚢.

    Key🔑:
    - **N**=number of passengers
    - **S**=survival rate
    """)

    topic = st.radio(
        "Choose the topic you want to explore:",
        ["Women and Children", "Wealth", "Occupation"],
    )

if topic == "Women and Children":

    st.markdown("""
    ### Women and children first?
    This analysis certainly shows a general trend that females were given priority.  It's not so convicing for children!
    """)

    st.plotly_chart(TitanicChartingHelper.create_strip_boxplot(titanic_passengers_cleaned, 'Sex', 'Age'))

elif topic == "Wealth":

    st.markdown("""
    ### Did wealth have an influence?
    Survival rate overall is signfiicantly higher for first class versus third class.
    """)

    st.plotly_chart(TitanicChartingHelper.create_strip_boxplot(titanic_passengers_cleaned, 'Pclass', 'FareLog10'))
    
elif topic == "Occupation":

    st.markdown("""
    ### Was occupation a factor?
    Interesting that all 8 of the reverands on board perished.
    """)

    st.plotly_chart(TitanicChartingHelper.create_strip_boxplot(titanic_passengers_cleaned, 'Title', 'Age'))    
    
else:
    st.write("Please select a topic to explore from the sidebar.")

st.expander("View Passenger Details").dataframe(titanic_passengers_cleaned)