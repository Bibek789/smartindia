import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import pydeck as pdk

# --- Page Configuration ---
st.set_page_config(
    page_title="FloatChat ARGO Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Database Connection ---
@st.cache_data
def fetch_data(query):
    """Fetches data from the database and caches the result."""
    conn = sqlite3.connect("argo.db")
    return pd.read_sql_query(query, conn)

# --- Load Data ---
# Fetching a sample of data to keep the dashboard responsive.
# For a full dashboard, you might want more complex queries or to load all data.
query = """
SELECT
    m.temperature,
    m.salinity,
    m.pressure,
    p.latitude,
    p.longitude,
    p.cycle_number,
    f.platform_number
FROM measurements m
JOIN profiles p ON m.profile_id = p.id
JOIN floats f ON p.float_id = f.id
;
"""
df = fetch_data(query)

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")

platform = st.sidebar.selectbox(
    "Select a Float Platform:",
    options=[None] + sorted(df["platform_number"].unique())
)

if platform:
    filtered_df = df[df["platform_number"] == platform]
else:
    filtered_df = df

# --- Main Page ---
st.title("🌊 ARGO Float Data Dashboard")
st.markdown("An interactive dashboard to explore oceanographic data from ARGO floats.")

# --- Map Visualization ---
st.header("Float Locations")
if not filtered_df.empty:
    # Get the last known location for each float in the filtered data
    map_data = filtered_df[['platform_number', 'latitude', 'longitude']].groupby('platform_number').last().reset_index()

    if not map_data.empty:
        # Define the initial view state of the map (center, zoom, etc.)
        view_state = pdk.ViewState(
            latitude=map_data["latitude"].mean(),
            longitude=map_data["longitude"].mean(),
            zoom=1,
            pitch=45,
        )

        # Define the layer for the map (how the points are rendered)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position="[longitude, latitude]",
            get_fill_color="[200, 30, 0, 160]",
            get_radius=30000, # Radius in meters
            pickable=True # Allows tooltips
        )

        # Render the pydeck chart
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, map_style='mapbox://styles/mapbox/satellite-streets-v12', tooltip={"text": "Float: {platform_number}"}))
else:
    st.warning("No data to display on the map for the selected filter.")


# --- Visualizations ---
st.header("Float Data Visualization")

if not filtered_df.empty:
    # Use tabs for a cleaner layout
    tab1, tab2, tab3 = st.tabs(["Vertical Profiles", "T-S Diagram", "Cycle Comparison"])

    with tab1:
        st.subheader("Vertical Profiles")
        col1, col2 = st.columns(2)
        with col1:
            # Temperature vs. Pressure Profile
            fig1 = px.scatter(filtered_df, x="temperature", y="pressure", color="cycle_number",
                              title="Temperature vs. Pressure",
                              labels={'pressure': 'Pressure (dbar)', 'temperature': 'Temperature (°C)', 'cycle_number': 'Cycle'},
                              hover_data=['salinity'])
            fig1.update_yaxes(autorange="reversed") # Pressure increases with depth
            fig1.update_layout(title_x=0.5) # Center title
            st.plotly_chart(fig1, use_container_width=True, theme="streamlit")

        with col2:
            # Salinity vs. Pressure Profile
            fig2 = px.scatter(filtered_df, x="salinity", y="pressure", color="cycle_number",
                              title="Salinity vs. Pressure",
                              labels={'pressure': 'Pressure (dbar)', 'salinity': 'Salinity (PSU)', 'cycle_number': 'Cycle'},
                              hover_data=['temperature'])
            fig2.update_yaxes(autorange="reversed")
            fig2.update_layout(title_x=0.5) # Center title
            st.plotly_chart(fig2, use_container_width=True, theme="streamlit")

    with tab2:
        st.subheader("Temperature-Salinity (T-S) Diagram")
        fig3 = px.scatter(filtered_df, x="salinity", y="temperature", color="pressure",
                          title="T-S Diagram",
                          labels={'salinity': 'Salinity (PSU)', 'temperature': 'Temperature (°C)', 'pressure': 'Pressure (dbar)'})
        fig3.update_layout(title_x=0.5) # Center title
        st.plotly_chart(fig3, use_container_width=True, theme="streamlit")
else:
    st.info("Select a float from the sidebar to see its data visualizations.")

st.header("Data Explorer")
st.dataframe(filtered_df, use_container_width=True)