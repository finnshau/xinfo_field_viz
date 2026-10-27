"""
xInfoViz Offensive Formation Mapper
====================================
Rule-based placement of offensive players onto a 2D field.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# FIELD CONSTANTS
# ============================================================================

FIELD_WIDTH_FT = 160
CENTER_Y = FIELD_WIDTH_FT / 2
LOS_X = 0
OL_STEP = 5
TE_STEP = 5

QB_DEPTH = {'N': -2.0, 'P': -12.0, 'S': -15.0}
RB_DEPTH = {'N': -21.0, 'P': -21.0, 'S': -15.0}
RB_LATERAL_STEP = 4.0
FB_DEPTH_NORMAL = -14.0
FB_DEPTH_PISTOL_SIDE = -15.0
FB_DEPTH_PISTOL_MID = -17.5
FB_DEPTH_SHOTGUN = -13.0
FB_LATERAL = 5.0

# ============================================================================
# ROLE CLASSIFICATION
# ============================================================================

OL_ROLES_ORDERED = ['C', 'LG', 'LT', 'RG', 'RT']

TE_ROLE_CODES = {
    'LTE', 'LIT', 'LW', 'LIW', 'PAL', 'PBL',
    'RTE', 'RIT', 'RW', 'RIW', 'PAR', 'PBR',
}

WR_ROLE_CODES = {
    'LOR', 'LSR', 'LIR', 'LIIR', 'LIIIR',
    'ROR', 'RSR', 'RIR', 'RIIR', 'RIIIR',
}

RB_ROLE_CODES = {'RBL', 'RBR', 'RBM', 'SBL', 'SBR', 'VSF'}
FB_ROLE_CODES = {'FBL', 'FBR', 'FBM'}

WR_SUFFIX_RANK = {'OR': 0, 'SR': 1, 'IR': 2, 'IIR': 3, 'IIIR': 4}


def _is_valid_number(value) -> bool:
    if pd.isna(value):
        return False
    try:
        int(float(value))
        return True
    except (TypeError, ValueError):
        return False


def _placeholder_row(role, number, name, reason: str) -> dict:
    return {
        'player_number': number, 'player_name': name, 'role': role,
        'x_ft': 0.0, 'y_ft': 0.0, 'is_uncertain': True, 'uncertain_reason': reason,
    }


def _ensure_eleven_players(df_coords: pd.DataFrame) -> pd.DataFrame:
    if len(df_coords) > 11:
        return df_coords.iloc[:11].reset_index(drop=True)
    if len(df_coords) < 11:
        missing = 11 - len(df_coords)
        placeholders = [_placeholder_row('UNK', '?', 'Placeholder', 'auto-pad-to-11') for _ in range(missing)]
        return pd.concat([df_coords, pd.DataFrame(placeholders)], ignore_index=True)
    return df_coords.reset_index(drop=True)


def wr_suffix_rank(role_code: str) -> int:
    return WR_SUFFIX_RANK.get(role_code[1:], 99)


def role_side(role_code: str) -> str:
    code = str(role_code).strip().upper()
    if code in {'RBL', 'FBL', 'SBL', 'PAL', 'PBL'}: return 'L'
    if code in {'RBR', 'FBR', 'SBR', 'PAR', 'PBR'}: return 'R'
    if code.startswith('L'): return 'L'
    if code.startswith('R'): return 'R'
    return 'M'


def normalize_qb_pos(raw) -> str:
    if pd.isna(raw) or not str(raw).strip(): return 'S'
    first = str(raw).strip().upper()[0]
    return first if first in QB_DEPTH else 'S'


def ol_y_positions() -> dict:
    return {
        'C':  CENTER_Y,
        'LG': CENTER_Y + OL_STEP,
        'LT': CENTER_Y + 2 * OL_STEP,
        'RG': CENTER_Y - OL_STEP,
        'RT': CENTER_Y - 2 * OL_STEP,
    }


# ============================================================================
# CORE MAPPER
# ============================================================================

def map_offense_to_coordinates(role_list, number_list, name_list, qb_pos='S'):
    qb_mode = normalize_qb_pos(qb_pos)
    players = []
    for role, number, name in zip(role_list, number_list, name_list):
        if pd.isna(role): continue
        rc = str(role).strip()
        if not rc or rc.lower() == 'nan': continue
        players.append({'role': rc, 'number': number, 'name': str(name).strip(),
                        'number_uncertain': not _is_valid_number(number)})

    coords = []
    uncertain_rows = []
    ol_y = ol_y_positions()
    OL_X = LOS_X - 3.0

    for p in players:
        if p['number_uncertain']:
            uncertain_rows.append(_placeholder_row(p['role'], '?', p['name'], 'uncertain-number'))

    for p in players:
        if p['number_uncertain']: continue
        if p['role'] in ol_y:
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                           'role': p['role'], 'x_ft': OL_X, 'y_ft': ol_y[p['role']],
                           'is_uncertain': False, 'uncertain_reason': ''})

    placed_ys_left  = [c['y_ft'] for c in coords if role_side(c['role']) in ('L','M') and c['role'] in ol_y]
    placed_ys_right = [c['y_ft'] for c in coords if role_side(c['role']) in ('R','M') and c['role'] in ol_y]
    lt_y = max(placed_ys_left)  if placed_ys_left  else CENTER_Y + 2*OL_STEP
    rt_y = min(placed_ys_right) if placed_ys_right else CENTER_Y - 2*OL_STEP

    left_tes  = [p for p in players if not p['number_uncertain'] and p['role'] in TE_ROLE_CODES and role_side(p['role']) in ('L','M')]
    right_tes = [p for p in players if not p['number_uncertain'] and p['role'] in TE_ROLE_CODES and role_side(p['role']) == 'R']

    for i, p in enumerate(left_tes):
        coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                       'x_ft': OL_X, 'y_ft': lt_y + TE_STEP*(i+1), 'is_uncertain': False, 'uncertain_reason': ''})
    for i, p in enumerate(right_tes):
        coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                       'x_ft': OL_X, 'y_ft': rt_y - TE_STEP*(i+1), 'is_uncertain': False, 'uncertain_reason': ''})

    all_placed_ys = [c['y_ft'] for c in coords]
    left_edge  = max(all_placed_ys) if all_placed_ys else CENTER_Y
    right_edge = min(all_placed_ys) if all_placed_ys else CENTER_Y

    left_wrs  = sorted([p for p in players if not p['number_uncertain'] and p['role'] in WR_ROLE_CODES and role_side(p['role'])=='L'], key=lambda p: wr_suffix_rank(p['role']))
    right_wrs = sorted([p for p in players if not p['number_uncertain'] and p['role'] in WR_ROLE_CODES and role_side(p['role'])=='R'], key=lambda p: wr_suffix_rank(p['role']))

    if left_wrs:
        step = (FIELD_WIDTH_FT - left_edge) / (len(left_wrs)+1)
        for i, p in enumerate(left_wrs, start=1):
            coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                           'x_ft': OL_X, 'y_ft': FIELD_WIDTH_FT-(step*i), 'is_uncertain': False, 'uncertain_reason': ''})
    if right_wrs:
        step = right_edge / (len(right_wrs)+1)
        for i, p in enumerate(right_wrs, start=1):
            coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                           'x_ft': OL_X, 'y_ft': step*i, 'is_uncertain': False, 'uncertain_reason': ''})

    for p in players:
        if p['number_uncertain']: continue
        if p['role'] == 'QB':
            coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': 'QB',
                           'x_ft': QB_DEPTH[qb_mode], 'y_ft': CENTER_Y, 'is_uncertain': False, 'uncertain_reason': ''})

    rb_side_count = {'L': 0, 'R': 0}
    for p in players:
        if p['number_uncertain']: continue
        if p['role'] not in RB_ROLE_CODES: continue
        side = role_side(p['role'])
        x = RB_DEPTH[qb_mode]
        if qb_mode == 'S':
            if side == 'L': rb_side_count['L'] += 1; y = CENTER_Y + RB_LATERAL_STEP*rb_side_count['L']
            elif side == 'R': rb_side_count['R'] += 1; y = CENTER_Y - RB_LATERAL_STEP*rb_side_count['R']
            else: y = CENTER_Y
        else:
            y = CENTER_Y+5 if side=='L' else (CENTER_Y-5 if side=='R' else CENTER_Y)
        coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                       'x_ft': x, 'y_ft': y, 'is_uncertain': False, 'uncertain_reason': ''})

    for p in players:
        if p['number_uncertain']: continue
        if p['role'] not in FB_ROLE_CODES: continue
        side = role_side(p['role'])
        if qb_mode == 'N':
            x = FB_DEPTH_NORMAL
            y = CENTER_Y+FB_LATERAL if side=='L' else (CENTER_Y-FB_LATERAL if side=='R' else CENTER_Y)
        elif qb_mode == 'P':
            if side == 'M': x = FB_DEPTH_PISTOL_MID; y = CENTER_Y
            else: x = FB_DEPTH_PISTOL_SIDE; y = CENTER_Y+FB_LATERAL if side=='L' else CENTER_Y-FB_LATERAL
        else:
            x = FB_DEPTH_SHOTGUN
            y = CENTER_Y+FB_LATERAL if side=='L' else (CENTER_Y-FB_LATERAL if side=='R' else CENTER_Y)
        coords.append({'player_number': p['number'], 'player_name': p['name'], 'role': p['role'],
                       'x_ft': x, 'y_ft': y, 'is_uncertain': False, 'uncertain_reason': ''})

    placed_roles = {c['role'] for c in coords}
    for p in players:
        if p['number_uncertain']: continue
        if p['role'] not in placed_roles:
            uncertain_rows.append(_placeholder_row(p['role'], p['number'], p['name'], 'unrecognized-role'))

    df_coords = pd.concat([pd.DataFrame(coords), pd.DataFrame(uncertain_rows)], ignore_index=True)
    return _ensure_eleven_players(df_coords)


def map_defense_to_coordinates(role_list, number_list, name_list, press_list, ol_coords):
    def get_y(role):
        rows = ol_coords[ol_coords['role'] == role]
        return float(rows['y_ft'].iloc[0]) if not rows.empty else None

    C_y   = get_y('C')  or 80.0
    LG_y  = get_y('LG') or 85.0
    LT_y  = get_y('LT') or 90.0
    RG_y  = get_y('RG') or 75.0
    RT_y  = get_y('RT') or 70.0
    LOR_y = get_y('LOR')
    ROR_y = get_y('ROR')
    LSR_y = get_y('LSR')
    RSR_y = get_y('RSR')
    LIR_y = get_y('LIR')
    RIR_y = get_y('RIR')

    players = []
    for role, number, name, press in zip(role_list, number_list, name_list, press_list):
        if pd.isna(role) or str(role).strip() in ('', 'nan'): continue
        players.append({'role': str(role).strip(), 'number': number,
                        'name': str(name).strip(), 'press': int(press) if not pd.isna(press) else 0})

    coords = []
    for p in players:
        role = p['role']
        press = p['press']
        base_role = role[:-1] if role.lower().endswith('m') else role
        x = y = None
        DL_X = 3

        if base_role in ('0T','NOSE','0'):    x,y = DL_X, C_y
        elif base_role == '1L':               x,y = DL_X, (C_y+RG_y)/2
        elif base_role == '1R':               x,y = DL_X, (C_y+LG_y)/2
        elif base_role == '2iL':              x,y = DL_X, RG_y+1
        elif base_role == '2iR':              x,y = DL_X, LG_y-1
        elif base_role == '2L':               x,y = DL_X, RG_y
        elif base_role == '2R':               x,y = DL_X, LG_y
        elif base_role == '3L':               x,y = DL_X, (RG_y+RT_y)/2
        elif base_role == '3R':               x,y = DL_X, (LG_y+LT_y)/2
        elif base_role == '4iL':              x,y = DL_X, RT_y+1
        elif base_role == '4iR':              x,y = DL_X, LT_y-1
        elif base_role == '4L':               x,y = DL_X, RT_y
        elif base_role == '4R':               x,y = DL_X, LT_y
        elif base_role == '5L':               x,y = DL_X, RT_y-2
        elif base_role == '5R':               x,y = DL_X, LT_y+2
        elif base_role == '5Lw':              x,y = DL_X, RT_y-5
        elif base_role == '5Rw':              x,y = DL_X, LT_y+5
        elif base_role == '6L':               x,y = DL_X, RT_y-8
        elif base_role == '6R':               x,y = DL_X, LT_y+8
        elif base_role == '7L':               x,y = DL_X, RT_y-10
        elif base_role == '7R':               x,y = DL_X, LT_y+10
        elif base_role == '9L':               x,y = DL_X, RT_y-12
        elif base_role == '9R':               x,y = DL_X, LT_y+12
        elif base_role == '9Lw':              x,y = DL_X, RT_y-15
        elif base_role == '9Rw':              x,y = DL_X, LT_y+15
        elif base_role == 'MLB':              x,y = 20, C_y
        elif base_role == 'LILB':             x,y = 17, (RT_y+RG_y)/2
        elif base_role == 'RILB':             x,y = 17, (LT_y+LG_y)/2
        elif base_role == 'RLB':              x,y = 17, LT_y+5
        elif base_role == 'LLB':              x,y = 17, RT_y-5
        elif base_role == 'ROLB':             x,y = 17, LT_y+8
        elif base_role == 'LOLB':             x,y = 17, RT_y-8
        elif base_role == 'LSS':              x,y = 24, RT_y-3
        elif base_role == 'RSS':              x,y = 24, LT_y+3
        elif base_role == 'MSS':              x,y = 24, C_y
        elif base_role == 'MS':               x,y = 38, C_y
        elif base_role == 'LS':               x,y = 47, 40
        elif base_role == 'RS':               x,y = 47, 120
        elif base_role == 'CF':               x,y = 56, C_y
        elif base_role == 'LOC':              x=26; y=ROR_y if ROR_y is not None else RT_y-20
        elif base_role == 'ROC':              x=26; y=LOR_y if LOR_y is not None else LT_y+20
        elif base_role == 'LSC':              x=20; y=RSR_y if RSR_y is not None else RT_y-15
        elif base_role == 'RSC':              x=20; y=LSR_y if LSR_y is not None else LT_y+15
        elif base_role == 'LIC':              x=20; y=RIR_y if RIR_y is not None else RT_y-10
        elif base_role == 'RIC':              x=20; y=LIR_y if LIR_y is not None else LT_y+10
        elif base_role == 'LIIC':             x,y = 20, RT_y-8
        elif base_role == 'RIIC':             x,y = 20, LT_y+8
        else:                                 x,y = 20, C_y

        if press == 1: x = 4
        coords.append({'player_number': p['number'], 'player_name': p['name'],
                       'role': role, 'x_ft': float(x), 'y_ft': float(y), 'press': press})
    return pd.DataFrame(coords)


# ============================================================================
# VISUALIZATION — legacy
# ============================================================================

def plot_offense(df_coords, title="Offensive Formation"):
    fig, ax = plt.subplots(figsize=(4.8, 8.2))
    ax.set_facecolor('#2f7a34')
    fig.patch.set_facecolor('#2f7a34')
    ax.axvline(LOS_X, color='white', linewidth=2.4, zorder=1)
    ax.scatter(df_coords['x_ft'], df_coords['y_ft'], s=250, c='#7c4ec8',
               edgecolors='#f0b54a', linewidths=1.8, zorder=3)
    for _, row in df_coords.iterrows():
        try: num = int(float(row['player_number']))
        except: num = '?'
        ax.text(row['x_ft'], row['y_ft'], str(num), ha='center', va='center',
                fontsize=8, fontweight='bold', color='white', zorder=4)
    ax.set_xlim(-23, 3); ax.set_ylim(0, FIELD_WIDTH_FT)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.set_title(title, fontsize=13, color='white', fontweight='bold', pad=8)
    plt.tight_layout()
    return fig, ax


# ============================================================================
# NFL TEAM COLOR PALETTE
# ============================================================================

NFL_TEAM_COLORS = {
    '49ers':      {'primary': '#AA0000', 'secondary': '#B3995D'},
    'Bears':      {'primary': '#0B162A', 'secondary': '#C83803'},
    'Bengals':    {'primary': '#FB4F14', 'secondary': '#000000'},
    'Bills':      {'primary': '#00338D', 'secondary': '#C60C30'},
    'Broncos':    {'primary': '#FB4F14', 'secondary': '#002244'},
    'Browns':     {'primary': '#311D00', 'secondary': '#FF3C00'},
    'Buccaneers': {'primary': '#D50A0A', 'secondary': '#FF7900'},
    'Cardinals':  {'primary': '#97233F', 'secondary': '#FFB612'},
    'Chargers':   {'primary': '#002A5E', 'secondary': '#FFC20E'},
    'Chiefs':     {'primary': '#E31837', 'secondary': '#FFB81C'},
    'Colts':      {'primary': '#003A70', 'secondary': '#A2AAAD'},
    'Commanders': {'primary': '#5A1414', 'secondary': '#FFB612'},
    'Cowboys':    {'primary': '#003594', 'secondary': '#869397'},
    'Dolphins':   {'primary': '#008E97', 'secondary': '#FC4C02'},
    'Eagles':     {'primary': '#004C54', 'secondary': '#A5ACAF'},
    'Falcons':    {'primary': '#A71930', 'secondary': '#000000'},
    'Giants':     {'primary': '#0B2265', 'secondary': '#A71930'},
    'Jaguars':    {'primary': '#006778', 'secondary': '#9F792C'},
    'Jets':       {'primary': '#125740', 'secondary': '#FFFFFF'},
    'Lions':      {'primary': '#0076B6', 'secondary': '#B0B7BC'},
    'Packers':    {'primary': '#203731', 'secondary': '#FFB612'},
    'Panthers':   {'primary': '#0085CA', 'secondary': '#101820'},
    'Patriots':   {'primary': '#002244', 'secondary': '#C60C30'},
    'Raiders':    {'primary': '#000000', 'secondary': '#A5ACAF'},
    'Rams':       {'primary': '#003594', 'secondary': '#FFA300'},
    'Ravens':     {'primary': '#241773', 'secondary': '#000000'},
    'Saints':     {'primary': '#101820', 'secondary': '#D3BC8D'},
    'Seahawks':   {'primary': '#002244', 'secondary': '#69BE28'},
    'Steelers':   {'primary': '#101820', 'secondary': '#FFB612'},
    'Texans':     {'primary': '#03202F', 'secondary': '#A71930'},
    'Titans':     {'primary': '#0C2340', 'secondary': '#4B92DB'},
    'Vikings':    {'primary': '#4F2683', 'secondary': '#FFC62F'},
}

_DEFAULT_OFF = {'primary': '#f0b54a', 'secondary': '#1a1a1a'}
_DEFAULT_DEF = {'primary': '#c8102e', 'secondary': '#ffffff'}


def _team_colors(nickname, default):
    if not nickname: return default
    return NFL_TEAM_COLORS.get(str(nickname).strip(), default)


# ============================================================================
# MAIN VISUALIZATION — plot_offense_v2
# ============================================================================

def plot_offense_v2(
    df_coords,
    df_def_coords=None,
    title='Offensive Formation',
    yard_line=40,
    attacking_right=True,
    off_team='',
    def_team='',
):
    # ── Scale factor ─────────────────────────────────────────────────────────
    # Field renders at full size (SCALE=1.0) and is saved at 300 DPI.
    # Displayed at width=400 in Streamlit — browser downscales for sharpness.
    # FONT_NUM and FONT_ROLE are boosted so text stays crisp after downscale.
    SCALE = 1.0

    FIG_W      = 10   * SCALE
    FIG_H      = 13   * SCALE
    PLAYER_S   = 650  * SCALE**2
    FONT_NUM   = 14   * SCALE      # boosted — survives 400px downscale
    FONT_ROLE  = 12   * SCALE      # boosted — survives 400px downscale
    FONT_YARD  = 44   * SCALE
    FONT_TITLE = 15   * SCALE
    LW_SIDE    = 2.5  * SCALE
    LW_LOS     = 2.8  * SCALE
    LW_YARD    = 1.0  * SCALE
    LW_TICK    = 0.7  * SCALE
    LW_HASH    = 1.0  * SCALE
    LW_CIRCLE  = 1.8  * SCALE
    LW_PRESS   = 2.5  * SCALE
    LABEL_PTS  = 36   * SCALE
    TICK_H     = 0.5  * SCALE
    HASH_W     = 0.15 * SCALE

    # ── Colors ────────────────────────────────────────────────────────────────
    off_colors = _team_colors(off_team, _DEFAULT_OFF)
    def_colors = _team_colors(def_team, _DEFAULT_DEF)
    C_BG       = '#0d0d1a'
    C_FIELD_A  = '#2a6622'
    C_FIELD_B  = '#256020'
    C_OFF_FILL = off_colors['primary']
    C_OFF_TEXT = off_colors['secondary']
    C_DEF_FILL = def_colors['primary']
    C_DEF_TEXT = def_colors['secondary']

    # ── Figure ────────────────────────────────────────────────────────────────
    x_min, x_max = -20.0, 20.0
    y_min, y_max =   0.0, 53.3

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_FIELD_A)

    # Grass stripes
    for idx, sx in enumerate(range(int(x_min), int(x_max), 5)):
        left  = max(float(sx),     x_min)
        right = min(float(sx + 5), x_max)
        if left < right:
            ax.axvspan(left, right, color=(C_FIELD_A, C_FIELD_B)[idx % 2], zorder=0)

    # Sidelines
    ax.axhline(y_min, color='white', linewidth=LW_SIDE, zorder=2)
    ax.axhline(y_max, color='white', linewidth=LW_SIDE, zorder=2)

    # Per-yard tick marks
    for yd in range(int(x_min), int(x_max) + 1):
        ax.plot([yd, yd], [y_min, y_min + TICK_H], color='white', linewidth=LW_TICK, alpha=0.5, zorder=2)
        ax.plot([yd, yd], [y_max - TICK_H, y_max], color='white', linewidth=LW_TICK, alpha=0.5, zorder=2)

    # 10-yard markers + numbers
    for marker in range(0, 101, 10):
        yard_x = float(marker - yard_line)
        if x_min <= yard_x <= x_max and yard_x != 0:
            ax.axvline(yard_x, color='white', linewidth=LW_YARD, alpha=0.3, zorder=2)
            label_val = marker if marker <= 50 else (100 - marker)
            label_str = str(int(label_val))
            ax.text(yard_x, y_min + 1.6, str(int(label_val)), ha='center', va='bottom',
        color='white', fontsize=FONT_YARD, fontweight='bold', alpha=0.18, zorder=1)
            ax.text(yard_x, y_max - 1.6, str(int(label_val)), ha='center', va='top',
        color='white', fontsize=FONT_YARD, fontweight='bold', alpha=0.18, zorder=1)

    # Hash marks
    for hash_y in (17.4, 35.9):
        for hx in range(int(x_min) - 1, int(x_max) + 2):
            ax.plot([hx - HASH_W, hx + HASH_W], [hash_y, hash_y],
                    color='white', linewidth=LW_HASH, alpha=0.6, zorder=3)

    # Conditional end zone
    import matplotlib.patches as _mp
    _yds_to_goal = 100 - yard_line

    def _primary(team):
        return NFL_TEAM_COLORS.get(str(team).strip(), {}).get('primary', '#1a4a1a')

    if _yds_to_goal <= 20:
        _goal_x = float(_yds_to_goal)
        ax.add_patch(_mp.Rectangle((_goal_x, y_min), x_max - _goal_x, y_max - y_min,
                                   facecolor=_primary(def_team), alpha=0.55, zorder=1, linewidth=0))
        ax.axvline(_goal_x, color='white', linewidth=LW_SIDE, zorder=4)
        _w = x_max - _goal_x
        if _w >= 2.0:
            _label = str(def_team).upper()
            _fs = min(16*SCALE, max(8*SCALE, 30*SCALE/max(len(_label),1)))
            ax.text(_goal_x+_w/2, (y_min+y_max)/2, _label, ha='center', va='center',
                    rotation=270, fontsize=_fs, fontweight='bold', color='white', alpha=0.9, zorder=5)
    elif _yds_to_goal >= 80:
        _goal_x = float(_yds_to_goal - 100)
        ax.add_patch(_mp.Rectangle((x_min, y_min), _goal_x - x_min, y_max - y_min,
                                   facecolor=_primary(off_team), alpha=0.55, zorder=1, linewidth=0))
        ax.axvline(_goal_x, color='white', linewidth=LW_SIDE, zorder=4)
        _w = _goal_x - x_min
        if _w >= 2.0:
            _label = str(off_team).upper()
            _fs = min(16*SCALE, max(8*SCALE, 30*SCALE/max(len(_label),1)))
            ax.text(x_min+_w/2, (y_min+y_max)/2, _label, ha='center', va='center',
                    rotation=90, fontsize=_fs, fontweight='bold', color='white', alpha=0.9, zorder=5)

    # LOS
    ax.axvline(0, color='white', linewidth=LW_LOS, zorder=4)
    ax.text(0.25, y_max - 0.8, 'LOS', ha='left', va='top', color='white',
            fontsize=7*SCALE, fontweight='bold', alpha=0.6, zorder=5)

    # Title
    ax.set_title(title, color='white', fontsize=FONT_TITLE, fontweight='bold', pad=10)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _fmt_num(val):
        try:
            if val is None: return '?'
            s = str(val).strip()
            if s in ('?','','nan','None'): return '?'
            return str(int(float(s)))
        except: return '?'

    def _to_plot(x_ft, y_ft):
        px = x_ft / 3
        py = y_ft / 3

        # Full directional flip:
        # - flip x so offense/defense swap sides of the LOS
        # - flip y so left/right role orientation mirrors correctly
        if not attacking_right:
            px = -px
            py = 53.3 - py

        return px, py

    def _label_offset_pts(px, py, all_xs, all_ys, prefer_right=True):
        candidates = [
            ( LABEL_PTS,  0, 'left',   'center'),
            (-LABEL_PTS,  0, 'right',  'center'),
            ( 0,  LABEL_PTS*0.6, 'center', 'bottom'),
            ( 0, -LABEL_PTS*0.6, 'center', 'top'),
        ]
        best = candidates[0] if prefer_right else candidates[1]
        best_dist = -1
        for dx, dy, ha, va in candidates:
            tx = px + dx * 0.018
            ty = py + dy * 0.018
            if not all_xs: return dx, dy, ha, va
            dists = [((tx-ox)**2+(ty-oy)**2)**0.5 for ox,oy in zip(all_xs,all_ys) if not (ox==px and oy==py)]
            d = min(dists) if dists else 999
            if d > best_dist: best_dist = d; best = (dx, dy, ha, va)
        return best

    # Collect all positions for label placement
    all_xs, all_ys = [], []
    for _, row in df_coords.iterrows():
        px, py = _to_plot(row['x_ft'], row['y_ft'])
        all_xs.append(px); all_ys.append(py)
    if df_def_coords is not None and not df_def_coords.empty:
        for _, row in df_def_coords.iterrows():
            px, py = _to_plot(row['x_ft'], row['y_ft'])
            all_xs.append(px); all_ys.append(py)

    # ── Draw offense ──────────────────────────────────────────────────────────
    for _, row in df_coords.iterrows():
        px, py = _to_plot(row['x_ft'], row['y_ft'])
        ax.scatter(px, py, s=PLAYER_S, c=C_OFF_FILL, edgecolors='#ffffff',
                   linewidths=LW_CIRCLE, zorder=6)
        ax.text(px, py, _fmt_num(row['player_number']), ha='center', va='center',
                fontsize=FONT_NUM, fontweight='bold', color=C_OFF_TEXT, zorder=7)
        dx, dy, ha, va = _label_offset_pts(px, py, all_xs, all_ys, prefer_right=attacking_right)
        ax.annotate(str(row['role']), xy=(px,py), xytext=(dx,dy), textcoords='offset points',
                    ha=ha, va=va, fontsize=FONT_ROLE, fontweight='bold', color='#f5f5f5',
                    zorder=7, annotation_clip=False)

    # ── Draw defense ──────────────────────────────────────────────────────────
    if df_def_coords is not None and not df_def_coords.empty:
        for _, row in df_def_coords.iterrows():
            px, py = _to_plot(row['x_ft'], row['y_ft'])
            ax.scatter(px, py, s=PLAYER_S, c=C_DEF_FILL, edgecolors='#ffffff',
                       linewidths=LW_CIRCLE, zorder=6)
            ax.text(px, py, _fmt_num(row['player_number']), ha='center', va='center',
                    fontsize=FONT_NUM, fontweight='bold', color=C_DEF_TEXT, zorder=7)
            dx, dy, ha, va = _label_offset_pts(px, py, all_xs, all_ys, prefer_right=attacking_right)
            ax.annotate(str(row['role']), xy=(px,py), xytext=(dx,dy), textcoords='offset points',
                        ha=ha, va=va, fontsize=FONT_ROLE, fontweight='bold', color='#f5f5f5',
                        zorder=7, annotation_clip=False)
            if row.get('press', 0) == 1:
                circle_r = (PLAYER_S**0.5) / 2 * 0.014
                ax.scatter(px, py, s=PLAYER_S*2.6, c='none', edgecolors='#ffdd00',
                           linewidths=LW_PRESS, zorder=5, alpha=0.85)
                ax.text(px, py + circle_r + 0.6*SCALE, 'P', ha='center', va='bottom',
                        fontsize=8*SCALE, fontweight='bold', color='#ffdd00', zorder=8,
                        bbox=dict(boxstyle='round,pad=0.15', fc=C_DEF_FILL, ec='#ffdd00',
                                  linewidth=1.2*SCALE, alpha=0.9))

    # ── Axis ──────────────────────────────────────────────────────────────────
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout(pad=1.5)
    return fig, ax


# ============================================================================
# CSV HELPERS
# ============================================================================

def build_title(team_name, formation) -> str:
    team = '' if pd.isna(team_name) else str(team_name).strip()
    form = '' if pd.isna(formation) else str(formation).strip()
    if team and form: return f"{team} - {form}"
    return team or form or 'Offense'


def extract_from_wide_row(row) -> tuple:
    role_list   = [row.get(f'off_{i}_role')             for i in range(1, 12)]
    number_list = [row.get(f'off_{i}_number')           for i in range(1, 12)]
    name_list   = [row.get(f'off_{i}_player_last_name') for i in range(1, 12)]
    qb_pos = row.get('qb_pos', row.get('QB_POS', row.get('QB_pos', 'S')))
    title  = build_title(row.get('offensive_team_nickname', 'Offense'), row.get('offensive_formation', ''))
    return role_list, number_list, name_list, qb_pos, title


def extract_from_long_df(df, play_unique_id=None):
    if play_unique_id is None: play_unique_id = df['PLAY_UNIQUE_ID'].iloc[0]
    play_df = df[df['PLAY_UNIQUE_ID'] == play_unique_id].copy()
    positioning = play_df[play_df['ROLE_CATEGORY'].str.upper() == 'POSITIONING'].copy()
    positioning = positioning.drop_duplicates(subset=['PLAYER_ID', 'ROLE_ABBREV'])
    if 'FORMATION_ORDER' in positioning.columns:
        positioning = positioning.sort_values(['FORMATION_ORDER', 'PLAYER_ID'])
    role_list   = positioning['ROLE_ABBREV'].tolist()
    number_list = positioning['PLAYER_NUMBER'].tolist()
    name_list   = positioning['PLAYER_LAST_NAME'].tolist()
    qb_pos = 'S'
    for col in ('QB_POS', 'QB_pos', 'qb_pos'):
        if col in play_df.columns and not play_df[col].dropna().empty:
            qb_pos = play_df[col].dropna().iloc[0]; break
    title = build_title(
        play_df['OFFENSIVE_TEAM_NICKNAME'].iloc[0] if 'OFFENSIVE_TEAM_NICKNAME' in play_df.columns else 'Offense',
        play_df['OFFENSIVE_FORMATION'].iloc[0]     if 'OFFENSIVE_FORMATION'     in play_df.columns else '',
    )
    return role_list, number_list, name_list, qb_pos, title


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',     type=str, default='final_x_info_catalog_with_event.csv')
    parser.add_argument('--play-id',   type=int, default=None)
    parser.add_argument('--row-index', type=int, default=0)
    parser.add_argument('--qb-pos',    type=str, default=None)
    parser.add_argument('--output',    type=str, default='outputs/figures/sample_offense.png')
    args = parser.parse_args()

    df = pd.read_csv(Path(args.input), low_memory=False)
    if {'PLAY_UNIQUE_ID', 'ROLE_CATEGORY', 'ROLE_ABBREV'}.issubset(df.columns):
        role_list, number_list, name_list, qb_pos, title = extract_from_long_df(df, args.play_id)
    else:
        col_candidates = ['play_unique_id', 'PLAY_UNIQUE_ID']
        row = df.iloc[args.row_index]
        if args.play_id is not None:
            for col in col_candidates:
                if col in df.columns:
                    m = df[df[col] == args.play_id]
                    if not m.empty: row = m.iloc[0]; break
        role_list, number_list, name_list, qb_pos, title = extract_from_wide_row(row)

    if args.qb_pos: qb_pos = args.qb_pos
    df_coords = map_offense_to_coordinates(role_list, number_list, name_list, qb_pos=qb_pos)
    fig, _ = plot_offense(df_coords, title=title)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    main()