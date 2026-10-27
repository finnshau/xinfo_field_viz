"""
xInfoViz — Pre-Snap Formation Browser
Run with:  streamlit run app.py
"""

import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR      = PROJECT_ROOT / 'src'
DATA_PATH    = PROJECT_ROOT / 'data' / 'raw' / 'xinfo_catalog2025_similar_plays.csv'

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from examples_plotly import map_offense_to_coordinates, map_defense_to_coordinates, plot_offense_v2, NFL_TEAM_COLORS

st.set_page_config(
    page_title='xInfoViz',
    page_icon='🏈',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0d0d1a; }
    [data-testid="stSidebar"] * { color: #e8e8f0 !important; }
    .stApp { background-color: #0f0f1a; }
    .stApp, .stApp * { color: #e8e8f0; }

    .scorebar {
        display: flex; align-items: center; justify-content: space-between;
        background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 10px;
        padding: 0.8rem 1.5rem; margin-bottom: 1rem;
    }
    .score-team { text-align: center; min-width: 120px; }
    .score-label { font-size: 0.65rem; color: #8888aa; text-transform: uppercase; letter-spacing: 0.1em; }
    .score-name { font-size: 1.4rem; font-weight: 900; color: #ffffff; letter-spacing: 1px; }
    .score-num { font-size: 2rem; font-weight: 900; color: #ffffff; }
    .score-mid { text-align: center; flex: 1; }
    .score-situation { background: #ff6b00; color: white; border-radius: 6px;
        padding: 0.3rem 1rem; font-size: 0.85rem; font-weight: 800;
        letter-spacing: 0.05em; display: inline-block; margin-bottom: 0.3rem; }
    .score-time { font-size: 1.1rem; font-weight: 700; color: #ffffff; }
    .score-qtr { font-size: 0.75rem; color: #aaaacc; }

    .pred-box {
        background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 10px;
        padding: 0.9rem 1.1rem; margin-bottom: 0.7rem;
    }
    .pred-label { font-size: 0.65rem; font-weight: 700; color: #ff6b00;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
    .pred-value { font-size: 1.8rem; font-weight: 900; color: #ffffff; line-height: 1; }
    .pred-sub { font-size: 0.7rem; color: #8888aa; margin-top: 0.2rem; }
    .pred-bar-bg { background: #2e2e4a; border-radius: 4px; height: 6px; margin-top: 0.5rem; }
    .pred-bar-fill { background: #ff6b00; border-radius: 4px; height: 6px; }

    /* Side info panel chips — stacked vertically */
    .info-panel { display: flex; flex-direction: column; gap: 0.5rem; }
    .chip {
        background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 6px;
        padding: 0.4rem 0.8rem;
    }
    .chip-label { font-size: 0.6rem; color: #7777aa; text-transform: uppercase;
        letter-spacing: 0.08em; margin-bottom: 0.1rem; }
    .chip-value { font-size: 0.9rem; font-weight: 700; color: #ffffff; }

    .roster-box {
        background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 10px;
        padding: 0.9rem 1.1rem;
    }
    .roster-title { font-size: 0.7rem; font-weight: 800; color: #ff6b00;
        text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.6rem; }
    .roster-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.2rem 1rem; }
    .roster-player { font-size: 0.75rem; color: #ccccdd; }
    .roster-player span { color: #ffffff; font-weight: 600; }

    .stDownloadButton > button { background-color: #ff6b00; color: white;
        border: none; border-radius: 8px; padding: 0.4rem 1.2rem;
        font-weight: 700; width: 100%; margin-top: 0.4rem; }
    .stDownloadButton > button:hover { background-color: #e05a00; }
    hr { border-color: #2e2e4a; margin: 0.8rem 0; }
    div[data-testid="stNumberInput"] input { background-color: #1a1a2e !important; color: #ffffff !important; }

    /* Similar plays section */
    .sim-box {
        background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 10px;
        padding: 1rem 1.2rem; margin-top: 0.5rem;
    }
    .sim-title { font-size: 0.7rem; font-weight: 800; color: #ff6b00;
        text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.2rem; }
    .sim-subtitle { font-size: 0.65rem; color: #7777aa; margin-bottom: 0.8rem; }
    .sim-table { width: 100%; border-collapse: collapse; }
    .sim-table th { font-size: 0.6rem; color: #7777aa; text-transform: uppercase;
        letter-spacing: 0.08em; padding: 0.3rem 0.6rem; text-align: left;
        border-bottom: 1px solid #2e2e4a; }
    .sim-table td { font-size: 0.82rem; padding: 0.35rem 0.6rem;
        border-bottom: 1px solid #1e1e3a; }
    .sim-table tr:last-child td { border-bottom: none; }
    .sim-this { color: #ffffff; font-weight: 700; }
    .sim-avg  { color: #aaaacc; }
    .sim-up   { color: #4caf80; }
    .sim-down { color: #e05a5a; }
    .sim-badge { display: inline-block; background: #2e2e4a; border-radius: 4px;
        padding: 0.1rem 0.5rem; font-size: 0.65rem; color: #aaaacc;
        margin-left: 0.4rem; vertical-align: middle; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner='Loading catalog…')
def load_catalog(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for col in ['week','down','distance','yd_from_goal','time_remaining',
                'period','home_score','away_score','men_in_box','play_unique_id','game_code',
                'xyards','xrush%','xovryds','xsack%','xscramble%','xtd%','xrushtd%']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Strip leading/trailing whitespace from all string columns
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())
    return df


def _safe_int(val, default=0):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except: pass
    try: return int(float(str(val)))
    except: return default


def _safe_float(val, default=0.0):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except: pass
    try: return float(val)
    except: return default


def _clean(val, default='—'):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except: pass
    s = str(val).strip()
    return s if s and s.lower() not in ('nan','none','') else default


def _fmt_time(seconds):
    try:
        if pd.isna(seconds): return '—'
    except: pass
    try:
        m, s = divmod(int(float(seconds)), 60)
        return f'{m}:{s:02d}'
    except: return '—'


def _team_color(nickname):
    return NFL_TEAM_COLORS.get(str(nickname).strip(), {}).get('primary', '#3a3a6a')


def _play_label(row) -> str:
    down_map = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}
    down = down_map.get(_safe_int(row.get('down'), 0), '?')
    dist = _safe_int(row.get('distance'), 0) or '?'
    yds  = _safe_int(row.get('yd_from_goal'), 0) or '?'
    form = _clean(row.get('offensive_formation'), '?')
    time = _fmt_time(row.get('time_remaining'))
    qtr  = f"Q{_safe_int(row.get('period'), 1)}"
    off  = _clean(row.get('offensive_team_nickname'), '')
    pid  = _safe_int(row.get('play_unique_id'), 0)
    return f"{pid}  |  {qtr} {time}  |  {down} & {dist}  |  {yds} yds  |  {off} — {form}"


@st.cache_data(show_spinner='Rendering…')
def render_play(play_id: int, game_code: int, _hash: str):
    cat = load_catalog(DATA_PATH)
    matches = cat[(cat['play_unique_id']==play_id) & (cat['game_code']==game_code)]
    if matches.empty:
        matches = cat[cat['play_unique_id']==play_id]
    if matches.empty:
        raise ValueError(f'No play found with ID {play_id} / game {game_code}.')
    row = matches.iloc[0]

    roles, nums, names = [], [], []
    for i in range(1, 12):
        r = row.get(f'off_{i}_role')
        if pd.notna(r) and str(r).strip() not in ('','nan'):
            roles.append(str(r).strip())
            nums.append(_safe_int(row.get(f'off_{i}_number'), 0))
            names.append(_clean(row.get(f'off_{i}_player_last_name'), ''))
    qb_pos = str(row.get('qb_pos','S') or 'S').strip().upper()[0]
    if qb_pos not in ('N','P','S'): qb_pos = 'S'
    df_off = map_offense_to_coordinates(roles, nums, names, qb_pos)

    d_roles, d_nums, d_names, d_press = [], [], [], []
    for i in range(1, 12):
        r = row.get(f'def_{i}_role')
        if pd.notna(r) and str(r).strip() not in ('','nan'):
            d_roles.append(str(r).strip())
            d_nums.append(_safe_int(row.get(f'def_{i}_number'), 0))
            d_names.append(_clean(row.get(f'def_{i}_player_last_name'), ''))
            d_press.append(_safe_int(row.get(f'def_{i}_press'), 0))
    df_def = map_defense_to_coordinates(d_roles, d_nums, d_names, d_press, df_off)

    off_team = _clean(row.get('offensive_team_nickname'), '')
    def_team = _clean(row.get('defensive_team_nickname'), '')
    yd = row.get('yd_from_goal')

    # Determine field side and attacking direction from yd_from_goal.
    # yd_from_goal > 50  -> offense is in its own half and attacks right.
    # yd_from_goal <= 50 -> offense is in opponent territory and attacks left.
    if pd.notna(yd):
        yd_from_goal = int(float(yd))
        if yd_from_goal > 50:
            yard_line = 100 - yd_from_goal
            attacking_right = True
        else:
            yard_line = yd_from_goal
            attacking_right = False
    else:
        yard_line = 50
        attacking_right = True

    fig, _ = plot_offense_v2(
        df_coords=df_off, df_def_coords=df_def,
        title='',
        yard_line=yard_line,
        attacking_right=attacking_right,
        off_team=off_team, def_team=def_team,
    )
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read(), row, df_off, df_def


def build_plotly_field(df_off, df_def, yard_line, attacking_right, off_team, def_team):
    """
    Replicate the plot_offense_v2 field in Plotly with hover tooltips.
    All visual parameters mirror plot_offense_v2 exactly — only hover is new.
    """
    SCALE = 1.0
    PLAYER_S  = 650  * SCALE**2
    LW_CIRCLE = 1.8  * SCALE
    LW_PRESS  = 2.5  * SCALE

    _DEFAULT_OFF = {'primary': '#f0b54a', 'secondary': '#1a1a1a'}
    _DEFAULT_DEF = {'primary': '#c8102e', 'secondary': '#ffffff'}

    def _team_colors(nickname, default):
        if not nickname:
            return default
        return NFL_TEAM_COLORS.get(str(nickname).strip(), default)

    off_colors = _team_colors(off_team, _DEFAULT_OFF)
    def_colors = _team_colors(def_team, _DEFAULT_DEF)
    C_BG       = '#0d0d1a'
    C_FIELD_A  = '#2a6622'
    C_FIELD_B  = '#256020'
    C_OFF_FILL = off_colors['primary']
    C_OFF_TEXT = off_colors['secondary']
    C_DEF_FILL = def_colors['primary']
    C_DEF_TEXT = def_colors['secondary']

    x_min, x_max = -23.0, 23.0
    y_min, y_max =   0.0, 53.3

    def _to_plot(x_ft, y_ft):
        px = x_ft / 3
        py = y_ft / 3
        if not attacking_right:
            px = -px
            py = 53.3 - py
        return px, py

    def _fmt_num(val):
        try:
            if val is None: return '?'
            s = str(val).strip()
            if s in ('?', '', 'nan', 'None'): return '?'
            return str(int(float(s)))
        except:
            return '?'

    fig = go.Figure()

    # Grass stripes
    for idx, sx in enumerate(range(int(x_min), int(x_max), 5)):
        left  = max(float(sx),     x_min)
        right = min(float(sx + 5), x_max)
        if left < right:
            color = C_FIELD_A if idx % 2 == 0 else C_FIELD_B
            fig.add_shape(type='rect', x0=left, x1=right, y0=y_min, y1=y_max,
                          fillcolor=color, line_width=0, layer='below')

    # Sidelines
    fig.add_shape(type='line', x0=x_min, x1=x_max, y0=y_min, y1=y_min,
                  line=dict(color='white', width=2.5))
    fig.add_shape(type='line', x0=x_min, x1=x_max, y0=y_max, y1=y_max,
                  line=dict(color='white', width=2.5))

    # Per-yard tick marks
    TICK_H = 0.5 * SCALE
    for yd in range(int(x_min), int(x_max) + 1):
        fig.add_shape(type='line', x0=yd, x1=yd, y0=y_min, y1=y_min + TICK_H,
                      line=dict(color='white', width=0.7), opacity=0.5)
        fig.add_shape(type='line', x0=yd, x1=yd, y0=y_max - TICK_H, y1=y_max,
                      line=dict(color='white', width=0.7), opacity=0.5)

    # 10-yard markers + numbers
    for marker in range(0, 101, 10):
        yard_x = float(marker - yard_line)
        if x_min <= yard_x <= x_max and yard_x != 0:
            fig.add_shape(type='line', x0=yard_x, x1=yard_x, y0=y_min, y1=y_max,
                          line=dict(color='white', width=1.0), opacity=0.3)
            label_val = marker if marker <= 50 else (100 - marker)
            for txt_y, anchor, rotate in [(y_min + 1.6, 'bottom', 0), (y_max - 1.6, 'top', 180)]:
                fig.add_annotation(x=yard_x, y=txt_y, text=str(int(label_val)),
                       showarrow=False,
                       font=dict(color='white', size=44*SCALE, family='Arial Black'),
                       opacity=0.18, yanchor=anchor, xanchor='center',
                       textangle=rotate)
    # Hash marks
    HASH_W = 0.15 * SCALE
    for hash_y in (17.4, 35.9):
        for hx in range(int(x_min) - 1, int(x_max) + 2):
            fig.add_shape(type='line', x0=hx - HASH_W, x1=hx + HASH_W,
                          y0=hash_y, y1=hash_y,
                          line=dict(color='white', width=1.0), opacity=0.6)

    # Conditional end zone
    def _primary(team):
        return NFL_TEAM_COLORS.get(str(team).strip(), {}).get('primary', '#1a4a1a')

    _yds_to_goal = 100 - yard_line
    if _yds_to_goal <= 20:
        _goal_x = float(_yds_to_goal)
        fig.add_shape(type='rect', x0=_goal_x, x1=x_max, y0=y_min, y1=y_max,
                      fillcolor=_primary(def_team), opacity=0.55, line_width=0, layer='below')
        fig.add_shape(type='line', x0=_goal_x, x1=_goal_x, y0=y_min, y1=y_max,
                      line=dict(color='white', width=2.5))
    elif _yds_to_goal >= 80:
        _goal_x = float(_yds_to_goal - 100)
        fig.add_shape(type='rect', x0=x_min, x1=_goal_x, y0=y_min, y1=y_max,
                      fillcolor=_primary(off_team), opacity=0.55, line_width=0, layer='below')
        fig.add_shape(type='line', x0=_goal_x, x1=_goal_x, y0=y_min, y1=y_max,
                      line=dict(color='white', width=2.5))

    # LOS
    fig.add_shape(type='line', x0=0, x1=0, y0=y_min, y1=y_max,
                  line=dict(color='white', width=2.8))
    fig.add_annotation(x=0.25, y=y_max - 0.8, text='LOS', showarrow=False,
                       font=dict(color='white', size=7*SCALE), opacity=0.6,
                       xanchor='left', yanchor='top')

    MARKER_SIZE = 16  # approximate match for s=650 in matplotlib
    LABEL_OFFSET = 1.2   # base vertical offset for role labels
    CROWD_RADIUS = 1.5   # distance threshold to consider players "crowded"

    def _smart_label_offset(px, py, all_positions):
        """
        Pick the least-crowded direction for a role label.
        Tries above, below, left, right and returns (dx, dy, xanchor, yanchor).
        """
        candidates = [
            (0,  LABEL_OFFSET, 'center', 'bottom'),   # above
            (0, -LABEL_OFFSET, 'center', 'top'),       # below
            ( LABEL_OFFSET, 0, 'left',   'middle'),    # right
            (-LABEL_OFFSET, 0, 'right',  'middle'),    # left
        ]
        best = candidates[0]
        best_min_dist = -1
        for dx, dy, xa, ya in candidates:
            tx, ty = px + dx, py + dy
            dists = [((tx - ox)**2 + (ty - oy)**2)**0.5
                     for ox, oy in all_positions if not (ox == px and oy == py)]
            min_d = min(dists) if dists else 999
            if min_d > best_min_dist:
                best_min_dist = min_d
                best = (dx, dy, xa, ya)
        return best

    # Pre-collect all player positions for crowding checks
    all_positions = []
    for _, p in df_off.iterrows():
        all_positions.append(_to_plot(p['x_ft'], p['y_ft']))
    if df_def is not None and not df_def.empty:
        for _, p in df_def.iterrows():
            all_positions.append(_to_plot(p['x_ft'], p['y_ft']))

    # Draw offense
    for _, p in df_off.iterrows():
        px, py = _to_plot(p['x_ft'], p['y_ft'])
        num  = _fmt_num(p.get('player_number'))
        name = str(p.get('player_name', '')).strip()
        role = str(p.get('role', '')).strip()
        hover = f"<b>#{num} {name}</b><br>Role: {role}<br>Side: Offense<extra></extra>"
        fig.add_trace(go.Scatter(
            x=[px], y=[py], mode='markers',
            marker=dict(size=MARKER_SIZE, color=C_OFF_FILL,
                        line=dict(color='white', width=LW_CIRCLE)),
            hovertemplate=hover, showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[px], y=[py], mode='text',
            text=[num], textfont=dict(color=C_OFF_TEXT, size=10*SCALE, family='Arial Black'),
            hovertemplate=hover, showlegend=False,
        ))
        dx, dy, xa, ya = _smart_label_offset(px, py, all_positions)
        fig.add_annotation(x=px + dx, y=py + dy, text=role, showarrow=False,
                           font=dict(color='#f5f5f5', size=8*SCALE, family='Arial Black'),
                           xanchor=xa, yanchor=ya)

    # Draw defense
    if df_def is not None and not df_def.empty:
        for _, p in df_def.iterrows():
            px, py = _to_plot(p['x_ft'], p['y_ft'])
            num   = _fmt_num(p.get('player_number'))
            name  = str(p.get('player_name', '')).strip()
            role  = str(p.get('role', '')).strip()
            press = int(p.get('press', 0)) if not pd.isna(p.get('press', 0)) else 0
            hover = (
                f"<b>#{num} {name}</b><br>Role: {role}<br>Side: Defense"
                + ("<br><b>PRESS</b>" if press == 1 else "")
                + "<extra></extra>"
            )
            if press == 1:
                fig.add_trace(go.Scatter(
                    x=[px], y=[py], mode='markers',
                    marker=dict(size=MARKER_SIZE * 1.65, color='rgba(0,0,0,0)',
                                line=dict(color='#ffdd00', width=LW_PRESS)),
                    hoverinfo='skip', showlegend=False,
                ))
            fig.add_trace(go.Scatter(
                x=[px], y=[py], mode='markers',
                marker=dict(size=MARKER_SIZE, color=C_DEF_FILL,
                            line=dict(color='white', width=LW_CIRCLE)),
                hovertemplate=hover, showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=[px], y=[py], mode='text',
                text=[num], textfont=dict(color=C_DEF_TEXT, size=10*SCALE, family='Arial Black'),
                hovertemplate=hover, showlegend=False,
            ))
            dx, dy, xa, ya = _smart_label_offset(px, py, all_positions)
            fig.add_annotation(x=px + dx, y=py + dy, text=role, showarrow=False,
                               font=dict(color='#f5f5f5', size=8*SCALE, family='Arial Black'),
                               xanchor=xa, yanchor=ya)

    fig.update_layout(
        paper_bgcolor=C_BG,
        plot_bgcolor=C_FIELD_A,
        xaxis=dict(range=[x_min, x_max], showticklabels=False, showgrid=False,
                   zeroline=False, fixedrange=True, constrain='domain'),
        yaxis=dict(range=[y_min, y_max], showticklabels=False, showgrid=False,
                   zeroline=False, scaleanchor='x', scaleratio=1, fixedrange=True,
                   constrain='domain'),
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
        hoverlabel=dict(
            bgcolor='#1a1a2e',
            bordercolor='#ff6b00',
            font=dict(color='white', size=13, family='Arial'),
        ),
        dragmode=False,
        autosize=True,
    )
    return fig


def _field_zone(yd_from_goal):
    """Bucket yd_from_goal into four field zones based on yards to opponent end zone."""
    try:
        y = int(float(yd_from_goal))
    except:
        return None
    if y <= 20:  return 'Red Zone'
    if y <= 50:  return "Opp. Side"
    if y <= 80:  return 'Own Side'
    return 'Backed Up'


def get_similar_plays(cat, row, dist_tolerance=1):
    """
    Return a DataFrame of similar plays based on:
      - same offensive_formation
      - same offensive_personnel (if available)
      - same down
      - distance within ±dist_tolerance
      - same field zone (bucketed from yd_from_goal)
    Falls back to ±2 yards if fewer than 10 matches found.
    Excludes the current play itself.
    """
    formation  = str(row.get('offensive_formation', '') or '').strip()
    personnel  = str(row.get('offensive_personnel', '') or '').strip()
    down       = _safe_int(row.get('down'), 0)
    distance   = _safe_int(row.get('distance'), 0)
    zone       = _field_zone(row.get('yd_from_goal'))
    pid        = _safe_int(row.get('play_unique_id'), 0)

    if not formation or formation in ('nan', 'None', '—') or not down or not zone:
        return pd.DataFrame()

    # clean personnel — only use if it's a real value
    use_personnel = (
        personnel and
        personnel not in ('nan', 'None', '—', '') and
        not pd.isna(row.get('offensive_personnel', float('nan')))
        if hasattr(pd, 'isna') else True
    )

    def _filter(tol):
        mask = (
            (cat['offensive_formation'] == formation) &
            (cat['down'] == float(down)) &
            (cat['distance'] >= distance - tol) &
            (cat['distance'] <= distance + tol) &
            (cat['play_unique_id'] != pid)
        )
        if use_personnel:
            mask &= (cat['offensive_personnel'] == personnel)
        sub = cat[mask].copy()
        sub['_zone'] = sub['yd_from_goal'].apply(_field_zone)
        return sub[sub['_zone'] == zone]

    result = _filter(dist_tolerance)
    if len(result) < 10:
        result = _filter(dist_tolerance + 1)
    # if still too few, relax personnel constraint
    if len(result) < 5 and use_personnel:
        def _filter_no_personnel(tol):
            mask = (
                (cat['offensive_formation'] == formation) &
                (cat['down'] == float(down)) &
                (cat['distance'] >= distance - tol) &
                (cat['distance'] <= distance + tol) &
                (cat['play_unique_id'] != pid)
            )
            sub = cat[mask].copy()
            sub['_zone'] = sub['yd_from_goal'].apply(_field_zone)
            return sub[sub['_zone'] == zone]
        result = _filter_no_personnel(dist_tolerance + 1)
    return result


def _sim_row_html(label, this_val, avg_val, fmt_this, fmt_avg, higher_is_better=True):
    """Render one comparison row with color coding."""
    try:
        diff = this_val - avg_val
        if abs(diff) < 0.001:
            cls = 'sim-avg'
            arrow = ''
        elif (diff > 0) == higher_is_better:
            cls = 'sim-up'
            arrow = ' ▲'
        else:
            cls = 'sim-down'
            arrow = ' ▼'
    except:
        cls = 'sim-avg'
        arrow = ''
    return f"""
        <tr>
            <td style="color:#aaaacc">{label}</td>
            <td class="sim-this">{fmt_this}</td>
            <td class="{cls}">{fmt_avg}{arrow}</td>
        </tr>"""


def main():
    cat = load_catalog(DATA_PATH)

    with st.sidebar:
        st.markdown('### 🏈 xInfoViz')
        st.markdown('<p style="color:#8888aa;font-size:0.8rem;">2025 NFL Season</p>', unsafe_allow_html=True)
        search_mode = st.radio('Search method', ['Browse by game', 'Direct Play ID search'],
                               label_visibility='collapsed')
        st.markdown('---')
        pid_input, gc_input = None, None

        if search_mode == 'Browse by game':
            weeks = sorted(cat['week'].dropna().unique().astype(int).tolist())
            playoff_map = {19:'Wild Card', 20:'Divisional', 21:'Conference', 23:'Super Bowl'}
            selected_week = st.selectbox('Week', options=weeks,
                format_func=lambda w: f"Week {w} — {playoff_map[w]}" if w in playoff_map else f"Week {w}")
            week_games = cat[cat['week']==selected_week].copy()
            game_opts = (week_games[['game_code','game_date','home_team_nickname','away_team_nickname']]
                         .drop_duplicates('game_code').sort_values('game_date'))
            game_map = {int(r['game_code']): f"{r['away_team_nickname']}  @  {r['home_team_nickname']}  ({r['game_date']})"
                        for _, r in game_opts.iterrows()}
            selected_game = st.selectbox('Game', options=list(game_map.keys()),
                                         format_func=lambda g: game_map[g])
            game_rows = week_games[week_games['game_code']==selected_game].copy()
            teams = sorted(game_rows['offensive_team_nickname'].dropna().unique().tolist())
            selected_team = st.selectbox('Offensive team', options=['Both teams'] + teams)
            formations = sorted(game_rows['offensive_formation'].dropna().unique().tolist())
            selected_formation = st.selectbox('Formation', options=['All formations'] + formations)
            downs_raw = sorted(game_rows['down'].dropna().unique().astype(int).tolist())
            down_labels = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}
            selected_down = st.selectbox('Down', options=['Any down'] + downs_raw,
                format_func=lambda d: down_labels.get(d, str(d)) if d != 'Any down' else 'Any down')
            filtered = game_rows.copy()
            if selected_team != 'Both teams':
                filtered = filtered[filtered['offensive_team_nickname']==selected_team]
            if selected_formation != 'All formations':
                filtered = filtered[filtered['offensive_formation']==selected_formation]
            if selected_down != 'Any down':
                filtered = filtered[filtered['down']==float(selected_down)]
            filtered = filtered.sort_values(['period','time_remaining'], ascending=[True,False])
            if filtered.empty:
                st.warning('No plays match filters.')
                return
            play_map = {int(r['play_unique_id']): _play_label(r) for _, r in filtered.iterrows()}
            selected_pid = st.selectbox(f'{len(filtered):,} plays', options=list(play_map.keys()),
                                        format_func=lambda p: play_map[p])
            pid_input = selected_pid
            gc_input  = selected_game
        else:
            pid_input = st.number_input('Play ID', min_value=0, value=2639200, step=1, format='%d')
            gc_input  = st.number_input('Game Code', min_value=0, value=2879291, step=1, format='%d')

        st.markdown('---')
        st.caption('Direction is set automatically from yd_from_goal.')
        render_btn = st.button('Render ▶', use_container_width=True)

    if render_btn or 'rendered_pid' not in st.session_state:
        st.session_state['rendered_pid'] = int(pid_input)
        st.session_state['rendered_gc']  = int(gc_input)

    pid = st.session_state['rendered_pid']
    gc  = st.session_state['rendered_gc']

    with st.spinner('Rendering…'):
        try:
            png, row, df_off, df_def = render_play(
                play_id=pid,
                game_code=gc,
                _hash=str(DATA_PATH.stat().st_mtime),
            )
        except Exception as e:
            st.error(f'Could not render play: {e}')
            return

    # ── Recompute yard_line / attacking_right for Plotly (mirrors render_play logic) ──
    _yd = row.get('yd_from_goal')
    if pd.notna(_yd):
        _yd_from_goal = int(float(_yd))
        if _yd_from_goal > 50:
            yard_line = 100 - _yd_from_goal
            attacking_right = True
        else:
            yard_line = _yd_from_goal
            attacking_right = False
    else:
        yard_line = 50
        attacking_right = True

    # ── Extract values ────────────────────────────────────────────────────────
    off   = _clean(row.get('offensive_team_nickname'), '—')
    deff  = _clean(row.get('defensive_team_nickname'), '—')
    down_map = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}
    down  = down_map.get(_safe_int(row.get('down'), 0), '—')
    dist  = _safe_int(row.get('distance'), 0)
    yds   = _safe_int(row.get('yd_from_goal'), 0)
    qtr   = f"Q{_safe_int(row.get('period'), 1)}"
    time  = _fmt_time(row.get('time_remaining'))
    home_s = _safe_int(row.get('home_score'), 0)
    away_s = _safe_int(row.get('away_score'), 0)
    home_n = _clean(row.get('home_team_nickname'), '—')
    away_n = _clean(row.get('away_team_nickname'), '—')
    form   = _clean(row.get('offensive_formation'), '—')
    front  = _clean(row.get('defensive_front'), '—')
    off_p  = _clean(row.get('offensive_personnel'), '—')
    def_p  = _clean(row.get('defensive_personnel'), '—')
    box    = _clean(row.get('men_in_box'), '—')
    blitz  = 'Yes' if _clean(row.get('blitz'), 'F') == 'T' else 'No'
    motion = 'Yes' if _clean(row.get('is_motion'), 'F') == 'T' else 'No'
    pa     = 'Yes' if _clean(row.get('play_action'), 'N') == 'Y' else 'No'
    hash_  = _clean(row.get('snap_hash'), '—')
    xrush  = _safe_float(row.get('xrush%'), 0.0)
    xovr   = _safe_float(row.get('xovryds'), 0.0)
    xtd    = _safe_float(row.get('xtd%'), 0.0)
    xsack  = _safe_float(row.get('xsack%'), 0.0)
    xscram = _safe_float(row.get('xscramble%'), 0.0)
    xyds   = _safe_float(row.get('xyards'), 0.0)
    off_color = _team_color(off)
    def_color = _team_color(deff)

    # ── Scorebar ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="scorebar">
        <div class="score-team">
            <div class="score-label">AWAY</div>
            <div class="score-name" style="color:{_team_color(away_n)}">{away_n.upper()}</div>
            <div class="score-num">{away_s}</div>
        </div>
        <div class="score-mid">
            <div class="score-situation">{down} &amp; {dist} · BALL ON {yds} YDS</div>
            <br>
            <div class="score-time">{time}</div>
            <div class="score-qtr">{qtr}</div>
        </div>
        <div class="score-team">
            <div class="score-label">HOME</div>
            <div class="score-name" style="color:{_team_color(home_n)}">{home_n.upper()}</div>
            <div class="score-num">{home_s}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main layout: predictors | field | info chips ──────────────────────────
    col_pred, col_field, col_info = st.columns([1, 2, 1])

    with col_pred:
        rush_pct = int(xrush * 100)
        st.markdown(f"""
        <div class="pred-box">
            <div class="pred-label">Run/Pass Predictor</div>
            <div class="pred-value">{rush_pct}%</div>
            <div class="pred-sub">{'RUSH EXPECTED' if xrush > 0.5 else 'PASS EXPECTED'}</div>
            <div class="pred-bar-bg">
                <div class="pred-bar-fill" style="width:{rush_pct}%"></div>
            </div>
        </div>
        <div class="pred-box">
            <div class="pred-label">Expected Output</div>
            <div class="pred-value">{xovr:.1f}</div>
            <div class="pred-sub">OVERALL YDS &nbsp;·&nbsp; {xyds:.1f} xYDS</div>
        </div>
        <div class="pred-box">
            <div class="pred-label">TD Probability</div>
            <div class="pred-value">{xtd*100:.2f}%</div>
        </div>
        <div class="pred-box">
            <div class="pred-label">Sack %</div>
            <div class="pred-value">{xsack*100:.1f}%</div>
            <div class="pred-sub">SCRAMBLE {xscram*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col_field:
        plotly_fig = build_plotly_field(
            df_off=df_off, df_def=df_def,
            yard_line=yard_line,
            attacking_right=attacking_right,
            off_team=off,
            def_team=deff,
        )
        st.plotly_chart(plotly_fig, use_container_width=True, config={'displayModeBar': False})
        dn   = down_map.get(_safe_int(row.get('down'), 0), 'X')
        fname = f"xInfoViz_{off}_vs_{deff}_{qtr}_{time.replace(':','m')}s_{dn}_and_{dist}.png".replace(' ','_')
        st.download_button('⬇  Download PNG', data=png, file_name=fname, mime='image/png')

    with col_info:
        st.markdown(f"""
        <div class="info-panel">
            <div class="chip"><div class="chip-label">Off. Formation</div><div class="chip-value">{form}</div></div>
            <div class="chip"><div class="chip-label">Def. Front</div><div class="chip-value">{front}</div></div>
            <div class="chip"><div class="chip-label">Off. Personnel</div><div class="chip-value">{off_p}</div></div>
            <div class="chip"><div class="chip-label">Def. Personnel</div><div class="chip-value">{def_p}</div></div>
            <div class="chip"><div class="chip-label">Men in Box</div><div class="chip-value">{box}</div></div>
            <div class="chip"><div class="chip-label">Blitz</div><div class="chip-value">{blitz}</div></div>
            <div class="chip"><div class="chip-label">Motion</div><div class="chip-value">{motion}</div></div>
            <div class="chip"><div class="chip-label">Play Action</div><div class="chip-value">{pa}</div></div>
            <div class="chip"><div class="chip-label">Snap Hash</div><div class="chip-value">{hash_}</div></div>
            <div class="chip"><div class="chip-label">QB Position</div><div class="chip-value">{_clean(row.get('qb_pos'),'—')}</div></div>
        </div>
        """, unsafe_allow_html=True)

    # ── Personnel rosters ─────────────────────────────────────────────────────
    st.markdown('---')
    col_off_roster, col_def_roster = st.columns(2)

    def _roster_html(df, title, color):
        rows_html = ''
        for _, p in df.iterrows():
            num  = p.get('player_number', '')
            name = p.get('player_name', '')
            role = p.get('role', '')
            try:
                num = int(float(str(num))) if str(num) not in ('?','','nan') else '?'
            except: num = '?'
            rows_html += f'<div class="roster-player"><span>#{num} {name}</span> · {role}</div>'
        return f"""
        <div class="roster-box">
            <div class="roster-title" style="color:{color}">{title} PERSONNEL</div>
            <div class="roster-grid">{rows_html}</div>
        </div>"""

    with col_off_roster:
        st.markdown(_roster_html(df_off, off, off_color), unsafe_allow_html=True)

    with col_def_roster:
        st.markdown(_roster_html(df_def, deff, def_color), unsafe_allow_html=True)

    # ── Similar Plays ─────────────────────────────────────────────────────────
    st.markdown('---')
    sim_df  = get_similar_plays(cat, row)
    n_sim   = len(sim_df)
    zone_label = _field_zone(row.get('yd_from_goal')) or '—'
    dist_label = f"{dist} yd" + ("s" if dist != 1 else "")
    down_label = down
    fallback_note = ' <span class="sim-badge">±2 yd tolerance</span>' if n_sim >= 10 and _safe_int(row.get('distance'),0) else ''

    if n_sim == 0:
        st.markdown(f"""
        <div class="sim-box">
            <div class="sim-title">Similar Play Tendencies</div>
            <div class="sim-subtitle" style="color:#e05a5a">
                No similar plays found for {form} · {off_p} · {down_label} &amp; {dist_label} · {zone_label}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        import math

        def _fmt_pct(v):
            return f"{v*100:.1f}%" if not (isinstance(v, float) and math.isnan(v)) else '—'
        def _fmt_yds(v):
            return f"{v:.1f}" if not (isinstance(v, float) and math.isnan(v)) else '—'
        def _yn(val):
            """Convert T/F/1/0/True/False to Yes or No."""
            return 'Yes' if str(val).strip() in ('T','True','true','1','1.0') else 'No'
        def _pct_col(col):
            if col not in sim_df.columns: return float('nan')
            return sim_df[col].apply(lambda v: 1 if str(v).strip() in ('True','1','T','true','1.0') else 0).mean()

        # Pre-snap model averages
        avg_rush  = sim_df['xrush%'].mean()   if 'xrush%'   in sim_df.columns else float('nan')
        avg_yds   = sim_df['xyards'].mean()   if 'xyards'   in sim_df.columns else float('nan')
        avg_td    = sim_df['xtd%'].mean()     if 'xtd%'     in sim_df.columns else float('nan')
        avg_sack  = sim_df['xsack%'].mean()   if 'xsack%'   in sim_df.columns else float('nan')
        avg_ovr   = sim_df['xovryds'].mean()  if 'xovryds'  in sim_df.columns else float('nan')
        avg_scram = sim_df['xscramble%'].mean() if 'xscramble%' in sim_df.columns else float('nan')

        # Actual outcomes
        actual_avg_yds    = sim_df['yd_gained'].mean()    if 'yd_gained'    in sim_df.columns else float('nan')
        actual_td_rate    = _pct_col('is_td')
        actual_first_down = _pct_col('is_first_down')
        actual_success    = sim_df['success_play'].mean() if 'success_play' in sim_df.columns else float('nan')
        actual_explosive  = _pct_col('explosive')

        # This play actual values
        this_play_type  = _clean(row.get('play_type'), '—')
        this_yd_gained  = _safe_float(row.get('yd_gained'),  float('nan'))
        this_is_td      = _yn(row.get('is_td', 'F'))
        this_first_down = _yn(row.get('is_first_down', 'F'))
        this_success    = _yn(row.get('success_play', 0))
        this_explosive  = _yn(row.get('explosive', 0))

        # Pre-snap model rows
        pressnap_rows = (
            _sim_row_html('xRush %',   xrush, avg_rush, f"{xrush*100:.1f}%", _fmt_pct(avg_rush), higher_is_better=False) +
            _sim_row_html('xYards',    xyds,  avg_yds,  f"{xyds:.1f}",       _fmt_yds(avg_yds),  higher_is_better=True)  +
            _sim_row_html('xTD %',     xtd,   avg_td,   f"{xtd*100:.2f}%",   _fmt_pct(avg_td),   higher_is_better=True)  +
            _sim_row_html('xSack %',   xsack, avg_sack, f"{xsack*100:.1f}%", _fmt_pct(avg_sack), higher_is_better=False)
        )

        # Actual outcome rows — binary fields show Yes/No for this play, % for similar avg
        # Play Type has no similar avg comparison
        play_type_row = f"""
            <tr>
                <td style="color:#aaaacc">Play Type</td>
                <td class="sim-this">{this_play_type}</td>
                <td style="color:#aaaacc">—</td>
            </tr>"""

        outcome_rows = (
            play_type_row +
            _sim_row_html('Yards Gained', this_yd_gained,  actual_avg_yds,    _fmt_yds(this_yd_gained), _fmt_yds(actual_avg_yds),   higher_is_better=True) +
            _sim_row_html('Touchdown',    1 if this_is_td=='Yes' else 0, actual_td_rate,    this_is_td,       _fmt_pct(actual_td_rate),   higher_is_better=True) +
            _sim_row_html('1st Down',     1 if this_first_down=='Yes' else 0, actual_first_down, this_first_down,  _fmt_pct(actual_first_down),higher_is_better=True) +
            _sim_row_html('Success',      1 if this_success=='Yes' else 0, actual_success,    this_success,     _fmt_pct(actual_success),   higher_is_better=True) +
            _sim_row_html('Explosive',    1 if this_explosive=='Yes' else 0, actual_explosive,  this_explosive,   _fmt_pct(actual_explosive), higher_is_better=True)
        )

        pre_header = '<tr><td colspan="3" style="color:#ff6b00;font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;padding-top:0.6rem;border:none">Pre-Snap Model</td></tr>'
        act_header = '<tr><td colspan="3" style="color:#ff6b00;font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;padding-top:0.8rem;border:none">Actual Outcomes</td></tr>'

        rows_html = pre_header + pressnap_rows + act_header + outcome_rows

        st.markdown(f"""
        <div class="sim-box">
            <div class="sim-title">Similar Play Tendencies{fallback_note}</div>
            <div class="sim-subtitle">
                {form} · {off_p} · {down_label} &amp; {dist_label} · {zone_label}
                &nbsp;·&nbsp; <b style="color:#ffffff">{n_sim:,} similar plays</b>
            </div>
            <table class="sim-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>This Play</th>
                        <th>Similar Avg</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>""", unsafe_allow_html=True)

    st.markdown(f'<p style="color:#555577;font-size:0.7rem;margin-top:1rem;">Play ID: {pid} · Game Code: {gc} · Week {_safe_int(row.get("week"),0)} · {_clean(row.get("game_date"),"")}</p>',
                unsafe_allow_html=True)


if __name__ == '__main__':
    main()