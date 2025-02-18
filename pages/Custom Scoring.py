import streamlit as st
from scoring import ScoringFormat

st.title("Create Custom Scoring Format")

# Initialize session state for custom scoring formats if not already set


# Function to create and store a new custom scoring format
def create_custom_scoring():
    name = st.text_input("Enter a name for your custom scoring format:")

    with st.form("custom_scoring_form",
                 ):
        st.write("### Scoring Values")
        pass_yards_value = st.number_input("Passing Yards (pts per yard)", value=0.04, step=0.01)
        pass_tds_value = st.number_input("Passing TDs (pts per TD)", value=4, step=1)
        pass_ints_value = st.number_input("Passing INTs (pts per INT)", value=-2, step=1)
        rush_yards_value = st.number_input("Rushing Yards (pts per yard)", value=0.1, step=0.01)
        rush_tds_value = st.number_input("Rushing TDs (pts per TD)", value=6, step=1)
        receptions_value = st.number_input("Receptions (pts per reception)", value=1.0, step=0.1)
        rec_yards_value = st.number_input("Receiving Yards (pts per yard)", value=0.1, step=0.01)
        rec_tds_value = st.number_input("Receiving TDs (pts per TD)", value=6, step=1)
        two_point_conversions_value = st.number_input("Two-Point Conversions (pts each)", value=2, step=1)
        fumble_recovery_td_value = st.number_input("Fumble Recovery TDs (pts each)", value=6, step=1)
        fumble_lost_value = st.number_input("Fumbles Lost (pts each)", value=-2, step=1)

        submitted = st.form_submit_button("Create Custom Format")

    if submitted and name:
        if name in st.session_state.custom_scoring_formats:
            st.warning(f"A scoring format named '{name}' already exists. Choose a different name.")
        else:
            scoring_values = {
                "pass_yards_value": pass_yards_value,
                "pass_tds_value": pass_tds_value,
                "pass_ints_value": pass_ints_value,
                "rush_yards_value": rush_yards_value,
                "rush_tds_value": rush_tds_value,
                "receptions_value": receptions_value,
                "rec_yards_value": rec_yards_value,
                "rec_tds_value": rec_tds_value,
                "two_point_conversions_value": two_point_conversions_value,
                "fumble_recovery_td_value": fumble_recovery_td_value,
                "fumble_lost_value": fumble_lost_value
            }

            new_format = ScoringFormat(name=name, **scoring_values)
            st.session_state.scoring_formats.append(new_format)
            st.success(f"Custom scoring format '{name}' created!")


# Display the form
create_custom_scoring()


# Display info about the saves scoring formats
st.subheader('Saved Scoring Formats')
scoring_format_n_cols = len(st.session_state.scoring_formats)
scoring_format_cols = st.columns(scoring_format_n_cols)
for i in range(scoring_format_n_cols):
    with scoring_format_cols[i]:
        st.write(st.session_state.scoring_formats[i].to_markdown())





# Optional: Provide a link back to the main page
# st.page_link("app.py", label="Back to Main Page", icon="🏠")
