"""
CS230: Section HB1
Name: Zach Feldman
Data: McDonalds Data Set
Description: This Program is a streamlit dashboard configured with a data set for 14,000+ McDonald's stores across the US
A user inputs their address, and the script will geocode their entry to find the 10 closest McDonald's stores in their state
Then, the program displays this information with a pydeck map, and displays the addresses of the closest stores sorted by distance
I pledge that I have completed the programming assignment independently.
I have not copied the code from a student or any source.
I have not given my code to any student.

URL: <URL for streamlit dashboard here>
"""

import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk

import geopandas as gpd
import geopy
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# List of all of the states for our selectbox
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# this function uses geocoding to take an address and retrieve latitude and longitude values
def geocode_address(street, city, province, country):

    geolocator = Nominatim(user_agent="GTA Lookup")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    location = geolocator.geocode(street+", "+city+", "+province+", "+country)

    lat = location.latitude
    lon = location.longitude

    return (lat, lon) # return a tuple of latitude and longitude

# this function takes two tuples of (lat, lon)
# and returns the geodesic distance between the two points in kilometers
def get_distance(coords_1, coords_2):  
    return geodesic(coords_1, coords_2).km

# this function takes the user's coordinates as well as the data points for the mcdonalds
# but does not return a value. Instead it displays the map of the data points
def map_stores(user_coords, data_points):
    # invoke the pydeck integration in streamlit to show the mapped lat & lon data
    st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=user_coords[0],
                longitude=user_coords[1],
                zoom=10
            ),
            layers=[
                pdk.Layer(
                'ScatterplotLayer',
                data_points,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=20,
                radius_min_pixels=4
                ),
                pdk.Layer(
                'ScatterplotLayer',
                data=[[user_coords[1], user_coords[0]]], # pipe in user coordinates to show where they are
                get_position='-',
                get_color='[0, 168, 81, 160]',
                get_radius=20,
                radius_min_pixels=4
                )
            ],
        ))

# read the cleaned mc_data
mc_data = pd.read_csv('mcdonalds_clean.csv')

# header & sidebar information
st.title(f'McDonalds Store Locator')
st.sidebar.markdown(f'### Enter your address to find the 10 closest McDonalds stores in your state!')

# input fields for sidebar

street = st.sidebar.text_input("Address", "175 Forest St")
city = st.sidebar.text_input("City", "Waltham")
state = st.sidebar.selectbox('State', STATES, index=21)
country = "United States" # hard code country because we only have data for US

st.sidebar.markdown(f'#### once you enter your data the map should present your location with a green dot, and the McDonald\'s stores with red dots!')

# we must put this logic inside a try except block to not show potential errors when user inputs a bad address
# instead, we ask them to revise the address they input and check for errors (makes for a better user experience)
try:
    # get a tuple of the user entered coordinates
    user_coords = geocode_address(street, city, state, country)

    # get a boolean panda series filtered to the users state
    # because we don't want to parse through 14,000 computations every refresh
    filtered_state = mc_data['state'] == state.upper()
    mc_data = mc_data[filtered_state] # boil down the mc_data to just the states we want


    # now that we have our user coordinates
    # we can update our dictionary with the distances for each of those stores
    # to do this, we can use an amazing pandas function called 'apply'
    # in conjunction with a lambda function that runs for every lat long pair for the data frame
    mc_data['distance_km'] = mc_data.apply(lambda store : get_distance(user_coords, (store['Y'], store['X'])), axis = 1) 

    # boil down the stores to the 10 closest stores
    ten_closest_stores = mc_data.nsmallest(n=10, columns='distance_km')

    # create a dictionary of the lat & lon of the stores in the selected user state
    store_dict = {'lon': ten_closest_stores['X'], 'lat': ten_closest_stores['Y']}
    data_points = pd.DataFrame(data=store_dict)

    # invoke our function that displays the map on the streamlit dashboard
    map_stores(user_coords, data_points)

    st.markdown(f'### Below is a list of the 10 {state} McDonalds closest to: \n `{street}, {city}`')
    # print out some aggregate data about the closest mcdonalds stores
    st.write(ten_closest_stores[['address', 'city', 'phone', 'distance_km']])
except AttributeError:
    st.markdown(f'### Could not find McDonald\'s stores near the address: \n`{street}, {city}, {state}`\n ### Please revise input to find stores!')
