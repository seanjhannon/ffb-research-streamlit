import pandas as pd
import streamlit as st
import utils.data_loader as data_loader
import numpy as np
import plotly.graph_objects as go


def stat_radar(page_key, player_index=0):
    state = getattr(st.session_state, page_key)
    player = state["players"][player_index]
    points_by_stat = player["tables"]["player_points_by_stat"]
    nonzero_points_series = points_by_stat[points_by_stat != 0]
    if nonzero_points_series.sum() == 0:
        st.warning("This dude didn't score any points in this time period!")
        return

    # Extract categories and values programmatically
    categories = nonzero_points_series.index.tolist()  # List of categories
    values = nonzero_points_series.values.tolist()
    # List of corresponding values

    st.subheader(f"How {player['name']} Scores")
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Fantasy Scoring',
        hovertemplate='<b>Stat</b>: %{theta} <br>'
                      '<b>Points Scored</b>: %{r}<br>'
                      '<extra></extra>'
    ))

    # Dynamically adjust the range based on the values
    max_value = max(values)
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max_value * 1.1]  # Slightly expand the range for aesthetics
            )
        ),
        showlegend=False,
        # title="Fantasy Football Scoring Breakdown",
        template='plotly_dark'  # Optional: adds a dark theme to the chart
    )
    st.write(fig)

def custom_bar(page_key,
               player_index=0):
    st.subheader("Self-Service Bar Chart")
    player_data = getattr(st.session_state,page_key)["players"][player_index]["tables"]["player_data"]
    player_data_numeric = (player_data.drop(columns=[
        "season", "week", "fantasy_points", "fantasy_points_ppr"
    ]).rename(columns={"calc_fantasy_points": "fantasy_points"}).select_dtypes(include=np.number))

    valid_cols = (player_data_numeric != 0).any() & player_data_numeric.notna().any()
    df_non_zero = player_data_numeric.loc[:, valid_cols]

    # Dropdown to select y-axis column
    y_column = st.selectbox(
        "Select a column to graph (y-axis):",
        options=df_non_zero.columns,
        format_func=lambda col: col.replace("_", " ").title(),
    )

    # Ensure we're plotting from df_non_zero
    st.bar_chart(data=df_non_zero.set_index(player_data["week"])[[y_column]])


def CustomBar(state):
    # Title
    st.subheader("Self-Service Bar Chart")

    player_data = state["tables"]["player_data"]

    player_data_numeric = (player_data.drop(columns=[
        "season", "week", "fantasy_points", "fantasy_points_ppr"
    ]).rename(columns={"calc_fantasy_points": "fantasy_points"}).select_dtypes(include=np.number))

    valid_cols = (player_data_numeric != 0).any() & player_data_numeric.notna().any()
    df_non_zero = player_data_numeric.loc[:, valid_cols]

    # Dropdown to select y-axis column
    y_column = st.selectbox(
        "Select a column to graph (y-axis):",
        options=df_non_zero.columns,
        format_func=lambda col: col.replace("_", " ").title(),
    )

    # Ensure we're plotting from df_non_zero
    st.bar_chart(data=df_non_zero.set_index(player_data["week"])[[y_column]])







