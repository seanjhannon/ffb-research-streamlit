import streamlit as st
import utils.data_loader as data_loader

def format_selector(page_key: str):
    """
    Displays a selectbox for choosing a scoring format.

    Args:
        page_key (str): The key to identify the page's state.
    """
    st.selectbox(
        "Select a Scoring Format",
        options=st.session_state.scoring_formats,  # Year options from 1999 to 2024
        index=st.session_state.scoring_formats.index(getattr(st.session_state, page_key)["selected_scoring_format"]),
        format_func=lambda x: x.name,
        key="selected_scoring_format",
        on_change=data_loader.handle_format_change,
        args=(page_key,)
    )


def week_selector(page_key: str):
    """
    Displays a slider for choosing a week.

    Args:
        page_key (str): The key to identify the page's state.
    """
    all_weeks = getattr(st.session_state, page_key)["full_data"]["week"].unique()
    if len(all_weeks) == 1:
        return
    else:
        selected_weeks = getattr(st.session_state, page_key)["selected_weeks"]
        st.slider(
            "Select a Range of Weeks",
            min_value=min(all_weeks), max_value=max(all_weeks), value=selected_weeks,
            step=1, key="selected_weeks",
            on_change=data_loader.handle_week_change,
            args=(page_key,)
        )

def year_selector(page_key: str):
    """
    Displays a selectbox for choosing a year.

    Args:
        page_key (str): The key to identify the page's state.
    """
    st.selectbox(
        "Select a Year",
        options=list(range(1999, 2025)),  # Year options from 1999 to 2024
        index=list(range(1999, 2025)).index(getattr(st.session_state, page_key)["selected_year"]),
        key="selected_year",
        on_change=data_loader.handle_year_change,
        args=(page_key,)
    )


def player_selector(page_key: str,
                    player_index:int=0,
                    label_visibility='visible'):
    """
    Displays a selectbox for choosing a player.

    Args:
        :param: page_key (str): The key to identify the page's state.
        :param: player_index: where in the state's list of players this guy sits.
    """
    all_players = getattr(st.session_state, page_key)["full_data"]["player_display_name"].unique()
    st.selectbox(
        "Choose Player",
        label_visibility=label_visibility,
        options=all_players,
        index=all_players.tolist().index(getattr(st.session_state, page_key)["players"][player_index]["name"]),
        key=f"selected_player_{player_index}",
        on_change=data_loader.handle_player_change,
        args=(page_key, player_index,)
    )


def xfp_toggle(page_key: str):
    """
    Displays a toggle for enabling/disabling XFP analysis.
    
    Args:
        page_key (str): The key to identify the page's state.
    """
    current_state = getattr(st.session_state, page_key).get("xfp_enabled", False)
    
    st.toggle(
        "Enable Expected Fantasy Points (XFP)",
        value=current_state,
        help="Enable advanced expected fantasy points analysis using play-by-play data. This may take longer to load.",
        key=f"xfp_toggle_{page_key}",
        on_change=_handle_xfp_toggle_change,
        args=(page_key,)
    )


def _handle_xfp_toggle_change(page_key: str):
    """Handle XFP toggle change."""
    new_value = st.session_state[f"xfp_toggle_{page_key}"]
    
    if new_value:
        data_loader.enable_xfp(page_key)
    else:
        data_loader.disable_xfp(page_key)