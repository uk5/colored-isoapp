import streamlit as st
import geopandas as gpd
import requests
from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
import contextily as ctx
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

ORS_API_KEY = '5b3ce3597851110001cf62483c9fa348736d4315a694410fd874e918'

def get_isochrones(lat, lon, minutes):
    url = 'https://api.openrouteservice.org/v2/isochrones/driving-car'
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'locations': [[lon, lat]],
        'range': [m * 60 for m in minutes]
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def create_isochrones_gdf(isochrones_data):
    polygons = [Polygon(feature['geometry']['coordinates'][0]) for feature in isochrones_data['features']]
    return gpd.GeoDataFrame(geometry=polygons, crs='EPSG:4326')

def main():
    st.set_page_config(page_title="Isochrone Map Generator", layout="wide")

    # Add header
    st.markdown("<h1 style='text-align: center;'>Isochrone Map Generator</h1>", unsafe_allow_html=True)

    # Sidebar content
    logo_url = "grmc_advisory_services_logo.png"
    try:
        st.sidebar.image(logo_url, use_column_width=True)
    except FileNotFoundError:
        st.sidebar.error(f"Logo file '{logo_url}' not found. Please ensure it is in the same directory as this script.")

    st.sidebar.title('Generate Isochrone Maps')
    st.sidebar.write("Enter coordinates and isochrone times to generate a map.")

    lat = st.sidebar.number_input("Enter the latitude:", value=25.00307729247567)
    lon = st.sidebar.number_input("Enter the longitude:", value=55.167526256190804)
    user_input = st.sidebar.text_input("Enter isochrone times in minutes (e.g., 5,10,15,20):", help="Comma-separated times in minutes.")

    if user_input:
        try:
            minutes = list(map(int, user_input.split(',')))
            isochrone_data = get_isochrones(lat, lon, minutes)
            if isochrone_data:
                gdf_isochrones = create_isochrones_gdf(isochrone_data)
                gdf_location = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs='EPSG:4326')

                fig, ax = plt.subplots(figsize=(8, 8))
                gdf_isochrones.plot(ax=ax, alpha=0.5, edgecolor='k', cmap='viridis')
                gdf_location.plot(ax=ax, color='red', markersize=100)
                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs='EPSG:4326')

                ax.set_title('Isochrone Map', fontsize=16)
                ax.set_xlabel('Longitude', fontsize=12)
                ax.set_ylabel('Latitude', fontsize=12)

                st.pyplot(fig)

                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    pdf.savefig(fig)

                st.sidebar.download_button(
                    label="Download map as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="isochrone_map.pdf",
                    mime="application/pdf"
                )

        except requests.HTTPError as e:
            st.sidebar.error(f"HTTP error occurred: {e}")
        except ValueError as e:
            st.sidebar.error(f"Error: {e}")
        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")

    # Add footer
    st.markdown(
        """
        <div style='text-align: center; padding: 10px;'>
            <p style='font-family: Arial, sans-serif; color: #666;'>Powered by OpenRouteService & Streamlit</p>
            <p style='font-family: Arial, sans-serif; color: #666;'>GRMC Advisory Services. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
