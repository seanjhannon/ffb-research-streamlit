import streamlit as st
import utils.data_loader as data_loader

# Set Streamlit page configuration (optional)
st.set_page_config(page_title="FFB Research", page_icon="📊", layout="wide")

data_loader.setup_state_main() # Create necessary state variables for boot

pages = [
    st.Page("pages/custom_scoring.py", title="Custom Scoring"),
    st.Page("pages/player_details.py", title="Details"),
    st.Page("pages/player_details_new.py", title="Details new"),
    st.Page("pages/player_comparison.py", title="player comp"),

]

pg = st.navigation(pages)
pg.run()




# # App Title
# st.title("Welcome to FFB Research Streamlit App")
#
# st.write("Use the sidebar to navigate between pages.")

data_loader.initialize_state()