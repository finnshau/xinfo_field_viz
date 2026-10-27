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
DATA_PATH     = PROJECT_ROOT / 'data' / 'raw' / 'xinfo_catalog2026_10_19.parquet'
DATA_PATH_OLD = PROJECT_ROOT / 'data' / 'raw' / '2026NFLEventsXI.20261019.xlsx'

# X-stat columns present in the weekly file (lowercase, matching catalog names)
_XSTAT_COLS = ['xyards', 'xrush%', 'xovryds', 'xsack%', 'xscramble%', 'xtd%', 'xrushtd%']

# Add both the project root and src/ to the path so xinfoviz_preview_field
# can be found whether it lives next to the app or inside src/.
for _p in (str(PROJECT_ROOT), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from xinfoviz_preview_field import map_offense_to_coordinates, map_defense_to_coordinates, plot_offense_v2, NFL_TEAM_COLORS

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

    .season-widget { background: #1a1a2e; border: 1px solid #2e2e4a; border-radius: 8px;
        padding: 0.7rem 0.9rem; margin-top: 0.5rem; }
    .season-title { font-size: 0.65rem; font-weight: 700; color: #ff6b00;
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
    .season-row { display: flex; justify-content: space-between; align-items: center;
        padding: 0.25rem 0; border-bottom: 1px solid #2e2e4a; }
    .season-row:last-child { border-bottom: none; }
    .season-label { font-size: 0.72rem; color: #aaaacc; }
    .season-val { font-size: 0.78rem; font-weight: 700; color: #ffffff; text-align: right; }
    .season-n { font-size: 0.65rem; color: #666688; font-weight: 400; }

    /* Make popovers match chip style */
    [data-testid="stPopover"] > button {
        background: #1a1a2e !important;
        border: 1px solid #2e2e4a !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.8rem !important;
        color: #ffffff !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        text-align: left !important;
        margin-bottom: 0.2rem !important;
    }
    [data-testid="stPopover"] > button:hover {
        border-color: #ff6b00 !important;
        color: #ff6b00 !important;
    }

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


@st.cache_data(show_spinner='Loading events data…')
def load_old_catalog_receivers(path: Path) -> pd.DataFrame:
    """Load play-level name + coverage data from 2026NFLEventsXl.xlsx."""
    _col_map = {
        'PLAY_UNIQUE_ID':        'play_unique_id',
        'PASSER':                'passer',
        'PASSER_ID':             'passer_id',
        'RUSHER':                'rusher',
        'RUSHER_ID':             'rusher_id',
        'RECEIVER':              'receiver',
        'RECEIVER_ID':           'receiver_id',
        'COVERAGE_CONCEPT_DESC': 'coverage_concept_desc',
    }
    want_out = ['play_unique_id', 'passer', 'passer_id', 'rusher', 'rusher_id',
                'receiver', 'receiver_id', 'coverage_concept_desc']
    try:
        ext = str(path).lower()
        if ext.endswith('.xlsx') or ext.endswith('.xls'):
            # Read all columns first (avoids openpyxl usecols lambda issues),
            # then filter down to the ones we want.
            df = pd.read_excel(path, engine='openpyxl')
        else:
            df = pd.read_csv(path, low_memory=False)
        # Normalise column names to upper for matching
        df.columns = [str(c).strip() for c in df.columns]
        keep = {c: _col_map[c.upper()] for c in df.columns if c.upper() in _col_map}
        df = df[list(keep.keys())].rename(columns=keep)
        for col in want_out:
            if col not in df.columns:
                df[col] = None
        df['play_unique_id'] = pd.to_numeric(df['play_unique_id'], errors='coerce').astype('Int64')
        df['receiver_id']    = pd.to_numeric(df['receiver_id'],    errors='coerce')
        df['passer_id']      = pd.to_numeric(df['passer_id'],      errors='coerce')
        df['rusher_id']      = pd.to_numeric(df['rusher_id'],      errors='coerce')
        return df[want_out].drop_duplicates('play_unique_id')
    except Exception as _e:
        # Store error for debug expander; return empty so app still runs
        import streamlit as _st
        _st.session_state['_evt_load_error'] = str(_e)
        return pd.DataFrame(columns=want_out)


@st.cache_data(show_spinner='Merging x-stats…')
def load_xstats(file_bytes: bytes) -> pd.DataFrame:
    """
    Load a weekly x-stats CSV uploaded by the user.
    Returns a DataFrame keyed on play_unique_id (and game_code) with
    the x-stat columns normalised to lowercase catalog names.
    """
    import io as _io
    df = pd.read_csv(_io.BytesIO(file_bytes), low_memory=False)
    # Normalise column names: lowercase, strip spaces
    df.columns = [c.strip().lower() for c in df.columns]
    # Rename weekly file columns → catalog column names (handles case variants)
    _rename = {
        'xyards':      'xyards',
        'xrush%':      'xrush%',
        'xovryds':     'xovryds',
        'is_sack':     'is_sack',       # not in catalog x-stats but keep in case
        'xsack%':      'xsack%',
        'xscramble%':  'xscramble%',
        'xtd%':        'xtd%',
        'xrushtd%':    'xrushtd%',
    }
    df = df.rename(columns={k: v for k, v in _rename.items() if k in df.columns})
    # Numeric keys for joining
    for key_col in ('play_unique_id', 'game_code'):
        if key_col in df.columns:
            df[key_col] = pd.to_numeric(df[key_col], errors='coerce')
    # Keep only join keys + x-stat columns
    keep = [c for c in ['play_unique_id', 'game_code'] + _XSTAT_COLS if c in df.columns]
    return df[keep].drop_duplicates('play_unique_id')


def apply_xstats(catalog: pd.DataFrame, xstats: pd.DataFrame) -> pd.DataFrame:
    """
    Overwrite the catalog's x-stat columns with values from the weekly file.
    Plays not in the weekly file keep their catalog values unchanged.
    Returns a new DataFrame (does not mutate the cached catalog).
    """
    if xstats is None or xstats.empty:
        return catalog
    merged = catalog.copy()
    xs_cols = [c for c in _XSTAT_COLS if c in xstats.columns]
    if not xs_cols:
        return merged
    xs_slim = xstats[['play_unique_id'] + xs_cols].copy()
    # Suffix _new for the fresh values so we can detect which rows got updated
    xs_slim = xs_slim.rename(columns={c: f'{c}_new' for c in xs_cols})
    merged = merged.merge(xs_slim, on='play_unique_id', how='left')
    for col in xs_cols:
        new_col = f'{col}_new'
        if new_col in merged.columns:
            # Fill with new value where available, else keep original
            merged[col] = merged[new_col].combine_first(merged[col])
            merged.drop(columns=[new_col], inplace=True)
    return merged


# Map X-Info role codes → readable position group labels
_ROLE_GROUP = {
    # Outside WRs
    'LOR': 'Outside Receivers', 'ROR': 'Outside Receivers',
    # Slot WRs
    'LSR': 'Slot Receivers',    'RSR': 'Slot Receivers',
    # Inside WRs
    'LIR': 'Inside Receivers',  'RIR': 'Inside Receivers',
    'LIIR': 'Inside Receivers', 'RIIR': 'Inside Receivers', 'RIIIR': 'Inside Receivers',
    # Tight Ends (attached / wing)
    'LTE': 'Tight Ends',  'RTE': 'Tight Ends',
    'LIT': 'Tight Ends',  'RIT': 'Tight Ends',
    'LW':  'Tight Ends',  'RW':  'Tight Ends',
    'LIW': 'Tight Ends',  'RIW': 'Tight Ends',
    'PAL': 'Tight Ends',  'PAR': 'Tight Ends',
    'PBL': 'Tight Ends',  'PBR': 'Tight Ends',
    # Backs
    'RBL': 'Running Backs', 'RBM': 'Running Backs', 'RBR': 'Running Backs',
    'FBL': 'Fullbacks',     'FBM': 'Fullbacks',     'FBR': 'Fullbacks',
    'SBL': 'Slot Backs',    'SBR': 'Slot Backs',
    # OL (rare routes)
    'LG': 'Linemen', 'LT': 'Linemen', 'RT': 'Linemen',
}

def _role_group(role_str: str) -> str:
    return _ROLE_GROUP.get(str(role_str).strip().upper(), 'Other')


@st.cache_data(show_spinner='Building targeting stats…')
def build_targeting_rates(_new_cat: pd.DataFrame, _old_cat: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
        last_name, role_group, route, coverage,
        player_targeted, player_total,
        group_targeted, group_total
    one row per (last_name, role_group, route, coverage) combination.
    """
    # Melt new catalog: one row per play × offensive slot
    slots = []
    for i in range(1, 12):
        cols_needed = [
            'play_unique_id',
            f'off_{i}_player_last_name',
            f'off_{i}_player_id',
            f'off_{i}_route',
            f'off_{i}_role',
        ]
        available = [c for c in cols_needed if c in _new_cat.columns]
        if len(available) < 5:
            continue
        tmp = _new_cat[available].copy()
        tmp.columns = ['play_unique_id', 'last_name', 'player_id', 'route', 'role']
        slots.append(tmp)
    if not slots:
        return pd.DataFrame()

    plays = pd.concat(slots, ignore_index=True)
    plays['player_id'] = pd.to_numeric(plays['player_id'], errors='coerce')

    # Filter out empty routes
    plays = plays[plays['route'].notna()]
    plays['route'] = plays['route'].astype(str).str.strip()
    plays = plays[~plays['route'].str.lower().isin(['no route', 'no_route', 'none', 'nan', '—', ''])]

    # Map role → position group
    plays['role_group'] = plays['role'].apply(_role_group)

    # Join coverage + receiver_id + success_play from old catalog
    old_slim = _old_cat[['play_unique_id', 'receiver_id', 'coverage_concept_desc']].copy()
    plays = plays.merge(old_slim, on='play_unique_id', how='left')
    plays['coverage'] = plays['coverage_concept_desc'].fillna('Unknown').astype(str).str.strip()
    plays['last_name'] = plays['last_name'].astype(str).str.strip().str.upper()

    # Join success_play from new catalog (play-level, not slot-level)
    if 'success_play' in _new_cat.columns:
        success_slim = _new_cat[['play_unique_id', 'success_play']].drop_duplicates('play_unique_id')
        plays = plays.merge(success_slim, on='play_unique_id', how='left')
        plays['success'] = plays['success_play'].apply(
            lambda v: 1 if str(v).strip() in ('T', 'True', 'true', '1', '1.0') else 0
        )
    else:
        plays['success'] = 0

    # Was this player targeted on this play?
    plays['targeted'] = (plays['player_id'] == plays['receiver_id']).astype(int)
    # Success when targeted = targeted AND success
    plays['targeted_success'] = ((plays['targeted'] == 1) & (plays['success'] == 1)).astype(int)

    # Per-player stats: (last_name, role_group, route, coverage)
    player_grp = plays.groupby(['last_name', 'role_group', 'route', 'coverage'], as_index=False).agg(
        player_targeted=('targeted', 'sum'),
        player_total=('targeted', 'count'),
        player_success=('targeted_success', 'sum'),
    )

    # Per-position-group stats: (role_group, route, coverage)
    group_grp = plays.groupby(['role_group', 'route', 'coverage'], as_index=False).agg(
        group_targeted=('targeted', 'sum'),
        group_total=('targeted', 'count'),
        group_success=('targeted_success', 'sum'),
    )

    result = player_grp.merge(group_grp, on=['role_group', 'route', 'coverage'], how='left')
    return result


@st.cache_data(show_spinner='Loading catalog…')
def load_catalog(path: Path) -> pd.DataFrame:
    # Only load columns actually used by the app — cuts CSV parse time significantly
    _ALWAYS = [
        'play_unique_id', 'game_code', 'game_date', 'week', 'period', 'time_remaining',
        'down', 'distance', 'yd_from_goal', 'home_score', 'away_score',
        'home_team_nickname', 'away_team_nickname',
        'offensive_team_nickname', 'defensive_team_nickname',
        'offensive_formation', 'offensive_personnel', 'defensive_personnel',
        'defensive_front', 'men_in_box', 'blitz', 'is_motion', 'play_action',
        'snap_hash', 'qb_pos', 'play_type', 'play_concept_desc',
        'initial_run_direction', 'rusher', 'receiver',
        'event_name', 'coverage_concept_desc',
        'xyards', 'xrush%', 'xovryds', 'xsack%', 'xscramble%', 'xtd%', 'xrushtd%',
        'yd_gained', 'success_play', 'is_first_down', 'is_td', 'explosive',
    ]
    # Offensive slots 1-11
    _SLOT_COLS = []
    for i in range(1, 12):
        _SLOT_COLS += [
            f'off_{i}_role', f'off_{i}_number', f'off_{i}_player_last_name',
            f'off_{i}_player_id', f'off_{i}_route', f'off_{i}_route_distance',
        ]
    # Defensive slots 1-11
    for i in range(1, 12):
        _SLOT_COLS += [
            f'def_{i}_role', f'def_{i}_number', f'def_{i}_player_last_name', f'def_{i}_press',
        ]
    try:
        all_cols = set(_ALWAYS + _SLOT_COLS)
        if str(path).endswith('.parquet'):
            import pyarrow.parquet as pq
            available = set(pq.read_schema(path).names)
            cols = list(all_cols & available)
            df = pd.read_parquet(path, columns=cols)
        else:
            df = pd.read_csv(path, usecols=lambda c: c in all_cols, low_memory=False)
    except Exception:
        if str(path).endswith('.parquet'):
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, low_memory=False)
    for col in ['week','down','distance','yd_from_goal','time_remaining',
                'period','home_score','away_score','men_in_box','play_unique_id','game_code',
                'xyards','xrush%','xovryds','xsack%','xscramble%','xtd%','xrushtd%']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Strip leading/trailing whitespace from all string columns
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())
    # Remove kickoff/special teams plays and ? & ? plays
    if 'event_name' in df.columns:
        df = df[~df['event_name'].str.lower().str.contains('kick', na=False)]
    if 'play_type' in df.columns:
        df = df[~df['play_type'].str.lower().str.contains('kick', na=False)]
    if 'down' in df.columns:
        df = df[df['down'].notna() & (df['down'] > 0)]
    if 'distance' in df.columns:
        df = df[df['distance'].notna() & (df['distance'] > 0)]
    if 'offensive_formation' in df.columns:
        df = df[df['offensive_formation'].notna() & (df['offensive_formation'].astype(str).str.strip() != '')]
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

    receiver_name = _clean(row.get('receiver'), '')

    player_routes      = {}   # LAST_NAME.upper() -> route string
    player_ids         = {}   # LAST_NAME.upper() -> player_id (numeric)
    player_roles       = {}   # LAST_NAME.upper() -> role_group string
    player_route_dists = {}   # LAST_NAME.upper() -> route depth in yards (float or None)
    for i in range(1, 12):
        route_val = _clean(row.get(f'off_{i}_route'), '')
        if not route_val or route_val.lower() in ('no route', 'no_route', 'none', 'nan', '—', ''):
            continue
        name_val = _clean(row.get(f'off_{i}_player_last_name'), '')
        if name_val and name_val != '—':
            key = name_val.upper()
            player_routes[key] = route_val
            pid_val = row.get(f'off_{i}_player_id')
            try:
                player_ids[key] = int(float(pid_val)) if pd.notna(pid_val) else None
            except (ValueError, TypeError):
                player_ids[key] = None
            role_val = _clean(row.get(f'off_{i}_role'), '')
            player_roles[key] = _role_group(role_val) if role_val else 'Other'
            dist_raw = row.get(f'off_{i}_route_distance')
            try:
                player_route_dists[key] = float(dist_raw) if pd.notna(dist_raw) else None
            except (ValueError, TypeError):
                player_route_dists[key] = None

    # Pull passer / rusher / receiver / coverage from 2026NFLEventsXl
    targeted_name   = ''   # LAST NAME upper — used to match red route on field
    play_coverage   = ''
    events_passer   = ''   # Full name "First Last" from events file
    events_rusher   = ''
    events_receiver = ''   # Full name "First Last" from events file
    try:
        old_cat   = load_old_catalog_receivers(DATA_PATH_OLD)
        _pid      = pd.to_numeric(play_id, errors='coerce')
        old_match = old_cat[old_cat['play_unique_id'] == _pid]
        if not old_match.empty:
            old_row = old_match.iloc[0]

            def _evt_full(raw):
                """'Last, First' → 'First Last'"""
                s = _clean(raw, '')
                if not s or s == '—': return ''
                if ',' in s:
                    parts = [p.strip() for p in s.split(',', 1)]
                    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else s
                return s

            events_passer   = _evt_full(old_row.get('passer'))
            events_rusher   = _evt_full(old_row.get('rusher'))
            events_receiver = _evt_full(old_row.get('receiver'))

            # targeted_name stays as LASTNAME.upper() for route-highlight matching
            raw_recv = _clean(old_row.get('receiver'), '')
            if raw_recv:
                targeted_name = (raw_recv.split(',')[0].strip().upper()
                                 if ',' in raw_recv
                                 else raw_recv.strip().split()[-1].upper())

            play_coverage = _clean(old_row.get('coverage_concept_desc'), '')
    except Exception as _evt_err:
        import traceback as _tb
        st.session_state['_evt_debug'] = (
            f"Events join error: {_evt_err}\n{_tb.format_exc()}"
        )

    return row, df_off, df_def, receiver_name, player_routes, targeted_name, player_ids, play_coverage, player_roles, player_route_dists, events_passer, events_rusher, events_receiver


@st.cache_data(show_spinner=False)
def render_play_png(play_id: int, game_code: int, _hash: str) -> bytes:
    """Generate the static matplotlib PNG — called only when Download is clicked."""
    cat = load_catalog(DATA_PATH)
    matches = cat[(cat['play_unique_id']==play_id) & (cat['game_code']==game_code)]
    if matches.empty:
        matches = cat[cat['play_unique_id']==play_id]
    if matches.empty:
        return b''
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

    yd = row.get('yd_from_goal')
    if pd.notna(yd):
        yd_from_goal = int(float(yd))
        yard_line = 100 - yd_from_goal if yd_from_goal > 50 else yd_from_goal
    else:
        yard_line = 50

    off_team = _clean(row.get('offensive_team_nickname'), '')
    def_team = _clean(row.get('defensive_team_nickname'), '')

    fig, _ = plot_offense_v2(
        df_coords=df_off, df_def_coords=df_def,
        title='', yard_line=yard_line, attacking_right=True,
        off_team=off_team, def_team=def_team,
    )
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _route_waypoints(route_name, px, py, attacking_right, field_y_min=0.0, field_y_max=53.3,
                     route_dist=None):
    """
    Return a list of (x, y) waypoints for a named route starting at (px, py).
    All distances are in plot units (1 unit = 1 yard).
    'downfield' = +x when attacking_right, -x otherwise.
    'outside'   = toward nearest sideline based on py position.
    'inside'    = toward center (y=26.65).
    route_dist  : actual route depth in yards from off_N_route_distance (overrides defaults).
    """
    d = 1 if attacking_right else -1          # downfield direction
    center_y = (field_y_min + field_y_max) / 2
    outside = -1 if py < center_y else 1      # toward nearest sideline
    inside  = -outside                         # toward middle

    def _stem(default):
        """Use actual route_dist if valid and positive, else fall back to default."""
        try:
            v = float(route_dist)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass
        return default

    r = str(route_name).strip().lower()

    if r in ('no route', 'no_route', 'none', '', 'nan'):
        return None

    # Each route returns a list of (x,y) waypoints including the start point
    if r == 'curl':
        stem = _stem(6)   # shorter than comeback — 5-7 yards
        return [(px, py),
                (px + d*stem, py),               # run straight upfield
                (px + d*(stem-2), py + inside*2)]  # break down and turn back diagonally

    elif r == 'out':
        stem = _stem(7)
        horiz = 6
        return [(px, py),
                (px + d*stem, py),
                (px + d*stem, py + outside*horiz)]

    elif r == 'flat':
        return [(px, py),
                (px + d*1.5, py + outside*6)]

    elif r in ('go', 'go route', 'go_route'):
        return [(px, py),
                (px + d*_stem(25), py)]

    elif r == 'dig':
        stem = _stem(12)
        cross = stem * 0.75
        return [(px, py),
                (px + d*stem, py),
                (px + d*stem, py + inside*cross)]

    elif r == 'drag':
        return [(px, py),
                (px + d*2, py),
                (px + d*3, py + inside*8)]

    elif r == 'swing':
        return [(px, py),
                (px - d*1,  py + outside*4),
                (px + d*5,  py + outside*8)]

    elif r in ('underneath screen', 'underneath_screen', 'screen'):
        return [(px, py),
                (px - d*0.5, py + outside*2.5)]

    elif r == 'slant':
        stem = _stem(9)
        return [(px, py),
                (px + d*2, py),
                (px + d*stem, py + inside*7)]

    elif r == 'post':
        stem = _stem(10)
        diag = stem * 1.2
        return [(px, py),
                (px + d*stem, py),
                (px + d*(stem+diag), py + inside*diag*0.7)]

    elif r == 'corner':
        stem = _stem(10)
        diag = stem * 1.2
        return [(px, py),
                (px + d*stem, py),
                (px + d*(stem+diag), py + outside*diag*0.7)]

    elif r == 'cross':
        stem = _stem(6)
        cross = stem * 1.67
        return [(px, py),
                (px + d*stem, py),
                (px + d*(stem+cross*0.6), py + inside*cross)]

    elif r in ('bubble screen', 'bubble_screen', 'bubble'):
        return [(px, py),
                (px - d*1,   py + outside*2),
                (px - d*0.5, py + outside*5)]

    elif r == 'wheel':
        return [(px, py),
                (px + d*2,  py + outside*6),
                (px + d*5,  py + outside*8),
                (px + d*_stem(22), py + outside*9)]

    elif r == 'comeback':
        stem = _stem(15)
        return [(px, py),
                (px + d*stem, py),
                (px + d*(stem-4), py + outside*3)]

    elif r == 'fade':
        return [(px, py),
                (px + d*_stem(20), py + outside*4)]

    # Fallback — treat unknown as a short go
    return [(px, py), (px + d*8, py)]


def _run_arrow_waypoints(concept, direction, rb_px, rb_py,
                         ol_positions, attacking_right,
                         field_y_min=0.0, field_y_max=53.3):
    """
    Return (x, y) waypoints for a run concept arrow.

    concept   : play_concept_desc string (e.g. "Inside Zone")
    direction : initial_run_direction string ("L" or "R")
    rb_px/py  : ballcarrier's plot-space position
    ol_positions : list of (px, py) for all OL players (C, LG, RG, LT, RT)
                   used to anchor gap targets to actual player positions
    attacking_right : bool (always True in this app)

    Gap landmarks are derived from the actual OL x-positions.
    downfield = +x when attacking_right.
    """
    d   = 1 if attacking_right else -1
    R   = direction.strip().upper() == 'R'   # True = right, False = left
    # In this coordinate system: higher y = LEFT side of field (LG=29, LT=31)
    #                             lower  y = RIGHT side of field (RG=24, RT=22)
    side = -1 if R else 1                   # R goes to lower y, L goes to higher y

    # ── Derive OL landmarks from actual plotted positions ──────────────────
    # ol_positions may contain guards, tackles, center in no guaranteed order.
    # Sort by y to get left→right ordering.
    ys = sorted([p[1] for p in ol_positions]) if ol_positions else []
    n  = len(ys)

    def _gap(i):
        """Return midpoint between i-th and (i+1)-th OL player (sorted by y)."""
        if n >= 2 and 0 <= i < n - 1:
            return (ys[i] + ys[i+1]) / 2
        return rb_py  # fallback: stay in lane

    # Identify approximate gaps; center is median OL player
    center_y = ys[n//2] if n else (field_y_min + field_y_max) / 2

    # A gap: between center and guard (one step from center toward play side)
    a_gap = center_y + side * abs(_gap(n//2, ) - center_y) * 0.6 if n >= 3 else center_y + side * 2
    # B gap: between guard and tackle
    b_gap = center_y + side * abs(_gap(n//2, ) - center_y) * 1.2 if n >= 4 else center_y + side * 4
    # C gap / edge: outside tackle
    c_gap = center_y + side * (abs(ys[-1] - center_y) + 2) if n >= 2 else center_y + side * 7
    edge  = center_y + side * (abs(ys[-1] - center_y) + 5) if n >= 2 else center_y + side * 9

    # Use simpler direct gap calculations anchored to actual OL spread
    if n >= 5:
        sorted_ys = sorted(ys)  # ascending: RT(low-y), RG, C, LG, LT(high-y)
        mid = n // 2            # center index = 2 when n=5
        if R:
            # Right side has LOWER y values: RG is mid-1, RT is mid-2
            a_gap  = (sorted_ys[mid] + sorted_ys[mid-1]) / 2   # C / RG
            b_gap  = (sorted_ys[mid-1] + sorted_ys[mid-2]) / 2  # RG / RT
            c_gap  = sorted_ys[mid-2]                            # at RT
            edge   = sorted_ys[mid-2] - 2                        # outside RT
        else:
            # Left side has HIGHER y values: LG is mid+1, LT is mid+2
            a_gap  = (sorted_ys[mid] + sorted_ys[mid+1]) / 2   # C / LG
            b_gap  = (sorted_ys[mid+1] + sorted_ys[mid+2]) / 2  # LG / LT
            c_gap  = sorted_ys[mid+2]                            # at LT
            edge   = sorted_ys[mid+2] + 2                        # outside LT
    elif n >= 2:
        spread = abs(ys[-1] - ys[0]) / 2
        a_gap = center_y + side * spread * 0.3
        b_gap = center_y + side * spread * 0.7
        c_gap = center_y + side * spread
        edge  = center_y + side * (spread + 3)

    c = str(concept).strip().lower()

    # ── Concept → waypoints ────────────────────────────────────────────────
    if c in ('inside zone', 'iz'):
        # Slight lateral angle to A/B gap, then vertical
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.5),
            (rb_px + d*4,   aim),
            (rb_px + d*10,  aim),
        ]

    elif c in ('outside zone', 'oz'):
        # Lateral flow toward C gap/edge, gradual bend upfield
        aim = c_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (aim - rb_py) * 0.4),
            (rb_px + d*3,   aim),
            (rb_px + d*10,  aim),
        ]

    elif c == 'duo':
        # Downhill through A/B gap, less lateral than IZ
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1.5, rb_py + (aim - rb_py) * 0.3),
            (rb_px + d*4,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'power':
        # Short downhill approach then angle to B/C gap
        aim = b_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.3),
            (rb_px + d*5,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'counter':
        # Initial step AWAY from play side, then cut back toward B/C gap
        away = -side
        aim  = b_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + away * 1.5),   # false step
            (rb_px + d*3,   rb_py),                  # plant
            (rb_px + d*5,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'trap':
        # Fast-hitting A/B interior, minimal lateral
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (aim - rb_py) * 0.2),
            (rb_px + d*3,   aim),
            (rb_px + d*8,   aim),
        ]

    elif c == 'long trap':
        # Like trap but to B/C gap
        aim = b_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.4),
            (rb_px + d*4,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'sweep':
        # Lateral to outside T/TE, then turn north-south
        aim = edge
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (aim - rb_py) * 0.5),
            (rb_px + d*2,   aim),
            (rb_px + d*8,   aim),
        ]

    elif c == 'end around':
        # WR crosses behind formation, attacks opposite edge
        opp_edge = center_y - side * (abs(edge - center_y))
        return [
            (rb_px,         rb_py),
            (rb_px - d*1,   opp_edge),   # cross behind LOS area
            (rb_px + d*3,   opp_edge),
            (rb_px + d*9,   opp_edge),
        ]

    elif c == 'reverse':
        # Two direction changes — initial flow one way, then back the other
        opp_edge = center_y - side * (abs(edge - center_y))
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (-side) * 3),   # initial flow wrong way
            (rb_px,         center_y),               # reversal through middle
            (rb_px + d*3,   opp_edge),
            (rb_px + d*9,   opp_edge),
        ]

    elif c == 'draw':
        # Delayed start, then straight downfield through A/B gap
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px - d*1,   rb_py),   # delay
            (rb_px + d*1,   rb_py),
            (rb_px + d*4,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c in ('iso', 'isolation'):
        # Direct downhill path through A/B gap
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*3,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'toss':
        # Immediate lateral to edge, rounded turn upfield (like sweep but wider start)
        aim = edge
        return [
            (rb_px,         rb_py),
            (rb_px + d*0.5, rb_py + (aim - rb_py) * 0.7),
            (rb_px + d*2,   aim),
            (rb_px + d*8,   aim),
        ]

    elif c in ('speed option', 'option'):
        # QB attacks C gap / edge, pitch is wider
        aim = c_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.5),
            (rb_px + d*5,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'qb sneak':
        # Straight over center, very short
        return [
            (rb_px,       center_y),
            (rb_px + d*3, center_y),
        ]

    elif c in ('zone read', 'read option'):
        # RB branch: inside zone A/B gap
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.5),
            (rb_px + d*4,   aim),
            (rb_px + d*9,   aim),
        ]

    elif c == 'belly':
        # Slight play-side step, downhill through B gap
        aim = b_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (aim - rb_py) * 0.2),
            (rb_px + d*3,   aim),
            (rb_px + d*8,   aim),
        ]

    elif c == 'dart':
        # Direct to B/C gap, modest angle
        aim = b_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*2,   rb_py + (aim - rb_py) * 0.4),
            (rb_px + d*5,   aim),
            (rb_px + d*8,   aim),
        ]

    elif c == 'dive':
        # Almost straight vertical, A gap
        aim = a_gap
        return [
            (rb_px,         rb_py),
            (rb_px + d*1,   rb_py + (aim - rb_py) * 0.1),
            (rb_px + d*3,   aim),
            (rb_px + d*7,   aim),
        ]

    # Fallback: generic interior run
    return [
        (rb_px,         rb_py),
        (rb_px + d*2,   rb_py + side * 1),
        (rb_px + d*5,   rb_py + side * 2),
        (rb_px + d*9,   rb_py + side * 2),
    ]


def build_plotly_field(df_off, df_def, yard_line, attacking_right, off_team, def_team, distance=None,
                       receiver_name=None, player_routes=None, targeted_name=None,
                       player_ids=None, play_coverage=None, targeting_rates=None, player_roles=None,
                       play_type=None, play_concept=None, run_direction=None, rusher_name=None,
                       player_route_dists=None):
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

    x_min, x_max = -15.0, 30.0
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
        if x_min <= yard_x <= x_max:
            # Draw the faint yard line only when it doesn't coincide with the LOS
            if yard_x != 0:
                fig.add_shape(type='line', x0=yard_x, x1=yard_x, y0=y_min, y1=y_max,
                              line=dict(color='white', width=1.0), opacity=0.3)
            # Always draw the number — overlap with LOS is fine and intentional
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

    # First-down marker
    # x=0 is the LOS; each plot unit = 1 yard (feet/3 in _to_plot, but yard markers
    # are placed as `marker - yard_line` which is already in yards). So distance yards
    # downfield = +distance plot units when attacking right, -distance when attacking left.
    if distance and distance > 0:
        fd_x = float(distance) if attacking_right else -float(distance)
        if x_min <= fd_x <= x_max:
            fig.add_shape(type='line', x0=fd_x, x1=fd_x, y0=y_min, y1=y_max,
                          line=dict(color='#ffe066', width=2.0), opacity=0.45)
            fig.add_annotation(x=fd_x + (0.25 if attacking_right else -0.25),
                               y=y_max - 0.8, text='1st', showarrow=False,
                               font=dict(color='#ffe066', size=7*SCALE), opacity=0.65,
                               xanchor='left' if attacking_right else 'right', yanchor='top')

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
    _oc = NFL_TEAM_COLORS.get(str(off_team).strip(), {}).get('primary', '#3a6ea5')
    _dc = NFL_TEAM_COLORS.get(str(def_team).strip(), {}).get('primary', '#a53a3a')

    for _, p in df_off.iterrows():
        px, py = _to_plot(p['x_ft'], p['y_ft'])
        num  = _fmt_num(p.get('player_number'))
        name = str(p.get('player_name', '')).strip()
        role = str(p.get('role', '')).strip()
        hover = (
            f"<b style='font-size:13px;color:{_oc}'>#{num} {name}</b><br>"
            f"<span style='color:#8888aa;font-size:10px'>{off_team.upper()} · OFFENSE</span><br>"
            f"<span style='color:#aaaacc;font-size:11px'>Role: <b style='color:#fff'>{role}</b></span>"
            f"<extra></extra>"
        )
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

    # Draw receiver routes — targeted receiver in red, all others in gold
    ROUTE_COLOR_DEFAULT  = '#ffe066'   # Madden-style gold
    ROUTE_COLOR_TARGETED = '#ff3333'   # red — targeted receiver
    _targeted_upper = targeted_name.strip().upper() if targeted_name else ''

    if player_routes:
        for _, p in df_off.iterrows():
            p_name = str(p.get('player_name', '')).strip().upper()
            if not p_name:
                continue
            route_val = None
            matched_key = None
            for key, val in player_routes.items():
                if key == p_name or key in p_name or p_name in key:
                    route_val = val
                    matched_key = key
                    break
            if not route_val:
                continue

            # Determine if this player is the targeted receiver
            is_targeted = bool(
                _targeted_upper and matched_key and (
                    _targeted_upper == matched_key
                    or _targeted_upper in matched_key
                    or matched_key in _targeted_upper
                )
            )
            r_color = ROUTE_COLOR_TARGETED if is_targeted else ROUTE_COLOR_DEFAULT
            r_width = 3.5 if is_targeted else 2.5

            # Build hover tooltip with targeting rates
            cov_label  = (play_coverage or 'Unknown').strip()
            this_group = (player_roles or {}).get(matched_key, 'Other')

            # ── Card-style hover tooltip ──────────────────────────────────
            def _divider():
                return "<br>"

            def _stat_block(label, pct, detail):
                return (
                    f"<span style='color:#8888aa;font-size:10px'>{label}</span><br>"
                    f"<b style='color:#ffffff;font-size:12px'>{pct}</b>"
                    f"<span style='color:#8888aa;font-size:10px'>&nbsp;·&nbsp;{detail}</span><br>"
                )

            # Header: LAMB — SLANT / COWBOYS · OFFENSE
            tip_header = (
                f"<b style='font-size:14px;color:{r_color};letter-spacing:0.05em'>"
                f"{matched_key} — {route_val}</b><br>"
                f"<span style='color:#8888aa;font-size:10px;letter-spacing:0.1em'>"
                f"{off_team.upper()} · OFFENSE</span>"
            )

            stat_blocks = []
            if targeting_rates is not None and not targeting_rates.empty:
                tr = targeting_rates
                pmask = (
                    (tr['last_name'] == matched_key) &
                    (tr['route'].str.upper() == route_val.upper()) &
                    (tr['coverage'] == cov_label)
                )
                pr = tr[pmask]
                if not pr.empty:
                    pt_n = int(pr.iloc[0]['player_targeted'])
                    pt_d = int(pr.iloc[0]['player_total'])
                    pt_pct = f"{100*pt_n/pt_d:.0f}%" if pt_d else 'N/A'
                    ps_n  = int(pr.iloc[0]['player_success'])
                    ps_pct = f"{100*ps_n/pt_n:.0f}%" if pt_n else 'N/A'
                    stat_blocks.append(_divider())
                    stat_blocks.append(_stat_block(
                        f'{matched_key} "{route_val}" Target Rate vs {cov_label}',
                        pt_pct, f"{pt_n} of {pt_d} routes"
                    ))
                    stat_blocks.append(_stat_block(
                        f'{matched_key} "{route_val}" Success Rate vs {cov_label}',
                        ps_pct, f"{ps_n} of {pt_n} targets"
                    ))

                gmask = (
                    (tr['role_group'] == this_group) &
                    (tr['route'].str.upper() == route_val.upper()) &
                    (tr['coverage'] == cov_label)
                )
                gr = tr[gmask]
                if not gr.empty:
                    gt_n = int(gr['group_targeted'].iloc[0])
                    gt_d = int(gr['group_total'].iloc[0])
                    gt_pct = f"{100*gt_n/gt_d:.0f}%" if gt_d else 'N/A'
                    gs_n  = int(gr['group_success'].iloc[0])
                    gs_pct = f"{100*gs_n/gt_n:.0f}%" if gt_n else 'N/A'
                    # Shorten group name for display: "Outside Receivers" → "Outside WR"
                    _grp_short = (this_group
                                  .replace('Outside Receivers', 'Outside WR')
                                  .replace('Slot Receivers', 'Slot WR')
                                  .replace('Inside Receivers', 'Inside WR')
                                  .replace('Running Backs', 'RB')
                                  .replace('Tight Ends', 'TE')
                                  .replace('Fullbacks', 'FB'))
                    stat_blocks.append(_divider())
                    stat_blocks.append(_stat_block(
                        f'{_grp_short} "{route_val}" Target Rate vs {cov_label}',
                        gt_pct, f"{gt_n} of {gt_d} routes"
                    ))
                    stat_blocks.append(_stat_block(
                        f'{_grp_short} "{route_val}" Success Rate vs {cov_label}',
                        gs_pct, f"{gs_n} of {gt_n} targets"
                    ))

            # Footer: season tag
            stat_blocks.append(_divider())
            stat_blocks.append(
                f"<span style='color:#555577;font-size:9px;letter-spacing:0.12em'>2026 Season</span>"
            )

            hover_tip = tip_header + ''.join(stat_blocks) + '<extra></extra>'

            rpx, rpy = _to_plot(p['x_ft'], p['y_ft'])
            r_dist = (player_route_dists or {}).get(matched_key)
            pts = _route_waypoints(route_val, rpx, rpy, attacking_right, y_min, y_max,
                                   route_dist=r_dist)
            if pts and len(pts) >= 2:
                pts = [(max(x_min, min(x_max, x)), max(y_min, min(y_max, y))) for x, y in pts]
                xs = [pt[0] for pt in pts]
                ys = [pt[1] for pt in pts]
                # Invisible wider line so the hover is easy to trigger
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode='lines',
                    line=dict(color='rgba(0,0,0,0)', width=12),
                    hovertemplate=hover_tip, showlegend=False, name='',
                ))
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode='lines',
                    line=dict(color=r_color, width=r_width),
                    hoverinfo='skip', showlegend=False,
                ))
                fig.add_annotation(
                    x=xs[-1], y=ys[-1],
                    ax=xs[-2], ay=ys[-2],
                    xref='x', yref='y', axref='x', ayref='y',
                    showarrow=True, arrowhead=2, arrowsize=1.4,
                    arrowwidth=r_width, arrowcolor=r_color,
                    text='',
                )

    # ── Draw run arrow (run plays only) ─────────────────────────────────────
    _is_run = str(play_type or '').strip().lower() in ('run', 'rush')
    if _is_run and play_concept and run_direction:
        # Find the ballcarrier position — match rusher_name to df_off
        rb_px, rb_py = 0.0, (y_min + y_max) / 2   # fallback: center of field
        if rusher_name and df_off is not None and not df_off.empty:
            raw = str(rusher_name).strip()
            # Handle "Last, First" or "First Last" formats — extract last name
            if ',' in raw:
                rusher_upper = raw.split(',')[0].strip().upper()
            else:
                rusher_upper = raw.strip().split()[-1].upper()
            for _, p in df_off.iterrows():
                p_name = str(p.get('player_name', '')).strip().upper()
                if rusher_upper in p_name or p_name in rusher_upper:
                    rb_px, rb_py = _to_plot(p['x_ft'], p['y_ft'])
                    break

        # Collect OL positions (roles: LT, LG, C, RG, RT)
        OL_ROLES = {'LT', 'LG', 'C', 'RG', 'RT'}
        ol_pts = []
        if df_off is not None and not df_off.empty:
            for _, p in df_off.iterrows():
                if str(p.get('role', '')).strip().upper() in OL_ROLES:
                    ol_pts.append(_to_plot(p['x_ft'], p['y_ft']))

        pts = _run_arrow_waypoints(
            concept=play_concept,
            direction=run_direction,
            rb_px=rb_px, rb_py=rb_py,
            ol_positions=ol_pts,
            attacking_right=attacking_right,
            field_y_min=y_min, field_y_max=y_max,
        )

        RUN_COLOR = '#00e5ff'   # bright cyan — distinct from route gold/red
        RUN_WIDTH = 3.0

        if pts and len(pts) >= 2:
            pts = [(max(x_min, min(x_max, x)), max(y_min, min(y_max, y))) for x, y in pts]
            rxs = [p[0] for p in pts]
            rys = [p[1] for p in pts]
            run_hover = (
                f"<b style='font-size:13px;color:{RUN_COLOR}'>{play_concept}</b><br>"
                f"<span style='color:#8888aa;font-size:10px'>{str(run_direction).upper()} · RUN PLAY</span>"
                f"<extra></extra>"
            )
            # Invisible wide hit target
            fig.add_trace(go.Scatter(
                x=rxs, y=rys, mode='lines',
                line=dict(color='rgba(0,0,0,0)', width=12),
                hovertemplate=run_hover, showlegend=False, name='',
            ))
            # Visible arrow line
            fig.add_trace(go.Scatter(
                x=rxs, y=rys, mode='lines',
                line=dict(color=RUN_COLOR, width=RUN_WIDTH, dash='dot'),
                hoverinfo='skip', showlegend=False,
            ))
            # Arrowhead at tip
            fig.add_annotation(
                x=rxs[-1], y=rys[-1],
                ax=rxs[-2], ay=rys[-2],
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=2, arrowsize=1.4,
                arrowwidth=RUN_WIDTH, arrowcolor=RUN_COLOR,
                text='',
            )

    # Draw defense
    if df_def is not None and not df_def.empty:
        for _, p in df_def.iterrows():
            px, py = _to_plot(p['x_ft'], p['y_ft'])
            num   = _fmt_num(p.get('player_number'))
            name  = str(p.get('player_name', '')).strip()
            role  = str(p.get('role', '')).strip()
            press = int(p.get('press', 0)) if not pd.isna(p.get('press', 0)) else 0
            hover = (
                f"<b style='font-size:13px;color:{_dc}'>#{num} {name}</b><br>"
                f"<span style='color:#8888aa;font-size:10px'>{def_team.upper()} · DEFENSE</span><br>"
                f"<span style='color:#aaaacc;font-size:11px'>Role: <b style='color:#fff'>{role}</b></span>"
                + (f"<br><span style='color:#ffdd00;font-size:11px'>⚡ Press</span>" if press == 1 else "")
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
            bgcolor='#121220',
            bordercolor='#2e2e4a',
            font=dict(color='#e8e8f0', size=12, family='Arial'),
            namelength=0,
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


def _sim_row_html(label, this_val, team_avg_val, league_avg_val, fmt_this, fmt_team, fmt_league, higher_is_better=True):
    """Render one comparison row with team avg and league avg columns."""
    def _arrow_cls(this_v, avg_v):
        try:
            diff = this_v - avg_v
            if abs(diff) < 0.001:
                return 'sim-avg', ''
            elif (diff > 0) == higher_is_better:
                return 'sim-up', ' ▲'
            else:
                return 'sim-down', ' ▼'
        except:
            return 'sim-avg', ''
    t_cls, t_arrow = _arrow_cls(this_val, team_avg_val)
    l_cls, l_arrow = _arrow_cls(this_val, league_avg_val)
    return f"""
        <tr>
            <td style="color:#aaaacc">{label}</td>
            <td class="sim-this">{fmt_this}</td>
            <td class="{t_cls}">{fmt_team}{t_arrow}</td>
            <td class="{l_cls}">{fmt_league}{l_arrow}</td>
        </tr>"""


def main():
    cat     = load_catalog(DATA_PATH)
    old_cat = load_old_catalog_receivers(DATA_PATH_OLD)

    # ── Apply weekly x-stats if the user uploaded one ───────────────────────
    # xstats_file is populated by the sidebar uploader widget defined below;
    # we read it here AFTER the sidebar block runs (Streamlit evaluates the
    # full script top-to-bottom, so we pull it from session_state instead).
    _xstats_df = None
    if 'xstats_bytes' in st.session_state and st.session_state['xstats_bytes']:
        _xstats_df = load_xstats(st.session_state['xstats_bytes'])
    if _xstats_df is not None:
        cat = apply_xstats(cat, _xstats_df)

    # Compute once per session — this is the expensive aggregation step
    targeting_rates = build_targeting_rates(cat, old_cat)

    with st.sidebar:
        st.markdown('### 🏈 xInfoViz')
        st.markdown('<p style="color:#8888aa;font-size:0.8rem;">2026 NFL Season</p>', unsafe_allow_html=True)
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

            # ── Offensive team filter ────────────────────────────────────────
            teams = sorted(game_rows['offensive_team_nickname'].dropna().unique().tolist())
            selected_team = st.selectbox('Offensive team', options=['Both teams'] + teams)

            # ── Play Type filter ─────────────────────────────────────────────
            _pt_opts = ['All play types', 'Pass', 'Run', 'Scramble', 'Sack']
            _pt_icons = {'Pass': '🎯', 'Run': '🏃', 'Scramble': '💨', 'Sack': '🔨'}
            selected_play_type = st.selectbox(
                'Play type',
                options=_pt_opts,
                format_func=lambda v: v if v == 'All play types' else f"{_pt_icons.get(v,'')} {v}",
            )

            # ── Highlights filter ────────────────────────────────────────────
            _HL_ALL  = 'All plays'
            _HL_OPTS = [
                _HL_ALL,
                '🏈 Touchdowns',
                '💥 Big plays (25+ yds)',
                '✅ 3rd & 4th down conversions',
                '🔄 Turnovers',
                '🔨 Sacks',
                '🎭 Play action',
                '🏃 Scrambles',
                '📺 Red zone',
            ]
            selected_highlight = st.selectbox('Highlights', options=_HL_OPTS)

            # ── Player Focus filter ──────────────────────────────────────────
            def _parse_last(name_str):
                """Extract last name from 'Last, First' or 'First Last' format."""
                s = str(name_str).strip()
                if not s or s in ('nan', '—', ''): return None
                if ',' in s:
                    return s.split(',')[0].strip()
                return s.strip().split()[-1]

            def _full_name(name_str):
                """Convert 'Last, First' → 'First Last' for display."""
                s = str(name_str).strip()
                if not s or s in ('nan', '—', ''): return None
                if ',' in s:
                    parts = [p.strip() for p in s.split(',', 1)]
                    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else s
                return s

            _player_names = set()
            for _pcol in ('passer', 'rusher', 'receiver'):
                if _pcol in game_rows.columns:
                    _player_names.update(
                        _full_name(v) for v in game_rows[_pcol].dropna().unique()
                        if _full_name(v)
                    )
            _player_list = ['Any player'] + sorted(_player_names)
            selected_player = st.selectbox('Player focus', options=_player_list)

            # ── Apply all filters ────────────────────────────────────────────
            filtered = game_rows.copy()
            if selected_team != 'Both teams':
                filtered = filtered[filtered['offensive_team_nickname'] == selected_team]

            if selected_play_type != 'All play types':
                filtered = filtered[
                    filtered['play_type'].str.strip().str.lower() == selected_play_type.lower()
                ]

            if selected_highlight != _HL_ALL:
                if selected_highlight == '🏈 Touchdowns':
                    filtered = filtered[filtered['is_td'] == True]
                elif selected_highlight == '💥 Big plays (25+ yds)':
                    filtered = filtered[pd.to_numeric(filtered['yd_gained'], errors='coerce') >= 25]
                elif selected_highlight == '✅ 3rd & 4th down conversions':
                    filtered = filtered[
                        (filtered['down'].isin([3.0, 4.0])) &
                        (filtered['is_first_down'].astype(str).str.strip() == 'T')
                    ]
                elif selected_highlight == '🔄 Turnovers':
                    filtered = filtered[
                        filtered['event_name'].str.lower().str.contains('intercept', na=False)
                    ]
                elif selected_highlight == '🔨 Sacks':
                    filtered = filtered[
                        filtered['event_name'].str.lower().str.contains('sack', na=False)
                    ]
                elif selected_highlight == '🎭 Play action':
                    filtered = filtered[
                        filtered['play_action'].astype(str).str.strip().isin(['Y', 'J', 'P', 'E'])
                    ]
                elif selected_highlight == '🏃 Scrambles':
                    filtered = filtered[
                        filtered['play_type'].astype(str).str.strip().str.lower() == 'scramble'
                    ]
                elif selected_highlight == '📺 Red zone':
                    filtered = filtered[
                        pd.to_numeric(filtered['yd_from_goal'], errors='coerce') <= 20
                    ]

            if selected_player != 'Any player':
                def _player_match(row_ser, player_full):
                    for col in ('passer', 'rusher', 'receiver'):
                        if col in row_ser.index:
                            fn = _full_name(row_ser[col])
                            if fn and fn == player_full:
                                return True
                    return False
                filtered = filtered[filtered.apply(lambda r: _player_match(r, selected_player), axis=1)]

            filtered = filtered.sort_values(['period', 'time_remaining'], ascending=[True, False])
            if filtered.empty:
                st.warning('No plays match the selected filters.')
                return

            # ── Play selector label: show context for big moments ────────────
            def _play_label_rich(row):
                down_map_l = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}
                dn   = down_map_l.get(_safe_int(row.get('down'), 0), '?')
                dist_l = _safe_int(row.get('distance'), 0) or '?'
                qtr_l  = f"Q{_safe_int(row.get('period'), 1)}"
                time_l = _fmt_time(row.get('time_remaining'))
                yg     = _safe_int(row.get('yd_gained'), 0)
                ev     = _clean(row.get('event_name'), '')
                td     = row.get('is_td')
                # Badge
                badge = ''
                if str(td).strip() in ('True', '1', '1.0'):
                    badge = ' 🏈'
                elif yg >= 25:
                    badge = f' 💥+{yg}'
                elif str(row.get('event_name', '')).lower().find('intercept') >= 0:
                    badge = ' 🔄'
                elif str(row.get('event_name', '')).lower().find('sack') >= 0:
                    badge = ' 🔨'
                off_nick = _clean(row.get('offensive_team_nickname'), '')
                return f"{qtr_l} {time_l}  ·  {dn} & {dist_l}  ·  {off_nick}{badge}"

            play_map = {int(r['play_unique_id']): _play_label_rich(r) for _, r in filtered.iterrows()}
            selected_pid = st.selectbox(
                f'{len(filtered):,} plays',
                options=list(play_map.keys()),
                format_func=lambda p: play_map[p],
            )
            pid_input = selected_pid
            gc_input  = selected_game
        else:
            pid_input = st.number_input('Play ID', min_value=0, value=2639200, step=1, format='%d')
            gc_input  = st.number_input('Game Code', min_value=0, value=2879291, step=1, format='%d')

        st.markdown('---')
        render_btn = st.button('Render ▶', use_container_width=True)

    if render_btn or 'rendered_pid' not in st.session_state:
        st.session_state['rendered_pid'] = int(pid_input)
        st.session_state['rendered_gc']  = int(gc_input)

    pid = st.session_state['rendered_pid']
    gc  = st.session_state['rendered_gc']

    _data_hash = str(DATA_PATH.stat().st_mtime)
    with st.spinner('Rendering…'):
        try:
            row, df_off, df_def, receiver_name, player_routes, targeted_name, player_ids, play_coverage, player_roles, player_route_dists, events_passer, events_rusher, events_receiver = render_play(
                play_id=pid,
                game_code=gc,
                _hash=_data_hash,
            )
        except Exception as e:
            st.error(f'Could not render play: {e}')
            return

    # ── Recompute yard_line for Plotly ──────────────────────────────────────────
    _yd = row.get('yd_from_goal')
    if pd.notna(_yd):
        _yd_from_goal = int(float(_yd))
        yard_line = 100 - _yd_from_goal if _yd_from_goal > 50 else _yd_from_goal
    else:
        yard_line = 50
    attacking_right = True  # offense always on left, defense on right

    # ── Extract values ────────────────────────────────────────────────────────
    off   = _clean(row.get('offensive_team_nickname'), '—')
    deff  = _clean(row.get('defensive_team_nickname'), '—')
    down_map = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}
    down  = down_map.get(_safe_int(row.get('down'), 0), '—')
    dist  = _safe_int(row.get('distance'), 0)
    _yds_raw = _safe_int(row.get('yd_from_goal'), 0)
    yds   = 100 - _yds_raw if _yds_raw > 50 else _yds_raw  # convert to yard-line label (max 50)
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
            distance=_safe_int(row.get('distance'), 0),
            receiver_name=receiver_name,
            player_routes=player_routes,
            targeted_name=targeted_name,
            player_ids=player_ids,
            play_coverage=play_coverage,
            player_roles=player_roles,
            player_route_dists=player_route_dists,
            targeting_rates=targeting_rates,
            play_type=_clean(row.get('play_type'), ''),
            play_concept=_clean(row.get('play_concept_desc'), ''),
            run_direction=_clean(row.get('initial_run_direction'), ''),
            rusher_name=_clean(row.get('rusher'), ''),
        )
        st.plotly_chart(plotly_fig, use_container_width=True, config={'displayModeBar': False})
        dn   = down_map.get(_safe_int(row.get('down'), 0), 'X')
        fname = f"xInfoViz_{off}_vs_{deff}_{qtr}_{time.replace(':','m')}s_{dn}_and_{dist}.png".replace(' ','_')
        # PNG is generated lazily — only when the button is clicked, not on every render
        st.download_button(
            '⬇  Download PNG',
            data=render_play_png(pid, gc, _data_hash),
            file_name=fname,
            mime='image/png',
        )

    with col_info:
        import math as _math

        # ── Helper: compute season stat ───────────────────────────────────────
        def _sstat(team_col, team_val, filters, metric_col, is_pct=False, zone=None):
            """
            Compute a season stat for a team with optional filters and field zone.
            filters: list of (col, val) tuples
            """
            if not team_val or team_val == '—': return None
            mask = cat[team_col] == team_val
            for fc, fv in (filters or []):
                if fc and fv and str(fv).strip() not in ('—','nan',''):
                    mask &= cat[fc].astype(str).str.strip() == str(fv).strip()
            if zone:
                mask &= cat['yd_from_goal'].apply(_field_zone) == zone
            sub = cat[mask]
            if len(sub) == 0: return None
            if is_pct:
                val = sub[metric_col].apply(lambda v: 1 if str(v).strip() in ('T','True','true','1','1.0') else 0).mean()
            else:
                val = pd.to_numeric(sub[metric_col], errors='coerce').mean()
            return round(val, 3), len(sub)

        def _fmt_stat(result, is_pct=False):
            if result is None: return '—', '—'
            val, n = result
            if isinstance(val, float) and _math.isnan(val): return '—', '—'
            display = f'{val*100:.1f}%' if is_pct else f'{val:.1f} yds'
            return display, f'{n:,} plays'

        this_zone = _field_zone(row.get('yd_from_goal'))
        def_front  = _clean(row.get('defensive_front'), '')
        blitz_flag = _clean(row.get('blitz'), 'F')
        is_blitz   = blitz_flag in ('T','True','true','1')

        # ── Static chips ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="info-panel">
            <div class="chip"><div class="chip-label">Men in Box</div><div class="chip-value">{box}</div></div>
            <div class="chip"><div class="chip-label">Motion</div><div class="chip-value">{motion}</div></div>
            <div class="chip"><div class="chip-label">Play Action</div><div class="chip-value">{pa}</div></div>
            <div class="chip"><div class="chip-label">Snap Hash</div><div class="chip-value">{hash_}</div></div>
            <div class="chip"><div class="chip-label">QB Position</div><div class="chip-value">{_clean(row.get('qb_pos'),'—')}</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:0.3rem"></div>', unsafe_allow_html=True)

        # ── Team colors for popovers ──────────────────────────────────────────
        _off_pri = NFL_TEAM_COLORS.get(str(off).strip(),  {}).get('primary', '#3a6ea5')
        _off_sec = NFL_TEAM_COLORS.get(str(off).strip(),  {}).get('secondary', '#ffffff')
        _def_pri = NFL_TEAM_COLORS.get(str(deff).strip(), {}).get('primary', '#a53a3a')
        _def_sec = NFL_TEAM_COLORS.get(str(deff).strip(), {}).get('secondary', '#ffffff')

        def _pop_card(team_name, color_pri, color_sec, subtitle, rows_html):
            """Render a styled team stat card inside a popover."""
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{color_pri}22,{color_pri}08);
                        border-left:3px solid {color_pri};border-radius:8px;
                        padding:0.75rem 1rem 0.6rem;margin-bottom:0.5rem">
              <div style="font-size:0.95rem;font-weight:800;color:{color_pri};
                          letter-spacing:0.04em;margin-bottom:0.1rem">{team_name}</div>
              <div style="font-size:0.65rem;color:#8888aa;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:0.6rem">{subtitle}</div>
              {rows_html}
            </div>""", unsafe_allow_html=True)

        def _pop_row(label, value, note=''):
            note_html = f' <span style="font-size:0.65rem;color:#666688;font-style:italic">{note}</span>' if note else ''
            return (f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                    f'padding:0.2rem 0;border-bottom:1px solid #ffffff0d">'
                    f'<span style="font-size:0.72rem;color:#aaaacc">{label}</span>'
                    f'<span style="font-size:0.82rem;font-weight:700;color:#ffffff">{value}{note_html}</span>'
                    f'</div>')

        # ── Popover 1: Defensive Front ────────────────────────────────────────
        with st.popover(f'🛡 Def. Front: {front}', use_container_width=True):
            r1 = _sstat('offensive_team_nickname', off, [('defensive_front', front)], 'yd_gained')
            r3 = _sstat('offensive_team_nickname', off, [('defensive_front', front)], 'success_play', is_pct=True)
            r4 = _sstat('offensive_team_nickname', off, [('defensive_front', front)], 'is_first_down', is_pct=True)
            off_rows = (
                _pop_row('Avg Yards (season)', _fmt_stat(r1)[0], _fmt_stat(r1)[1]) +
                _pop_row('Success Rate',       _fmt_stat(r3, is_pct=True)[0]) +
                _pop_row('1st Down Rate',      _fmt_stat(r4, is_pct=True)[0])
            )
            _pop_card(off, _off_pri, _off_sec, f'vs {front} — 2026 Season', off_rows)

            d1 = _sstat('defensive_team_nickname', deff, [('defensive_front', front)], 'yd_gained')
            d2 = _sstat('defensive_team_nickname', deff, [('defensive_front', front)], 'success_play', is_pct=True)
            def_rows = (
                _pop_row('Avg Yds Allowed',      _fmt_stat(d1)[0], _fmt_stat(d1)[1]) +
                _pop_row('Success Rate Allowed', _fmt_stat(d2, is_pct=True)[0])
            )
            _pop_card(deff, _def_pri, _def_sec, f'{front} defense — 2026 Season', def_rows)

        # ── Popover 2: Formation + Personnel ─────────────────────────────────
        with st.popover(f'📋 {form} · {off_p}', use_container_width=True):
            filters = [('offensive_formation', form), ('offensive_personnel', off_p)]
            r1  = _sstat('offensive_team_nickname', off, filters, 'yd_gained')
            r3  = _sstat('offensive_team_nickname', off, filters, 'success_play', is_pct=True)
            r4  = _sstat('offensive_team_nickname', off, filters, 'is_first_down', is_pct=True)
            fp2_rows = (
                _pop_row('Avg Yards (season)', _fmt_stat(r1)[0], _fmt_stat(r1)[1]) +
                _pop_row('Success Rate',       _fmt_stat(r3, is_pct=True)[0]) +
                _pop_row('1st Down Rate',      _fmt_stat(r4, is_pct=True)[0])
            )
            _pop_card(off, _off_pri, _off_sec, f'{form} / {off_p} — 2026 Season', fp2_rows)

        # ── Popover 3: Coverage ───────────────────────────────────────────────
        cov_desc = _clean(row.get('coverage_concept_desc'), '—')
        if cov_desc and cov_desc != '—':
            with st.popover(f'👁 Coverage: {cov_desc}', use_container_width=True):
                c1 = _sstat('offensive_team_nickname', off,  [('coverage_concept_desc', cov_desc)], 'yd_gained')
                c3 = _sstat('offensive_team_nickname', off,  [('coverage_concept_desc', cov_desc)], 'success_play', is_pct=True)
                c4 = _sstat('offensive_team_nickname', off,  [('coverage_concept_desc', cov_desc)], 'is_first_down', is_pct=True)
                cov_off_rows = (
                    _pop_row('Avg Yards (season)', _fmt_stat(c1)[0], _fmt_stat(c1)[1]) +
                    _pop_row('Success Rate',       _fmt_stat(c3, is_pct=True)[0]) +
                    _pop_row('1st Down Rate',      _fmt_stat(c4, is_pct=True)[0])
                )
                _pop_card(off, _off_pri, _off_sec, f'vs {cov_desc} — 2026 Season', cov_off_rows)

                d1 = _sstat('defensive_team_nickname', deff, [('coverage_concept_desc', cov_desc)], 'yd_gained')
                d2 = _sstat('defensive_team_nickname', deff, [('coverage_concept_desc', cov_desc)], 'success_play', is_pct=True)
                cov_def_rows = (
                    _pop_row('Avg Yds Allowed',      _fmt_stat(d1)[0], _fmt_stat(d1)[1]) +
                    _pop_row('Success Rate Allowed', _fmt_stat(d2, is_pct=True)[0])
                )
                _pop_card(deff, _def_pri, _def_sec, f'{cov_desc} coverage — 2026 Season', cov_def_rows)
        else:
            st.markdown(f"""
            <div class="chip" style="margin-bottom:0.2rem">
                <div class="chip-label">Coverage</div>
                <div class="chip-value">{cov_desc}</div>
            </div>""", unsafe_allow_html=True)

        # ── Blitz: chip when no blitz, popover when blitz ────────────────────
        if not is_blitz:
            st.markdown("""
            <div class="chip" style="margin-bottom:0.2rem">
                <div class="chip-label">Blitz</div>
                <div class="chip-value">No</div>
            </div>""", unsafe_allow_html=True)
        if is_blitz:
            game_code_val = _safe_int(row.get('game_code'), 0)
            with st.popover('⚡ Blitz: Yes', use_container_width=True):
                r_off   = _sstat('offensive_team_nickname', off,  [('blitz', 'T')], 'yd_gained')
                r_def   = _sstat('defensive_team_nickname', deff, [('blitz', 'T')], 'yd_gained')
                r_off_g = _sstat('offensive_team_nickname', off,
                                  [('blitz', 'T'), ('game_code', str(game_code_val))], 'yd_gained')
                r_def_g = _sstat('defensive_team_nickname', deff,
                                  [('blitz', 'T'), ('game_code', str(game_code_val))], 'yd_gained')
                off_s,  off_n  = _fmt_stat(r_off)
                def_s,  def_n  = _fmt_stat(r_def)
                off_g,  off_gn = _fmt_stat(r_off_g)
                def_g,  def_gn = _fmt_stat(r_def_g)
                blitz_off_rows = (
                    _pop_row('Avg Yards vs Blitz (season)', off_s, off_n) +
                    _pop_row('Avg Yards vs Blitz (this game)', off_g, off_gn)
                )
                _pop_card(off, _off_pri, _off_sec, 'Offense vs Blitz', blitz_off_rows)
                blitz_def_rows = (
                    _pop_row('Avg Yds Allowed when Blitzing (season)', def_s, def_n) +
                    _pop_row('Avg Yds Allowed when Blitzing (this game)', def_g, def_gn)
                )
                _pop_card(deff, _def_pri, _def_sec, 'Defense — Blitz Stats', blitz_def_rows)
    # ── Play narrative + insight badge ───────────────────────────────────────
    def _to_full_name(raw):
        """'Last, First' → 'First Last'. Pass-through for already-formatted names."""
        s = str(raw or '').strip()
        if not s or s in ('nan', '—', ''):
            return ''
        if ',' in s:
            parts = [p.strip() for p in s.split(',', 1)]
            return f"{parts[1]} {parts[0]}" if len(parts) == 2 else s
        return s

    def _name_from_roster(r, roles_set):
        """Scan off_1..11 for first player matching any role in roles_set."""
        for i in range(1, 12):
            if str(r.get(f'off_{i}_role', '')).strip() in roles_set:
                fn = str(r.get(f'off_{i}_player_first_name', '') or '').strip()
                ln = str(r.get(f'off_{i}_player_last_name', '') or '').strip()
                if fn and ln:
                    return f"{fn} {ln}"
        return ''

    def _qb_name_from_roster(r):
        return _name_from_roster(r, {'QB'})

    def _rb_name_from_roster(r):
        return _name_from_roster(r, {'RBL', 'RBM', 'RBR', 'FBL', 'FBM', 'FBR'})

    def _build_narrative(r, _targeted=None, _evt_passer='', _evt_rusher='', _evt_receiver=''):
        ev       = _clean(r.get('event_name'), '')
        # Priority: events file → catalog col → roster fallback
        passer_n = (_evt_passer
                    or _to_full_name(r.get('passer', ''))
                    or _qb_name_from_roster(r))
        recv_n   = (_evt_receiver
                    or _to_full_name(r.get('receiver', '')))
        rush_n   = (_evt_rusher
                    or _to_full_name(r.get('rusher', ''))
                    or _rb_name_from_roster(r))
        yg       = _safe_int(r.get('yd_gained'), 0)
        is_td_v  = str(r.get('is_td', '')).strip() in ('True', '1', '1.0', 'T')
        air      = _safe_int(r.get('air_yds'), None)
        yac      = _safe_int(r.get('yd_after_catch'), None)
        direction = _clean(r.get('initial_run_direction'), '')
        ev_low   = ev.lower()
        _dir_map  = {'l': 'left', 'r': 'right', 'ls': 'left', 'rs': 'right', 'm': 'middle'}
        direction = _dir_map.get(direction.lower(), direction)
        bt_n     = _safe_int(r.get('broken_tackles', 0), 0) or 0
        bt_str   = (f', breaking {bt_n} tackle{"s" if bt_n != 1 else ""}' if bt_n >= 1 else '')

        td_tag = ' for a <strong>TOUCHDOWN</strong>' if is_td_v else ''

        if 'incomplete' in ev_low or 'incomplet' in ev_low:
            if passer_n and recv_n:
                return f"{passer_n} throws incomplete to {recv_n}."
            elif passer_n:
                return f"{passer_n} throws incomplete."
            return "Incomplete pass."

        if 'intercept' in ev_low:
            if passer_n and recv_n:
                return f"{passer_n}'s pass intended for {recv_n} is <strong>intercepted</strong>."
            elif passer_n:
                return f"{passer_n}'s pass is <strong>intercepted</strong>."
            return "Pass intercepted."

        if 'sack' in ev_low:
            if passer_n:
                return f"{passer_n} is <strong>sacked</strong> for a loss of {abs(yg)} yard{'s' if abs(yg) != 1 else ''}."
            return f"Quarterback sacked for {abs(yg)} yard{'s' if abs(yg) != 1 else ''}."

        if 'completion' in ev_low or ('pass' in ev_low and 'complete' in ev_low):
            details = []
            if air is not None:
                details.append(f"{air} air yds")
            if yac is not None:
                details.append(f"{yac} YAC")
            detail_str = f" ({', '.join(details)})" if details else ''
            if passer_n and recv_n:
                return f"{passer_n} completes a {yg}-yard pass to {recv_n}{detail_str}{bt_str}{td_tag}."
            elif passer_n:
                return f"{passer_n} completes a {yg}-yard pass{detail_str}{bt_str}{td_tag}."
            return f"{yg}-yard pass completion{bt_str}{td_tag}."

        if 'scramble' in ev_low or str(r.get('play_type', '')).lower() == 'scramble':
            nm = passer_n or rush_n
            dir_str = f" {direction.lower()}" if direction and direction not in ('—', '') else ''
            if nm:
                return f"{nm} scrambles{dir_str} for {yg} yard{'s' if yg != 1 else ''}{bt_str}{td_tag}."
            return f"Quarterback scramble for {yg} yard{'s' if yg != 1 else ''}{bt_str}{td_tag}."

        # run play
        nm = rush_n or passer_n
        dir_str = f" {direction.lower()}" if direction and direction not in ('—', '') else ''
        if nm:
            return f"{nm} runs{dir_str} for {yg} yard{'s' if yg != 1 else ''}{bt_str}{td_tag}."
        return f"Run play for {yg} yard{'s' if yg != 1 else ''}{bt_str}{td_tag}."

    def _build_badge(r):
        """Return (label, color) for the most interesting thing, or (None, None)."""
        yg       = _safe_int(r.get('yd_gained'), 0)
        is_td_v  = str(r.get('is_td', '')).strip() in ('True', '1', '1.0', 'T')
        ev_low   = _clean(r.get('event_name'), '').lower()
        down_v   = _safe_int(r.get('down'), 0)
        ifd      = str(r.get('is_first_down', '')).strip() in ('T', 'True', '1', '1.0')
        bt       = _safe_int(r.get('broken_tackles', 0), 0) or 0
        blitz_v  = str(r.get('blitz', '')).strip() in ('T', 'True', '1')
        pa_v     = str(r.get('play_action', '')).strip() in ('Y', 'J', 'P', 'E')
        open_v   = str(r.get('was_receiver_open', '')).strip()
        pocket_v = _clean(r.get('pocket_detail'), '')
        cov_v    = _clean(r.get('coverage_concept_desc'), '')

        # Priority trickle-down
        if is_td_v:
            return '🏈 Touchdown', '#1a7a1a'
        if yg >= 25:
            return f'💥 Big Gain — +{yg} yards', '#0d5fa8'
        if 'intercept' in ev_low:
            return '🔄 Interception', '#8b0000'
        if 'sack' in ev_low:
            return '🔨 Sack', '#7a5500'
        if down_v in (3, 4) and ifd:
            ord_map = {3:'3rd', 4:'4th'}
            return f'✅ {ord_map.get(down_v,"")} Down Conversion', '#1a5c2e'
        if bt >= 2:
            return f'💪 {bt} Broken Tackles', '#5a3080'
        if bt == 1:
            return '💪 Broken Tackle', '#5a3080'
        if blitz_v and yg > 0:
            return f'⚡ Beat the Blitz — +{yg} yds', '#0d5fa8'
        if blitz_v and yg <= 0:
            return '⚡ Blitz Got There', '#7a5500'
        if pa_v:
            return '🎭 Play Action', '#3a5580'
        if open_v == 'Y':
            return '👁 Receiver Open', '#1a5c2e'
        if open_v == 'N':
            return '🛡 Receiver Covered', '#6a1a1a'
        if pocket_v and pocket_v not in ('—', ''):
            return f'📦 {pocket_v}', '#3a3a5a'
        if cov_v and cov_v not in ('—', ''):
            return f'🎯 {cov_v}', '#3a3a5a'
        return None, None

    _narrative_html = _build_narrative(
        row,
        _targeted=targeted_name,
        _evt_passer=events_passer,
        _evt_rusher=events_rusher,
        _evt_receiver=events_receiver,
    )
    _badge_label, _badge_color = _build_badge(row)

    _badge_color_display = '#4caf80' if _badge_color == '#1a7a1a' else (_badge_color or '#ff6b00')
    _badge_bg    = f"{_badge_color_display}22" if _badge_label else ''
    _badge_border= f"{_badge_color_display}55" if _badge_label else ''

    if _badge_label:
        _badge_html = (
            '<div style="margin-top:0.5rem">'
            f'<span style="display:inline-block;background:{_badge_bg};'
            f'color:{_badge_color_display};'
            f'border:1px solid {_badge_border};'
            'border-radius:20px;padding:0.3rem 0.85rem;'
            'font-size:0.82rem;font-weight:700;letter-spacing:0.02em">'
            f'{_badge_label}'
            '</span></div>'
        )
    else:
        _badge_html = ''

    _strip_html = (
        '<div style="margin:1.1rem 0 0.4rem;padding:1rem 1.25rem;'
        'background:rgba(255,255,255,0.03);border-radius:10px;'
        'border-left:3px solid #ff6b00">'
        f'<div style="font-size:1.05rem;font-weight:600;color:#e8e8f0;line-height:1.4">{_narrative_html}</div>'
        f'{_badge_html}'
        '</div>'
    )
    st.markdown(_strip_html, unsafe_allow_html=True)

    # clear any stale session state from old debug expander
    st.session_state.pop('_evt_debug', None)
    st.session_state.pop('_evt_load_error', None)


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

        # Team-filtered similar plays (same conditions, offensive team only)
        team_sim_df = sim_df[sim_df['offensive_team_nickname'] == off] if 'offensive_team_nickname' in sim_df.columns else sim_df.iloc[0:0]
        n_team_sim  = len(team_sim_df)

        def _team_pct_col(col):
            if col not in team_sim_df.columns or n_team_sim == 0: return float('nan')
            return team_sim_df[col].apply(lambda v: 1 if str(v).strip() in ('True','1','T','true','1.0') else 0).mean()

        # League actual outcomes
        actual_avg_yds    = sim_df['yd_gained'].mean()    if 'yd_gained'    in sim_df.columns else float('nan')
        actual_td_rate    = _pct_col('is_td')
        actual_first_down = _pct_col('is_first_down')
        actual_success    = sim_df['success_play'].mean() if 'success_play' in sim_df.columns else float('nan')
        actual_explosive  = _pct_col('explosive')

        # Team actual outcomes
        team_avg_yds    = team_sim_df['yd_gained'].mean()    if 'yd_gained'    in team_sim_df.columns and n_team_sim > 0 else float('nan')
        team_td_rate    = _team_pct_col('is_td')
        team_first_down = _team_pct_col('is_first_down')
        team_success    = team_sim_df['success_play'].mean() if 'success_play' in team_sim_df.columns and n_team_sim > 0 else float('nan')
        team_explosive  = _team_pct_col('explosive')

        # This play actual values
        this_play_type  = _clean(row.get('play_type'), '—')
        this_yd_gained  = _safe_float(row.get('yd_gained'),  float('nan'))
        this_is_td      = _yn(row.get('is_td', 'F'))
        this_first_down = _yn(row.get('is_first_down', 'F'))
        this_success    = _yn(row.get('success_play', 0))
        this_explosive  = _yn(row.get('explosive', 0))


        # Actual outcome rows — binary fields show Yes/No for this play, % for similar avg
        # Play Type has no similar avg comparison
        play_type_row = f"""
            <tr>
                <td style="color:#aaaacc">Play Type</td>
                <td class="sim-this">{this_play_type}</td>
                <td style="color:#aaaacc">—</td>
                <td style="color:#aaaacc">—</td>
            </tr>"""

        outcome_rows = (
            play_type_row +
            _sim_row_html('Yards Gained', this_yd_gained,  team_avg_yds,   actual_avg_yds,    _fmt_yds(this_yd_gained), _fmt_yds(team_avg_yds),   _fmt_yds(actual_avg_yds),   higher_is_better=True) +
            _sim_row_html('Touchdown',    1 if this_is_td=='Yes' else 0,    team_td_rate,      actual_td_rate,    this_is_td,  _fmt_pct(team_td_rate),   _fmt_pct(actual_td_rate),   higher_is_better=True) +
            _sim_row_html('1st Down',     1 if this_first_down=='Yes' else 0, team_first_down, actual_first_down, this_first_down, _fmt_pct(team_first_down), _fmt_pct(actual_first_down), higher_is_better=True) +
            _sim_row_html('Success',      1 if this_success=='Yes' else 0,  team_success,      actual_success,    this_success, _fmt_pct(team_success),   _fmt_pct(actual_success),   higher_is_better=True) +
            _sim_row_html('Explosive',    1 if this_explosive=='Yes' else 0, team_explosive,   actual_explosive,  this_explosive, _fmt_pct(team_explosive), _fmt_pct(actual_explosive), higher_is_better=True)
        )

        act_header = '<tr><td colspan="4" style="color:#ff6b00;font-weight:700;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;padding-top:0.6rem;border:none">Actual Outcomes</td></tr>'

        rows_html = act_header + outcome_rows

        team_sim_note = f' · <b style="color:{_off_pri}">{off}: {n_team_sim:,} plays</b>' if n_team_sim > 0 else ''

        st.markdown(f"""
        <div class="sim-box">
            <div class="sim-title">Similar Play Tendencies{fallback_note}</div>
            <div class="sim-subtitle">
                {form} · {off_p} · {down_label} &amp; {dist_label} · {zone_label}
                &nbsp;·&nbsp; <b style="color:#ffffff">{n_sim:,} league plays</b>{team_sim_note}
            </div>
            <table class="sim-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>This Play</th>
                        <th style="color:{_off_pri}">{off} Avg</th>
                        <th>League Avg</th>
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