import streamlit as st
import geojson
import shapely.geometry
import folium
from streamlit_folium import st_folium

def simplify_features(features, tolerance=0.00001):
    """Simplifies Polygon/MultiPolygon features while preserving properties."""
    simplified = []
    for feature in features:
        geom_type = feature['geometry']['type']
        if geom_type in ['Polygon', 'MultiPolygon']:
            shapely_geom = shapely.geometry.shape(feature['geometry'])
            simplified_geom = shapely_geom.simplify(tolerance, preserve_topology=True)
            new_feature = geojson.Feature(
                geometry=shapely.geometry.mapping(simplified_geom), 
                properties=feature['properties']
            )
            simplified.append(new_feature)
        else:
            simplified.append(feature)
    return simplified

def count_coordinates(geometry):
    """Counts total number of coordinates in a geometry."""
    if geometry['type'] == 'Polygon':
        return sum(len(ring) for ring in geometry['coordinates'])
    elif geometry['type'] == 'MultiPolygon':
        return sum(sum(len(ring) for ring in polygon) for polygon in geometry['coordinates'])
    return 0

st.title("GeoJSON Polygon Simplifier")
st.write("Upload a GeoJSON file to simplify polygon geometries and compare before/after visualizations.")

# More conservative tolerance range for 50-80% reduction
tolerance = st.slider(
    "Simplification Tolerance (degrees)", 
    min_value=0.00001, 
    max_value=0.0001, 
    value=0.00003,
    step=0.00001,
    format="%.5f",
    help="Lower values preserve more detail. Start with 0.00003 and adjust as needed."
)

uploaded_file = st.file_uploader("Upload your GeoJSON file", type=["geojson", "json"])

if uploaded_file:
    data = uploaded_file.read().decode("utf-8")
    geojson_obj = geojson.loads(data)
    
    # Support FeatureCollection and single Feature
    if geojson_obj['type'] == 'FeatureCollection':
        features = geojson_obj['features']
    elif geojson_obj['type'] == 'Feature':
        features = [geojson_obj]
    else:
        st.error("Invalid GeoJSON type. Please upload a FeatureCollection or Feature.")
        st.stop()
    
    # Simplify features
    simplified_features = simplify_features(features, tolerance)
    simplified_geojson = geojson.FeatureCollection(simplified_features)
    original_geojson = geojson.FeatureCollection(features)
    
    # Calculate statistics
    original_coords = sum(count_coordinates(f['geometry']) for f in features 
                         if f['geometry']['type'] in ['Polygon', 'MultiPolygon'])
    simplified_coords = sum(count_coordinates(f['geometry']) for f in simplified_features 
                           if f['geometry']['type'] in ['Polygon', 'MultiPolygon'])
    reduction_pct = ((original_coords - simplified_coords) / original_coords * 100) if original_coords > 0 else 0
    
    st.subheader("Simplification Results")
    col1, col2, col3 = st.columns(3)
    col1.metric("Original Points", f"{original_coords:,}")
    col2.metric("Simplified Points", f"{simplified_coords:,}")
    col3.metric("Reduction", f"{reduction_pct:.1f}%")
    
    # Show warning if reduction is too extreme
    if reduction_pct > 85:
        st.warning("⚠️ Reduction exceeds 85%. Consider lowering the tolerance to preserve shape better.")
    elif reduction_pct >= 50 and reduction_pct <= 80:
        st.success("✅ Good reduction range (50-80%)")
    
    # Calculate center point for maps
    first_geom = shapely.geometry.shape(features[0]['geometry'])
    centroid = first_geom.centroid
    center_lat, center_lon = centroid.y, centroid.x
    
    # Create side-by-side maps
    st.subheader("Visual Comparison")
    col_before, col_after = st.columns(2)
    
    with col_before:
        st.write("**Before Simplification**")
        map_before = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        folium.GeoJson(
            original_geojson,
            name="Original",
            style_function=lambda x: {
                'fillColor': 'blue',
                'color': 'blue',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(map_before)
        st_folium(map_before, width=350, height=500)
    
    with col_after:
        st.write("**After Simplification**")
        map_after = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        folium.GeoJson(
            simplified_geojson,
            name="Simplified",
            style_function=lambda x: {
                'fillColor': 'green',
                'color': 'green',
                'weight': 2,
                'fillOpacity': 0.3
            }
        ).add_to(map_after)
        st_folium(map_after, width=350, height=500)
    
    # Download section
    st.subheader("Download Simplified GeoJSON")
    simplified_str = geojson.dumps(simplified_geojson)
    st.download_button(
        label="Download Simplified GeoJSON",
        data=simplified_str,
        file_name="simplified.geojson",
        mime="application/json"
    )
