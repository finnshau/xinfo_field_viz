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
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR      = PROJECT_ROOT / 'src'
DATA_PATH    = PROJECT_ROOT / 'data' / 'raw' / 'xinfo_catalog2025_similar_plays'

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from examples import map_offense_to_coordinates, map_defense_to_coordinates, plot_offense_v2, NFL_TEAM_COLORS

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
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner='Loading catalog…')
def load_catalog(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for col in ['week','down','distance','yd_from_goal','time_remaining',
                'period','home_score','away_score','men_in_box','play_unique_id','game_code',
                'xyards','xrush%','xovryds','xsack%','xscramble%','xtd%','xrushtd%']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
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
        st.image(png, width=400)
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

    st.markdown(f'<p style="color:#555577;font-size:0.7rem;margin-top:1rem;">Play ID: {pid} · Game Code: {gc} · Week {_safe_int(row.get("week"),0)} · {_clean(row.get("game_date"),"")}</p>',
                unsafe_allow_html=True)


if __name__ == '__main__':
    main()