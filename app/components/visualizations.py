import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go


def stat_radar_comparison(page_key, player_indices=(0, 1)):
    state = getattr(st.session_state, page_key)
    players = [state["players"][i] for i in player_indices]


    # Get points by stat for each player
    points_by_stat_list = [p["tables"]["player_points_by_stat"] for p in players]

    # Combine all stat categories across both players
    all_categories = set(points_by_stat_list[0].index) | set(points_by_stat_list[1].index)

    # Ensure both players have values for all categories, filling missing ones with 0
    values_list = []
    for points_by_stat in points_by_stat_list:
        values = [points_by_stat.get(cat, 0) for cat in all_categories]
        values_list.append(values)

    # Close the shape for a FIFA-style hex effect
    all_categories = list(all_categories)  # Convert set to list for ordered indexing
    all_categories.append(all_categories[0])
    for values in values_list:
        values.append(values[0])

    colors = ["#FFD700", "#1E90FF"]  # Gold for Player 1, DodgerBlue for Player 2

    fig = go.Figure()
    for i, values in enumerate(values_list):
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=all_categories,
            fill='toself',
            line=dict(color=colors[i], width=2),
            marker=dict(size=4, color=colors[i]),
            hoverinfo="text",
            text=[f"{cat}: {val}" for cat, val in zip(all_categories, values)],
            name=f"{players[i]['name']}"  # Adjust index to match player count
        ))

    fig.update_layout(
        autosize=True,
        width=300,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        polar=dict(
            bgcolor="#1E1E1E",
            radialaxis=dict(visible=True, showticklabels=False, gridcolor="rgba(255,255,255,0.2)"),
            angularaxis=dict(showline=False, gridcolor="rgba(255,255,255,0.2)")
        ),
        showlegend=True,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)


def stat_radar_2(page_key, player_index=0):
    state = getattr(st.session_state, page_key)
    player = state["players"][player_index]
    points_by_stat = player["tables"]["player_points_by_stat"]
    nonzero_points_series = points_by_stat[points_by_stat != 0]

    if nonzero_points_series.sum() == 0:
        st.warning("No points scored in this period.")
        return

    categories = nonzero_points_series.index.tolist()
    values = nonzero_points_series.values.tolist()

    # Close the shape for a FIFA-style hex effect
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line=dict(color="#FFD700", width=2),
        marker=dict(size=4, color="#FFD700"),
        hoverinfo="text",
        text=[f"{cat}: {val}" for cat, val in zip(categories, values)]
    ))

    fig.update_layout(
        autosize=True,  # Allows Streamlit to properly resize
        width=250,  # Adjust width for compact fit
        height=250,  # Keep height in proportion
        margin=dict(l=20, r=20, t=20, b=20),  # Tight margins to prevent cut-off
        polar=dict(
            bgcolor="#1E1E1E",
            radialaxis=dict(
                visible=True,
                showticklabels=False,
                gridcolor="rgba(255,255,255,0.2)"
            ),
            angularaxis=dict(
                showline=False,
                gridcolor="rgba(255,255,255,0.2)"
            )
        ),
        showlegend=False,
        template="plotly_dark"
    )

    # Use st.plotly_chart instead of st.write for better scaling
    st.plotly_chart(fig, use_container_width=True)


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






