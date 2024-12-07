import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Load the data
data_path = 'Final_dataset.csv'  # Path to your dataset
geojson_path = 'boston_neighborhoods.geojson'  # Path to GeoJSON file
data = pd.read_csv(data_path, low_memory=False)
geo_data = gpd.read_file(geojson_path)

# Preprocess the data
data['no_of_violations'] = pd.to_numeric(data['no_of_violations'], errors='coerce')  # Ensure violations are numeric
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
        .agg({'no_of_violations': 'sum'})
    )
    
    # Merge Aggregated Data with GeoJSON
    merged_data = geo_data.merge(aggregated_data, left_on='neighborhood', right_on='Neighbourhood', how='left')
    merged_data['no_of_violations'] = merged_data['no_of_violations'].fillna(0)

    # Define Color Scale Function
    def get_color_scale(value):
        if value > 500:
            return '#FF0000'  # Red for high violations
        elif value > 100:
            return '#FFA500'  # Orange for moderate violations
        elif value > 10:
            return '#FFFF00'  # Yellow for low violations
        else:
            return '#00FF00'  # Green for very low violations

    # Create Folium Map
    boston_map = folium.Map(location=[42.3601, -71.0589], zoom_start=12, tiles='CartoDB positron')
    for _, row in merged_data.iterrows():
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feature, row=row: {
                'fillColor': get_color_scale(row['no_of_violations']),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,
            },
            tooltip=folium.Tooltip(f"{row['neighborhood']}: {row['no_of_violations']} violations"),
        ).add_to(boston_map)

    # Display the Map in Streamlit
    st.title("Boston Neighborhood Violations")
    st.write(f"Selected Years: {', '.join(selected_years)}")
    st_folium(boston_map, width=700, height=500)
else:
    st.write("Please select at least one year to display the map.")
