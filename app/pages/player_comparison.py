import streamlit as st
import utils.data_loader as data_loader
import components.visualizations as viz

if "player_comparison" not in st.session_state:
    data_loader.setup_state_player_comparison()
    data_loader.build_tables_player_comparison()

selector_container = st.container()
with selector_container:
    selector_cols = st.columns(3)
    with selector_cols[0]:
        viz.FormatSelector()

    with selector_cols[1]:
        page_state =
        current_weeks = page_state["user_input"]["selected_weeks"]
        all_weeks = page_state["tables"]["full_data"]['week'].unique().tolist()
        if len(all_weeks) == 1:
            return
        else:
            st.slider(
                "Select a range of weeks",
                min_value=min(all_weeks),
                max_value=max(all_weeks),
                value=current_weeks,
                step=1,
                key="selected_weeks",  # flat key for the slider widget
                on_change=data_loader.generic_on_change,
                args=(
                    "selected_weeks",
                    ["user_input", "selected_weeks"],
                    [data_loader.refresh_child_tables_player_details]
                # assuming update_state refreshes your tables for the new week range
                )
            )

comparison_columns = st.columns(2)

st.write(st.session_state.selected_scoring_format)

with comparison_columns[0]:
    st.write('player_1')


    #Header

    #KPIS

    #Radar

with comparison_columns[1]:
    st.write('player_2')
