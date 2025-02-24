import streamlit as st
import utils.data_loader as data_loader_experimental
# Set Streamlit page configuration (optional)
st.set_page_config(page_title="FFB Research", page_icon="📊", layout="wide")

data_loader_experimental.setup_state_main() # Create necessary state variables for boot

pages = [
    st.Page("pages/custom_scoring.py", title="Custom Scoring"),
    st.Page("pages/player_details.py", title="Player Details"),
    st.Page("pages/player_comparison.py", title="Compare Players"),

]

pg = st.navigation(pages)
pg.run()

