import streamlit as st

import utils.data_loader as data_loader
from utils.scoring import StandardScoringFormat, PPRScoringFormat

# Set Streamlit page configuration (optional)
st.set_page_config(page_title="FFB Research", page_icon="📊", layout="wide")

# App Title
st.title("Welcome to FFB Research Streamlit App")

st.write("Use the sidebar to navigate between pages.")

data_loader.initialize_state()