import streamlit as st

# Set Streamlit page configuration (optional)
st.set_page_config(page_title="FFB Research", page_icon="📊", layout="wide")

# App Title
st.title("Welcome to FFB Research Streamlit App")

st.write("Use the sidebar to navigate between pages.")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.info("Select a page above to continue.")

st.sidebar.write("Pages:")
st.sidebar.page_link("pages/page1.py", label="📈 Data Analysis")
st.sidebar.page_link("pages/page2.py", label="🔍 Insights")
st.sidebar.page_link("pages/page3.py", label="⚙️ Settings")