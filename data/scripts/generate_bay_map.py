import os
import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import MarkerCluster

def create_bay_map():
    # 1. Paths
    base_dir = "/workspaces/NorthEast/data"
    shp_path = os.path.join(base_dir, "data/nga_shp/nga_admin2.shp")
    schools_path = os.path.join(base_dir, "data/north_east_schools_complete.csv")
    conflict_path = os.path.join(base_dir, "data/conflict_data_nga.csv")
    output_map = os.path.join(base_dir, "maps/bay_states_basemap.html")

    # 2. Load and Filter LGA Boundaries
    print("Loading LGA boundaries...")
    gdf_lga = gpd.read_file(shp_path)
    # Filter for BAY states: Borno, Adamawa, Yobe
    bay_states = ["Borno", "Adamawa", "Yobe"]
    # Update to lowercase column names found in the shapefile
    gdf_bay = gdf_lga[gdf_lga['adm1_name'].isin(bay_states)].copy()
    
    # Drop non-serializable columns (like Timestamp 'valid_on')
    if 'valid_on' in gdf_bay.columns:
        gdf_bay = gdf_bay.drop(columns=['valid_on'])
    if 'valid_to' in gdf_bay.columns:
        gdf_bay = gdf_bay.drop(columns=['valid_to'])

    # 3. Initialize Folium Map (centered on BAY area)
    m = folium.Map(location=[11.5, 13.0], zoom_start=7, tiles="cartodbpositron")

    # 4. Add LGA Boundaries
    folium.GeoJson(
        gdf_bay,
        name="LGA Boundaries",
        style_function=lambda x: {
            "fillColor": "#f2f2f2",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.1,
        },
        tooltip=folium.GeoJsonTooltip(fields=["adm1_name", "adm2_name"], aliases=["State", "LGA"])
    ).add_to(m)

    # 5. Add Schools (Clustered)
    print("Adding schools...")
    df_schools = pd.read_csv(schools_path)
    # Filter for schools in BAY area (using coordinates as simple filter)
    # Approx bounding box for BAY: Lat [8.5, 13.5], Lon [11.0, 15.0]
    df_schools = df_schools[
        (df_schools['latitude'].between(8.5, 13.5)) & 
        (df_schools['longitude'].between(11.0, 15.0))
    ]
    
    school_cluster = MarkerCluster(name="Schools").add_to(m)
    for idx, row in df_schools.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                color="blue",
                fill=True,
                fill_color="blue",
                popup=f"School: {row['school_name']}<br>Level: {row['level']}",
            ).add_to(school_cluster)

    # 6. Add Conflict Events
    print("Adding conflict events...")
    df_conflict = pd.read_csv(conflict_path)
    # Filter for conflict events in BAY area
    df_conflict = df_conflict[
        (df_conflict['latitude'].between(8.5, 13.5)) & 
        (df_conflict['longitude'].between(11.0, 15.0))
    ]
    
    conflict_cluster = MarkerCluster(name="Conflict Events").add_to(m)
    for idx, row in df_conflict.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.Icon(color="red", icon="info-sign"),
                popup=(
                    f"Conflict: {row['conflict_name']}<br>"
                    f"Date: {row['source_date']}<br>"
                    f"Casualties (Best): {row['best']}"
                ),
            ).add_to(conflict_cluster)

    # 7. Add Layer Control
    folium.LayerControl().add_to(m)

    # 8. Save Map
    os.makedirs(os.path.dirname(output_map), exist_ok=True)
    m.save(output_map)
    print(f"Map saved to: {output_map}")

if __name__ == "__main__":
    create_bay_map()
