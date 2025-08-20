import streamlit as st
import json

def correct_geojson(geojson_data):
    """
    Corrects a GeoJSON object based on the specified requirements.

    Args:
        geojson_data (dict): The GeoJSON data as a Python dictionary.

    Returns:
        dict: The corrected GeoJSON data.
    """
    if "features" in geojson_data and isinstance(geojson_data["features"], list):
        for feature in geojson_data["features"]:
            if isinstance(feature, dict):
                # 1. remove the "id" field
                if "id" in feature:
                    del feature["id"]

                if "properties" in feature and isinstance(feature["properties"], dict):
                    properties = feature["properties"]
                    # 2. Rename "plot_id" to "ProductionPlace"
                    if "plot_id" in properties:
                        properties["ProductionPlace"] = properties.pop("plot_id")
                    # 3. Rename "country_code" to "ProducerCountry"
                    if "country_code" in properties:
                        properties["ProducerCountry"] = properties.pop("country_code")
    return geojson_data

def main():
    st.set_page_config(page_title="GeoJSON Corrector", layout="centered")
    st.title("GeoJSON File Corrector")

    st.write("Upload a GeoJSON file to correct it based on the specified requirements.")

    uploaded_file = st.file_uploader("Choose a GeoJSON file", type="geojson")

    if uploaded_file is not None:
        try:
            # Read the uploaded file's content as a string
            string_data = uploaded_file.getvalue().decode("utf-8")
            geojson_data = json.loads(string_data)

            st.write("Original GeoJSON snippet:")
            st.json(dict(list(geojson_data.items())[:2])) # Display first 2 items for brevity

            # Process the GeoJSON data
            corrected_geojson_data = correct_geojson(geojson_data)

            st.write("Corrected GeoJSON snippet:")
            st.json(dict(list(corrected_geojson_data.items())[:2]))

            # Convert the corrected data to a string for download
            corrected_geojson_string = json.dumps(corrected_geojson_data, indent=2)

            st.download_button(
                label="Download Corrected GeoJSON",
                data=corrected_geojson_string,
                file_name="corrected_geojson.geojson",
                mime="application/json"
            )
        except json.JSONDecodeError:
            st.error("Error: The uploaded file is not a valid GeoJSON file.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
