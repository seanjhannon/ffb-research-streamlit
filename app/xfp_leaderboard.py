import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data_loader import load_data, load_play_by_play_data, load_xfp_model
from utils.scoring import calculate_fantasy_points_vec, StandardScoringFormat, PPRScoringFormat
import utils.scoring as scoring

# ─── PALETTE ──────────────────────────────────────────────────────────────────
C_SELL    = "#FF6B35"
C_BUY     = "#0ECB81"
C_BREAK   = "#9B6DFF"
C_ELITE   = "#F0B429"
C_OTHER   = "#4A5580"
C_BG_PAGE = "#080C18"
C_BG_CARD = "#0F1629"
C_BORDER  = "#1A2540"
C_TEXT    = "#E4EAF6"
C_MUTED   = "#7B8DB0"

PAGE_KEY = "xfp_leaderboard"

# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
/* ── Page ── */
[data-testid="stAppViewContainer"] { background-color: #080C18; }
[data-testid="block-container"] { padding-top: 1rem; padding-bottom: 3rem; }
[data-testid="stVerticalBlock"] { gap: 0.5rem; }

/* ── Header ── */
.lb-header { border-bottom: 2px solid #F0B429; padding-bottom: 0.85rem; margin-bottom: 1.25rem; }
.lb-title {
    font-family: 'Arial Black', 'Impact', sans-serif;
    font-size: 2.2rem; font-weight: 900; color: #F0B429;
    letter-spacing: 0.06em; line-height: 1; margin: 0;
}
.lb-sub {
    font-size: 0.72rem; color: #7B8DB0;
    letter-spacing: 0.18em; text-transform: uppercase; margin-top: 0.3rem;
}

/* ── Summary bar ── */
.kpi-bar {
    display: flex; gap: 1px; background: #1A2540;
    border-radius: 10px; overflow: hidden; margin-bottom: 1.25rem;
}
.kpi-cell { flex: 1; background: #0F1629; padding: 0.85rem 1rem; text-align: center; }
.kpi-lbl { font-size: 0.6rem; color: #7B8DB0; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.3rem; }
.kpi-val { font-size: 1.45rem; font-weight: 800; line-height: 1; color: #E4EAF6; }
.kpi-val.gold   { color: #F0B429; }
.kpi-val.green  { color: #0ECB81; }
.kpi-val.orange { color: #FF6B35; }
.kpi-val.violet { color: #9B6DFF; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0F1629; border-radius: 8px;
    border: 1px solid #1A2540; gap: 0; padding: 3px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #7B8DB0; font-weight: 600;
    font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
    border-radius: 6px; padding: 0.45rem 1.25rem; border: none;
}
.stTabs [aria-selected="true"] { background: #1A2540 !important; color: #F0B429 !important; }

/* ── Player card ── */
.player-card {
    background: #0F1629; border: 1px solid #1A2540; border-radius: 12px;
    padding: 1rem 1.05rem; margin-bottom: 0.75rem;
    position: relative; overflow: hidden;
}
.player-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.card-sell::before  { background: linear-gradient(90deg, #FF6B35, #FF9A6C); }
.card-buy::before   { background: linear-gradient(90deg, #0ECB81, #0aaa6a); }
.card-break::before { background: linear-gradient(90deg, #9B6DFF, #c9a8ff); }
.card-elite::before { background: linear-gradient(90deg, #F0B429, #ffe08a); }
.card-other::before { background: #1A2540; }

/* ── Card top ── */
.card-top { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.8rem; }
.headshot-wrap { position: relative; width: 48px; height: 48px; flex-shrink: 0; }
.headshot-img {
    width: 48px; height: 48px; border-radius: 50%;
    object-fit: cover; border: 2px solid #1A2540; background: #1A2540;
    display: block;
}
.pos-badge {
    position: absolute; bottom: -2px; right: -4px;
    background: #1A2540; border: 1px solid #2A3A60; border-radius: 3px;
    font-size: 0.5rem; font-weight: 700; letter-spacing: 0.04em;
    padding: 1px 3px; color: #E4EAF6;
}
.p-name { font-size: 0.88rem; font-weight: 700; color: #E4EAF6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-team { font-size: 0.68rem; color: #7B8DB0; margin-top: 1px; }
.p-identity { flex: 1; min-width: 0; }
.tag {
    font-size: 0.58rem; font-weight: 800; letter-spacing: 0.07em;
    text-transform: uppercase; padding: 3px 7px; border-radius: 20px;
    white-space: nowrap; flex-shrink: 0;
}
.tag-sell  { background: rgba(255,107,53,.15);  color: #FF6B35; border: 1px solid rgba(255,107,53,.3); }
.tag-buy   { background: rgba(14,203,129,.12);  color: #0ECB81; border: 1px solid rgba(14,203,129,.25); }
.tag-break { background: rgba(155,109,255,.15); color: #9B6DFF; border: 1px solid rgba(155,109,255,.3); }
.tag-elite { background: rgba(240,180,41,.12);  color: #F0B429; border: 1px solid rgba(240,180,41,.25); }

/* ── Efficiency row ── */
.eff-row {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.7rem; padding: 0.55rem 0.7rem;
    background: #080C18; border-radius: 8px;
}
.eff-block, .ou-block, .trend-block { text-align: center; }
.eff-lbl, .ou-lbl, .trend-lbl {
    font-size: 0.56rem; color: #7B8DB0; letter-spacing: 0.12em;
    text-transform: uppercase; margin-bottom: 0.15rem; display: block;
}
.eff-val  { font-size: 1.3rem; font-weight: 800; line-height: 1; }
.ou-val   { font-size: 0.88rem; font-weight: 700; line-height: 1; }
.trend-val{ font-size: 1rem;   font-weight: 700; line-height: 1; }
.c-green  { color: #0ECB81; }
.c-red    { color: #FF4D4F; }
.c-orange { color: #FF6B35; }
.c-gold   { color: #F0B429; }
.c-violet { color: #9B6DFF; }
.c-muted  { color: #7B8DB0; }

/* ── FP bar ── */
.fp-bar-labels {
    display: flex; justify-content: space-between;
    font-size: 0.63rem; color: #7B8DB0; margin-bottom: 4px;
}
.fp-bar-labels strong { color: #E4EAF6; }
.fp-bar-track { height: 5px; background: #1A2540; border-radius: 3px; position: relative; overflow: hidden; }
.fp-fill { height: 100%; border-radius: 3px; position: absolute; top: 0; left: 0; }
.fill-over   { background: linear-gradient(90deg, #0ECB81, #06a85e); }
.fill-under  { background: linear-gradient(90deg, #FF4D4F, #cc3030); }

/* ── Footer ── */
.card-footer {
    display: flex; justify-content: space-around;
    padding-top: 0.55rem; border-top: 1px solid #1A2540;
    margin-top: 0.7rem;
}
.f-stat { text-align: center; }
.f-lbl  { font-size: 0.56rem; color: #7B8DB0; letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 2px; }
.f-val  { font-size: 0.82rem; font-weight: 600; color: #E4EAF6; }

/* ── Section dividers ── */
.section-head {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.2em;
    text-transform: uppercase; color: #7B8DB0;
    border-bottom: 1px solid #1A2540; padding-bottom: 0.5rem;
    margin-bottom: 0.75rem; margin-top: 1rem;
}

/* ── Selectbox label ── */
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stMultiSelect"] label {
    font-size: 0.68rem !important; color: #7B8DB0 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
}

/* ── Filter row ── */
.filter-row { background: #0F1629; border: 1px solid #1A2540; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem; }

/* ── Empty state ── */
.empty-state { padding: 3rem 2rem; text-align: center; color: #7B8DB0; font-size: 0.9rem; }

/* ── Insight box ── */
.insight-box {
    background: #0F1629; border-left: 3px solid;
    border-radius: 0 8px 8px 0; padding: 0.85rem 1rem;
    margin-bottom: 1.25rem; font-size: 0.82rem; color: #B0BCCF; line-height: 1.6;
}
.insight-box strong { color: #E4EAF6; }
.insight-sell  { border-color: #FF6B35; }
.insight-buy   { border-color: #0ECB81; }
.insight-break { border-color: #9B6DFF; }
</style>
""", unsafe_allow_html=True)


# ─── DATA COMPUTATION ─────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def compute_leaderboard(_xfp_calc, year, week_start, week_end, scoring_format_str, positions_tuple):
    """Compute xFP leaderboard for all players. Returns (leaderboard_df, weekly_df)."""

    pbp_raw  = load_play_by_play_data(year)
    weekly_raw = load_data(year)

    if pbp_raw.empty or weekly_raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Week filter
    pbp = pbp_raw[pbp_raw["week"].between(week_start, week_end)].copy() if "week" in pbp_raw.columns else pbp_raw.copy()

    # ── Build per-opportunity-type play frames ──
    def safe_col(df, col, default=0):
        return df[col] if col in df.columns else pd.Series(default, index=df.index)

    frames = []

    # Rush
    rush_mask = (safe_col(pbp, "rush_attempt") == 1) & (safe_col(pbp, "qb_scramble") != 1)
    if "rusher_player_id" in pbp.columns:
        subset = pbp[rush_mask & pbp["rusher_player_id"].notna()].copy()
        if not subset.empty:
            recs = subset.to_dict("records")
            frames.append(pd.DataFrame({
                "player_id": subset["rusher_player_id"].values,
                "week":      subset["week"].values if "week" in subset.columns else 0,
                "xfp":       [_xfp_calc.calculate_play_xfp(r, scoring_format_str) for r in recs],
                "opp_type":  "rush",
            }))

    # Targets (receivers)
    tgt_col = "target" if "target" in pbp.columns else ("pass_target" if "pass_target" in pbp.columns else None)
    if tgt_col and "receiver_player_id" in pbp.columns:
        target_mask = (safe_col(pbp, tgt_col) == 1)
        subset = pbp[target_mask & pbp["receiver_player_id"].notna()].copy()
        if not subset.empty:
            recs = subset.to_dict("records")
            frames.append(pd.DataFrame({
                "player_id": subset["receiver_player_id"].values,
                "week":      subset["week"].values if "week" in subset.columns else 0,
                "xfp":       [_xfp_calc.calculate_play_xfp(r, scoring_format_str) for r in recs],
                "opp_type":  "target",
            }))

    # Passes (QBs) – exclude scrambles and targeted plays to avoid double-count
    pass_mask = (
        (safe_col(pbp, "pass_attempt") == 1) &
        (safe_col(pbp, "qb_scramble") != 1) &
        (safe_col(pbp, tgt_col or "target") != 1)
    )
    if "passer_player_id" in pbp.columns:
        subset = pbp[pass_mask & pbp["passer_player_id"].notna()].copy()
        if not subset.empty:
            recs = subset.to_dict("records")
            frames.append(pd.DataFrame({
                "player_id": subset["passer_player_id"].values,
                "week":      subset["week"].values if "week" in subset.columns else 0,
                "xfp":       [_xfp_calc.calculate_play_xfp(r, scoring_format_str) for r in recs],
                "opp_type":  "pass",
            }))

    # Scrambles
    scram_mask = safe_col(pbp, "qb_scramble") == 1
    if "rusher_player_id" in pbp.columns:
        subset = pbp[scram_mask & pbp["rusher_player_id"].notna()].copy()
        if not subset.empty:
            recs = subset.to_dict("records")
            frames.append(pd.DataFrame({
                "player_id": subset["rusher_player_id"].values,
                "week":      subset["week"].values if "week" in subset.columns else 0,
                "xfp":       [_xfp_calc.calculate_play_xfp(r, scoring_format_str) for r in recs],
                "opp_type":  "scramble",
            }))

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    player_plays = pd.concat(frames, ignore_index=True)
    player_plays["player_id"] = player_plays["player_id"].astype(str)

    # ── Season aggregation ──
    player_season_xfp = player_plays.groupby("player_id").agg(
        expected_fp  = ("xfp", "sum"),
        total_plays  = ("xfp", "count"),
        rush_opps    = ("opp_type", lambda x: (x == "rush").sum()),
        target_opps  = ("opp_type", lambda x: (x == "target").sum()),
        pass_opps    = ("opp_type", lambda x: (x == "pass").sum()),
    ).reset_index()

    # ── Weekly xFP (trend) ──
    player_weekly_xfp = player_plays.groupby(["player_id", "week"]).agg(
        xfp = ("xfp", "sum")
    ).reset_index()

    # ── Actual FP from weekly data ──
    fmt_obj = PPRScoringFormat() if scoring_format_str == "ppr" else StandardScoringFormat()
    weekly_scored = calculate_fantasy_points_vec(weekly_raw.copy(), fmt_obj, scoring.stat_mapping_nfl_py)
    weekly_filtered = weekly_scored[weekly_scored["week"].between(week_start, week_end)].copy()

    player_season_actual = weekly_filtered.groupby("player_id").agg(
        actual_fp           = ("calc_fantasy_points", "sum"),
        games_played        = ("week", "nunique"),
        player_display_name = ("player_display_name", "last"),
        position            = ("position", "last"),
        recent_team         = ("recent_team", "last"),
        headshot_url        = ("headshot_url", "last"),
        targets             = ("targets", "sum"),
        carries             = ("carries", "sum"),
    ).reset_index()
    player_season_actual["player_id"] = player_season_actual["player_id"].astype(str)

    player_weekly_actual = weekly_filtered[["player_id", "week", "calc_fantasy_points"]].copy()
    player_weekly_actual["player_id"] = player_weekly_actual["player_id"].astype(str)
    player_weekly_actual = player_weekly_actual.rename(columns={"calc_fantasy_points": "actual_fp"})

    # ── Merge season data ──
    lb = player_season_actual.merge(player_season_xfp, on="player_id", how="inner")
    lb["efficiency"]   = lb["actual_fp"] / lb["expected_fp"].clip(lower=0.5)
    lb["over_under"]   = lb["actual_fp"] - lb["expected_fp"]
    lb["opportunities"] = lb["rush_opps"].fillna(0) + lb["target_opps"].fillna(0)

    # Position filter
    if positions_tuple:
        lb = lb[lb["position"].isin(positions_tuple)]

    # ── Trend: recent N weeks vs season ──
    all_weeks   = sorted(int(w) for w in player_plays["week"].dropna().unique())
    n_recent    = max(1, min(4, max(1, len(all_weeks) // 2)))
    recent_weeks = all_weeks[-n_recent:]

    recent_xfp = (
        player_weekly_xfp[player_weekly_xfp["week"].isin(recent_weeks)]
        .groupby("player_id").agg(recent_xfp=("xfp", "sum")).reset_index()
    )
    recent_actual = (
        player_weekly_actual[player_weekly_actual["week"].isin(recent_weeks)]
        .groupby("player_id").agg(recent_actual=("actual_fp", "sum")).reset_index()
    )

    lb = lb.merge(recent_xfp,    on="player_id", how="left")
    lb = lb.merge(recent_actual, on="player_id", how="left")
    lb["recent_xfp"]    = lb["recent_xfp"].fillna(0)
    lb["recent_actual"] = lb["recent_actual"].fillna(0)
    lb["recent_efficiency"] = lb["recent_actual"] / lb["recent_xfp"].clip(lower=0.5)
    lb["trend"]              = lb["recent_efficiency"] - lb["efficiency"]

    # ── Classification ──
    median_opps = lb["opportunities"].median()

    def classify(row):
        eff       = row["efficiency"]
        r_eff     = row["recent_efficiency"]
        opps      = row["opportunities"]
        is_over   = eff > 1.12
        is_under  = eff < 0.90
        is_hi_vol = opps >= max(median_opps * 0.60, 8)
        is_lo_vol = opps <= median_opps * 0.50
        declining = row["trend"] < -0.10

        if is_over and is_hi_vol:
            return "SELL HIGH" if declining else "ELITE"
        if is_under and is_hi_vol:
            return "BUY LOW"
        if is_over and is_lo_vol and eff > 1.20:
            return "BREAKOUT"
        return None

    lb["category"] = lb.apply(classify, axis=1)

    # Sanity filter
    lb = lb[lb["efficiency"].between(0.01, 15) & lb["actual_fp"].notna()]
    lb = lb.sort_values("actual_fp", ascending=False).reset_index(drop=True)

    # ── Combined weekly for callers ──
    weekly_combined = player_weekly_xfp.merge(player_weekly_actual, on=["player_id", "week"], how="inner")

    return lb, weekly_combined


# ─── CARD HTML ────────────────────────────────────────────────────────────────

def _card_html(player: pd.Series) -> str:
    name       = player["player_display_name"]
    pos        = player["position"]
    team       = player["recent_team"]
    headshot   = player.get("headshot_url", "") or ""
    actual_fp  = float(player["actual_fp"])
    expected_fp= float(player["expected_fp"])
    efficiency = float(player["efficiency"])
    over_under = float(player["over_under"])
    r_eff      = float(player.get("recent_efficiency", efficiency))
    trend_val  = float(player.get("trend", 0))
    opps       = int(player.get("opportunities", 0))
    games      = int(player.get("games_played", 1)) or 1
    cat        = player.get("category") or "other"

    cat_map = {
        "SELL HIGH": ("sell",  "SELL HIGH", "tag-sell"),
        "ELITE":     ("elite", "ELITE",     "tag-elite"),
        "BUY LOW":   ("buy",   "BUY LOW",   "tag-buy"),
        "BREAKOUT":  ("break", "BREAKOUT",  "tag-break"),
        "other":     ("other", "—",         ""),
    }
    card_cls, tag_text, tag_cls = cat_map.get(cat, cat_map["other"])

    # Efficiency color
    if efficiency > 1.12:
        eff_cls = "c-orange" if cat == "SELL HIGH" else "c-green" if cat == "BUY LOW" else "c-gold" if cat == "ELITE" else "c-violet"
    elif efficiency < 0.90:
        eff_cls = "c-red"
    else:
        eff_cls = "c-muted"

    ou_cls = "c-green" if over_under >= 0 else "c-red"

    if trend_val > 0.06:
        trend_icon, trend_cls = "↑", "c-green"
    elif trend_val < -0.06:
        trend_icon, trend_cls = "↓", "c-red"
    else:
        trend_icon, trend_cls = "→", "c-muted"

    bar_pct = min((actual_fp / max(expected_fp, 0.5)) * 100, 140)
    bar_cls = "fill-over" if actual_fp >= expected_fp else "fill-under"
    opps_per_g = f"{opps/games:.1f}"

    return f"""
<div class="player-card card-{card_cls}">
  <div class="card-top">
    <div class="headshot-wrap">
      <img class="headshot-img" src="{headshot}"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
           loading="lazy" />
      <div class="pos-badge">{pos}</div>
    </div>
    <div class="p-identity">
      <div class="p-name">{name}</div>
      <div class="p-team">{team}</div>
    </div>
    {'<div class="tag ' + tag_cls + '">' + tag_text + '</div>' if tag_cls else ''}
  </div>

  <div class="eff-row">
    <div class="eff-block">
      <span class="eff-lbl">Efficiency</span>
      <div class="eff-val {eff_cls}">{efficiency:.2f}x</div>
    </div>
    <div class="trend-block">
      <span class="trend-lbl">Recent</span>
      <div class="trend-val {trend_cls}">{trend_icon}&thinsp;{r_eff:.2f}x</div>
    </div>
    <div class="ou-block">
      <span class="ou-lbl">+/&minus;</span>
      <div class="ou-val {ou_cls}">{over_under:+.1f}</div>
    </div>
  </div>

  <div class="fp-bar-section">
    <div class="fp-bar-labels">
      <span>Actual&nbsp;<strong>{actual_fp:.1f}</strong></span>
      <span>xFP&nbsp;<strong>{expected_fp:.1f}</strong></span>
    </div>
    <div class="fp-bar-track">
      <div class="fp-fill {bar_cls}" style="width:{bar_pct:.0f}%"></div>
    </div>
  </div>

  <div class="card-footer">
    <div class="f-stat"><span class="f-lbl">Opps</span><span class="f-val">{opps}</span></div>
    <div class="f-stat"><span class="f-lbl">Games</span><span class="f-val">{games}</span></div>
    <div class="f-stat"><span class="f-lbl">Opps/G</span><span class="f-val">{opps_per_g}</span></div>
  </div>
</div>
"""


def render_cards(df: pd.DataFrame, n_cols: int = 3, max_cards: int = 21):
    if df.empty:
        st.markdown('<div class="empty-state">No players match the current filters.</div>', unsafe_allow_html=True)
        return
    df = df.head(max_cards)
    for i in range(0, len(df), n_cols):
        cols = st.columns(n_cols)
        for j, (_, row) in enumerate(df.iloc[i:i+n_cols].iterrows()):
            with cols[j]:
                st.markdown(_card_html(row), unsafe_allow_html=True)


# ─── SCATTER BOARD ────────────────────────────────────────────────────────────

def render_scatter(lb: pd.DataFrame):
    cat_style = {
        "SELL HIGH": (C_SELL,  "circle"),
        "ELITE":     (C_ELITE, "star"),
        "BUY LOW":   (C_BUY,   "circle"),
        "BREAKOUT":  (C_BREAK, "diamond"),
        None:        (C_OTHER, "circle"),
    }

    fig = go.Figure()

    median_opps = lb["opportunities"].median()
    fig.add_hline(y=1.0, line_dash="dot", line_color="rgba(255,255,255,0.18)", line_width=1)
    fig.add_vline(x=median_opps, line_dash="dot", line_color="rgba(255,255,255,0.18)", line_width=1)

    for cat, (color, symbol) in cat_style.items():
        sub = lb[lb["category"] == cat]
        if sub.empty:
            continue
        label = cat or "Other"
        marker_size = (sub["actual_fp"].clip(lower=5) / 4).clip(upper=22)
        fig.add_trace(go.Scatter(
            x=sub["opportunities"],
            y=sub["efficiency"],
            mode="markers+text",
            name=label,
            textposition="top center",
            marker=dict(size=marker_size, color=color, opacity=0.82,
                        line=dict(width=0), symbol=symbol),
            customdata=sub[["player_display_name", "actual_fp", "expected_fp",
                             "position", "recent_team", "over_under", "recent_efficiency"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b>  %{customdata[3]} · %{customdata[4]}<br>"
                "Efficiency: <b>%{y:.2f}x</b>  &nbsp;Recent: %{customdata[6]:.2f}x<br>"
                "Actual: %{customdata[1]:.1f} &nbsp;xFP: %{customdata[2]:.1f} &nbsp;+/-: %{customdata[5]:+.1f}<br>"
                "Opportunities: %{x}<extra></extra>"
            ),
        ))

    # Quadrant annotation helpers
    x_max = lb["opportunities"].quantile(0.97)
    y_min = max(lb["efficiency"].quantile(0.03), 0.3)
    y_max = lb["efficiency"].quantile(0.97)

    def quad_label(text, x, y, color):
        fig.add_annotation(text=text, x=x, y=y, xref="x", yref="y",
                           showarrow=False, font=dict(size=9, color=color),
                           opacity=0.4)

    quad_label("◀ LOW VOL · HIGH EFF<br>BREAKOUT",  median_opps * 0.25, y_max * 0.96, C_BREAK)
    quad_label("HIGH VOL · HIGH EFF ▶<br>ELITE / SELL HIGH", median_opps * 1.75, y_max * 0.96, C_ELITE)
    quad_label("◀ LOW VOL · LOW EFF<br>BENCH / STREAM",     median_opps * 0.25, y_min * 1.05, C_MUTED)
    quad_label("HIGH VOL · LOW EFF ▶<br>BUY LOW",           median_opps * 1.75, y_min * 1.05, C_BUY)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=C_BG_CARD,
        plot_bgcolor=C_BG_PAGE,
        font=dict(family="Arial", color=C_TEXT, size=11),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Opportunities (rush att + targets)",
                   gridcolor="rgba(255,255,255,0.05)", zeroline=False),
        yaxis=dict(title="Efficiency  (Actual FP / xFP)",
                   gridcolor="rgba(255,255,255,0.05)", zeroline=False,
                   tickformat=".2f"),
        margin=dict(l=10, r=10, t=20, b=90),
        height=520,
        hoverlabel=dict(bgcolor="#0F1629", bordercolor="#1A2540",
                        font=dict(color=C_TEXT, size=12)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── FULL TABLE ───────────────────────────────────────────────────────────────

def render_table(lb: pd.DataFrame):
    display_cols = {
        "player_display_name": "Player",
        "position":            "Pos",
        "recent_team":         "Team",
        "actual_fp":           "Actual FP",
        "expected_fp":         "xFP",
        "efficiency":          "Efficiency",
        "over_under":          "+/−",
        "opportunities":       "Opps",
        "games_played":        "G",
        "recent_efficiency":   "Recent Eff",
        "category":            "Tag",
    }
    tbl = lb[[c for c in display_cols if c in lb.columns]].rename(columns=display_cols)
    tbl["Efficiency"] = tbl["Efficiency"].round(3)
    tbl["Recent Eff"] = tbl["Recent Eff"].round(3)
    tbl["Actual FP"]  = tbl["Actual FP"].round(1)
    tbl["xFP"]        = tbl["xFP"].round(1)
    tbl["+/−"]        = tbl["+/−"].round(1)

    def color_row(row):
        cat = row.get("Tag", "")
        color_map = {
            "SELL HIGH": f"background-color: rgba(255,107,53,0.07)",
            "ELITE":     f"background-color: rgba(240,180,41,0.07)",
            "BUY LOW":   f"background-color: rgba(14,203,129,0.07)",
            "BREAKOUT":  f"background-color: rgba(155,109,255,0.08)",
        }
        style = color_map.get(cat, "")
        return [style] * len(row)

    styled = tbl.style.apply(color_row, axis=1)
    st.dataframe(styled, use_container_width=True, height=520, hide_index=True)


# ─── PAGE ─────────────────────────────────────────────────────────────────────

inject_css()

# ── State init ──
if PAGE_KEY not in st.session_state:
    st.session_state[PAGE_KEY] = {
        "selected_year":           2024,
        "selected_weeks":          (1, 17),
        "scoring_format":          "standard",
        "selected_positions":      ["WR", "RB", "TE"],
        "min_opportunities":       10,
    }
state = st.session_state[PAGE_KEY]

# ── Header ──
st.markdown("""
<div class="lb-header">
  <div class="lb-title">xFP LEADERBOARD</div>
  <div class="lb-sub">Expected Fantasy Points &nbsp;·&nbsp; Efficiency &amp; Opportunity Intelligence</div>
</div>
""", unsafe_allow_html=True)

# ── Filters ──
with st.container():
    fc = st.columns([1.2, 1.5, 1.2, 2.5, 1.2])
    with fc[0]:
        year = st.selectbox("Season", list(range(2024, 2014, -1)),
                            index=list(range(2024, 2014, -1)).index(state["selected_year"]),
                            key="lb_year")
    with fc[1]:
        weeks = st.slider("Week range", 1, 18, state["selected_weeks"], key="lb_weeks")
    with fc[2]:
        fmt = st.selectbox("Scoring", ["Standard", "PPR"],
                           index=0 if state["scoring_format"] == "standard" else 1,
                           key="lb_fmt")
    with fc[3]:
        positions = st.multiselect("Positions", ["QB", "RB", "WR", "TE"],
                                   default=state["selected_positions"], key="lb_pos")
    with fc[4]:
        min_opps = st.slider("Min opps", 1, 50, state["min_opportunities"], key="lb_min_opps")

# Update state
state.update({
    "selected_year":      year,
    "selected_weeks":     weeks,
    "scoring_format":     fmt.lower(),
    "selected_positions": positions,
    "min_opportunities":  min_opps,
})

# ── Load model ──
xfp_calc = load_xfp_model()
if xfp_calc is None:
    st.error("xFP model could not be loaded. Check that the model file exists.")
    st.stop()

# ── Compute ──
with st.spinner("Computing expected fantasy points for all players... (first load may take ~30s)"):
    lb_full, weekly_df = compute_leaderboard(
        xfp_calc,
        year,
        weeks[0],
        weeks[1],
        fmt.lower(),
        tuple(sorted(positions)),
    )

if lb_full.empty:
    st.warning("No data returned. Try a different year or wider week range.")
    st.stop()

# ── Apply min opps filter ──
lb = lb_full[lb_full["opportunities"] >= min_opps].copy()

# ── Summary bar ──
n_sell   = (lb["category"] == "SELL HIGH").sum()
n_elite  = (lb["category"] == "ELITE").sum()
n_buy    = (lb["category"] == "BUY LOW").sum()
n_break  = (lb["category"] == "BREAKOUT").sum()
avg_eff  = lb["efficiency"].mean()
top_over = lb.loc[lb["over_under"].idxmax(), "player_display_name"] if not lb.empty else "—"
top_under= lb.loc[lb["over_under"].idxmin(), "player_display_name"] if not lb.empty else "—"

st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi-cell">
    <div class="kpi-lbl">Avg Efficiency</div>
    <div class="kpi-val {'gold' if avg_eff > 1 else 'c-muted'}">{avg_eff:.2f}x</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Sell High</div>
    <div class="kpi-val orange">{n_sell}</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Elite</div>
    <div class="kpi-val gold">{n_elite}</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Buy Low</div>
    <div class="kpi-val green">{n_buy}</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Breakout</div>
    <div class="kpi-val violet">{n_break}</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Top Overperformer</div>
    <div style="font-size:0.8rem;font-weight:700;color:#E4EAF6;line-height:1.2">{top_over}</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-lbl">Top Underperformer</div>
    <div style="font-size:0.8rem;font-weight:700;color:#E4EAF6;line-height:1.2">{top_under}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──
tab_board, tab_sell, tab_buy, tab_break = st.tabs([
    "◈  FULL BOARD", "▲  SELL HIGH", "▼  BUY LOW", "◆  BREAKOUT WATCH"
])

# ── FULL BOARD ──
with tab_board:
    render_scatter(lb)
    st.markdown('<div class="section-head">All Players</div>', unsafe_allow_html=True)
    render_table(lb)

# ── SELL HIGH ──
with tab_sell:
    st.markdown("""
<div class="insight-box insight-sell">
  <strong>Sell High</strong> — These players have starter-level volume and are putting up good fantasy numbers,
  but are outpacing their expected output. The players tagged <em>Sell High</em> are also showing a recent
  efficiency decline (regression toward the mean has already started). <strong>Elite</strong> players share the
  same volume + overperformance profile but their recent efficiency is holding firm — they may just be
  genuinely great. Hold Elites; shop Sell Highs.
</div>
""", unsafe_allow_html=True)

    sell_df  = lb[lb["category"] == "SELL HIGH"].sort_values("efficiency", ascending=False)
    elite_df = lb[lb["category"] == "ELITE"].sort_values("actual_fp", ascending=False)

    if not sell_df.empty:
        st.markdown('<div class="section-head">⚠ Regression Risk — Consider Shopping</div>', unsafe_allow_html=True)
        render_cards(sell_df)

    if not elite_df.empty:
        st.markdown('<div class="section-head">★ Elite — Hold / Trust the Production</div>', unsafe_allow_html=True)
        render_cards(elite_df)

    if sell_df.empty and elite_df.empty:
        st.markdown('<div class="empty-state">No Sell High or Elite players with current filters.</div>',
                    unsafe_allow_html=True)

# ── BUY LOW ──
with tab_buy:
    st.markdown("""
<div class="insight-box insight-buy">
  <strong>Buy Low</strong> — These players have solid, consistent opportunity volume but are underperforming
  their expected output. If their workload holds, positive statistical regression is likely on its way.
  The best buy-low targets show a stable or improving trend — volume without results that haven't yet reflected
  in the box score. Acquire before the market corrects.
</div>
""", unsafe_allow_html=True)

    buy_df = lb[lb["category"] == "BUY LOW"].sort_values("efficiency", ascending=True)
    render_cards(buy_df)

# ── BREAKOUT WATCH ──
with tab_break:
    st.markdown("""
<div class="insight-box insight-break">
  <strong>Breakout Watch</strong> — Limited opportunities, outsized efficiency. These players are making the
  most of every touch — whether a new role, a rookie finding their footing, or a depth player getting a chance.
  Their raw numbers don't tell the full story yet. If the opportunity expands (injury, usage shift, game-plan
  change), the underlying efficiency suggests a big upside ceiling.
</div>
""", unsafe_allow_html=True)

    break_df = lb[lb["category"] == "BREAKOUT"].sort_values("efficiency", ascending=False)
    render_cards(break_df)
