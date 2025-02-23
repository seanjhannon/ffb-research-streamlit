import streamlit as st

st.write(st.session_state)

full_data = st.session_state.tables["full_data"]
st.write(full_data)