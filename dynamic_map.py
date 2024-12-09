import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Load the new dataset
data_path = 'Overall_Boston_violations.csv'  # Uploaded dataset
geojson_path = 'boston_neighborhoods.geojson'  # Path to GeoJSON file
data = pd.read_csv(data_path, low_memory=False)
geo_data = gpd.read_file(geojson_path)

# Preprocess the data
data['count'] = pd.to_numeric(data['count'], errors='coerce')  # Ensure count is numeric
data['year'] = data['year'].astype(str)  # Ensure year is a string

# Streamlit Sidebar for Year Selection
st.sidebar.title("Year Selection")
years = sorted(data['year'].dropna().unique())
selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years[:1])

# Filter and Aggregate Data Based on Selected Years
if selected_years:
    filtered_data = data[data['year'].isin(selected_years)]
    aggregated_data = (
        filtered_data.groupby('Neighbourhood', as_index=False)
        .agg({'count': 'sum'})
    )
    
    # Merge Aggregated Data with GeoJSON
    merged_data = geo_data.merge(aggregated_data, left_on='neighborhood', right_on='Neighbourhood', how='left')
    merged_data['count'] = merged_data['count'].fillna(0)
    
    # Calculate Dynamic Color Thresholds
    multiplier = len(selected_years)
    red_threshold = 100 * multiplier
    orange_threshold = 50 * multiplier

    # Define Color Scale Function
    def get_color_scale(value):
        if value > red_threshold:
            return '#FF0000'  # Red for high violations
        elif value > orange_threshold:
            return '#FFA500'  # Orange for moderate violations
        elif value > 10 * multiplier:
            return '#FFFF00'  # Yellow for low violations
        else:
            return '#00FF00'  # Green for very low violations

    # Create Folium Map
    boston_map = folium.Map(location=[42.3601, -71.0589], zoom_start=12, tiles='CartoDB positron')
    for _, row in merged_data.iterrows():
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feature, row=row: {
                'fillColor': get_color_scale(row['count']),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,
            },
            tooltip=folium.Tooltip(f"{row['neighborhood']}: {row['count']} violations"),
        ).add_to(boston_map)

    # Display the Map in Streamlit
    st.title("Boston Neighborhood Violations")
    st.write(f"Selected Years: {', '.join(selected_years)}")
    st.write(f"Color Thresholds: Red > {red_threshold}, Orange > {orange_threshold}, Yellow > {10 * multiplier}")
    st_folium(boston_map, width=700, height=500)
else:
    st.write("Please select at least one year to display the map.")
