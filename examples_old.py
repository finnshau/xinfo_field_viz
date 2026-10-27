"""
xInfoViz Offensive Formation Mapper
====================================
Rule-based placement of offensive players onto a 2D field.

FIELD GEOMETRY (all distances in feet):
  - Field width:        160 ft (sideline to sideline)
  - Center (C):         y = 80
  - Each OL step:       5 ft outward from C
  - Each TE step:       5 ft outward from outermost OL on that side
  - WR spacing:         remaining field / (num_WRs_on_side + 1), placed from sideline inward
  - LOS:                x = 0

QB DEPTH (pulled from qb_pos field: N / P / S):
  N = Under Center  ->  x = -2
  P = Pistol        ->  x = -12
  S = Shotgun       ->  x = -15

RB DEPTH:
  N / P  ->  x = -21
  S      ->  x = -15
  L/R offset from center: +/-4 ft (additional RBs same side: another +/-4 ft each)

FB DEPTH:
  N      ->  x = -14
  P side ->  x = -15 (left or right of QB)
  P mid  ->  x = -17.5
  S      ->  x = -13
  L/R offset: +/-5 ft

No player positions are hardcoded. Only field geometry and placement
rules are defined here.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# FIELD CONSTANTS (geometry only — no player data)
# ============================================================================

FIELD_WIDTH_FT = 160
CENTER_Y = FIELD_WIDTH_FT / 2
LOS_X = 0

OL_STEP = 5
TE_STEP = 5

QB_DEPTH = {
    'N': -2.0,
    'P': -12.0,
    'S': -15.0,
}

RB_DEPTH = {
    'N': -21.0,
    'P': -21.0,
    'S': -15.0,
}
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

WR_SUFFIX_RANK = {
    'OR':   0,
    'SR':   1,
    'IR':   2,
    'IIR':  3,
    'IIIR': 4,
}


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
        'player_number': number,
        'player_name':   name,
        'role':          role,
        'x_ft':          0.0,
        'y_ft':          0.0,
        'is_uncertain':  True,
        'uncertain_reason': reason,
    }


def _ensure_eleven_players(df_coords: pd.DataFrame) -> pd.DataFrame:
    if len(df_coords) > 11:
        print(f"WARNING: mapped {len(df_coords)} players; trimming to 11")
        return df_coords.iloc[:11].reset_index(drop=True)

    if len(df_coords) < 11:
        missing = 11 - len(df_coords)
        print(f"WARNING: mapped {len(df_coords)} players; padding {missing} placeholder(s)")
        placeholders = [
            _placeholder_row('UNK', '?', 'Placeholder', 'auto-pad-to-11')
            for _ in range(missing)
        ]
        return pd.concat([df_coords, pd.DataFrame(placeholders)], ignore_index=True)

    return df_coords.reset_index(drop=True)


def wr_suffix_rank(role_code: str) -> int:
    suffix = role_code[1:]
    return WR_SUFFIX_RANK.get(suffix, 99)


def role_side(role_code: str) -> str:
    code = str(role_code).strip().upper()
    left_explicit  = {'RBL', 'FBL', 'SBL', 'PAL', 'PBL'}
    right_explicit = {'RBR', 'FBR', 'SBR', 'PAR', 'PBR'}
    if code in left_explicit:
        return 'L'
    if code in right_explicit:
        return 'R'
    if code.startswith('L'):
        return 'L'
    if code.startswith('R'):
        return 'R'
    return 'M'


def normalize_qb_pos(raw) -> str:
    if pd.isna(raw) or not str(raw).strip():
        return 'S'
    first = str(raw).strip().upper()[0]
    return first if first in QB_DEPTH else 'S'


# ============================================================================
# OL Y-POSITION CALCULATOR
# ============================================================================

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

def map_offense_to_coordinates(
    role_list: list,
    number_list: list,
    name_list: list,
    qb_pos: str = 'S',
) -> pd.DataFrame:

    qb_mode = normalize_qb_pos(qb_pos)

    players = []
    for role, number, name in zip(role_list, number_list, name_list):
        if pd.isna(role):
            continue
        rc = str(role).strip()
        if not rc or rc.lower() == 'nan':
            continue
        players.append({
            'role': rc,
            'number': number,
            'name': str(name).strip(),
            'number_uncertain': not _is_valid_number(number),
        })

    coords = []
    uncertain_rows = []
    ol_y = ol_y_positions()

    for p in players:
        if p['number_uncertain']:
            uncertain_rows.append(_placeholder_row(p['role'], '?', p['name'], 'uncertain-number'))

    # ---- OFFENSIVE LINE ----
    for p in players:
        if p['number_uncertain']:
            continue
        if p['role'] in ol_y:
            coords.append({
                'player_number': p['number'],
                'player_name':   p['name'],
                'role':          p['role'],
                'x_ft':          LOS_X,
                'y_ft':          ol_y[p['role']],
                'is_uncertain':  False,
                'uncertain_reason': '',
            })

    # ---- TIGHT ENDS / WINGS ----
    placed_ys_left  = [c['y_ft'] for c in coords if role_side(c['role']) in ('L', 'M') and c['role'] in ol_y]
    placed_ys_right = [c['y_ft'] for c in coords if role_side(c['role']) in ('R', 'M') and c['role'] in ol_y]

    lt_y = max(placed_ys_left)  if placed_ys_left  else CENTER_Y + 2 * OL_STEP
    rt_y = min(placed_ys_right) if placed_ys_right else CENTER_Y - 2 * OL_STEP

    left_tes  = [p for p in players if not p['number_uncertain'] and p['role'] in TE_ROLE_CODES and role_side(p['role']) in ('L', 'M')]
    right_tes = [p for p in players if not p['number_uncertain'] and p['role'] in TE_ROLE_CODES and role_side(p['role']) == 'R']

    for i, p in enumerate(left_tes):
        coords.append({
            'player_number': p['number'],
            'player_name':   p['name'],
            'role':          p['role'],
            'x_ft':          LOS_X,
            'y_ft':          lt_y + TE_STEP * (i + 1),
            'is_uncertain':  False,
            'uncertain_reason': '',
        })

    for i, p in enumerate(right_tes):
        coords.append({
            'player_number': p['number'],
            'player_name':   p['name'],
            'role':          p['role'],
            'x_ft':          LOS_X,
            'y_ft':          rt_y - TE_STEP * (i + 1),
            'is_uncertain':  False,
            'uncertain_reason': '',
        })

    # ---- WIDE RECEIVERS ----
    all_placed_ys = [c['y_ft'] for c in coords]
    left_edge  = max(all_placed_ys) if all_placed_ys else CENTER_Y
    right_edge = min(all_placed_ys) if all_placed_ys else CENTER_Y

    left_wrs = sorted(
        [p for p in players if not p['number_uncertain'] and p['role'] in WR_ROLE_CODES and role_side(p['role']) == 'L'],
        key=lambda p: wr_suffix_rank(p['role'])  # OR first (outermost), IIIR last
    )
    right_wrs = sorted(
        [p for p in players if not p['number_uncertain'] and p['role'] in WR_ROLE_CODES and role_side(p['role']) == 'R'],
        key=lambda p: wr_suffix_rank(p['role'])
    )

    # Left WRs: place from left sideline (y=160) inward
    # step = remaining_field / (num_wrs + 1)
    # OR lands at 1 step from sideline, SR at 2 steps, etc.
    if left_wrs:
        remaining_left = FIELD_WIDTH_FT - left_edge
        step = remaining_left / (len(left_wrs) + 1)
        for i, p in enumerate(left_wrs, start=1):
            coords.append({
                'player_number': p['number'],
                'player_name':   p['name'],
                'role':          p['role'],
                'x_ft':          LOS_X,
                'y_ft':          FIELD_WIDTH_FT - (step * i),
                'is_uncertain':  False,
                'uncertain_reason': '',
            })

    # Right WRs: place from right sideline (y=0) inward
    # OR lands at 1 step from sideline, SR at 2 steps, etc.
    if right_wrs:
        remaining_right = right_edge
        step = remaining_right / (len(right_wrs) + 1)
        for i, p in enumerate(right_wrs, start=1):
            coords.append({
                'player_number': p['number'],
                'player_name':   p['name'],
                'role':          p['role'],
                'x_ft':          LOS_X,
                'y_ft':          step * i,
                'is_uncertain':  False,
                'uncertain_reason': '',
            })

    # ---- QUARTERBACK ----
    for p in players:
        if p['number_uncertain']:
            continue
        if p['role'] == 'QB':
            coords.append({
                'player_number': p['number'],
                'player_name':   p['name'],
                'role':          'QB',
                'x_ft':          QB_DEPTH[qb_mode],
                'y_ft':          CENTER_Y,
                'is_uncertain':  False,
                'uncertain_reason': '',
            })

    # ---- RUNNING BACKS ----
    rb_side_count = {'L': 0, 'R': 0}
    for p in players:
        if p['number_uncertain']:
            continue
        if p['role'] not in RB_ROLE_CODES:
            continue
        side = role_side(p['role'])
        x = RB_DEPTH[qb_mode]

        if qb_mode == 'S':
            if side == 'L':
                rb_side_count['L'] += 1
                y = CENTER_Y + RB_LATERAL_STEP * rb_side_count['L']
            elif side == 'R':
                rb_side_count['R'] += 1
                y = CENTER_Y - RB_LATERAL_STEP * rb_side_count['R']
            else:
                y = CENTER_Y
        else:
            y = CENTER_Y + 5 if side == 'L' else (CENTER_Y - 5 if side == 'R' else CENTER_Y)

        coords.append({
            'player_number': p['number'],
            'player_name':   p['name'],
            'role':          p['role'],
            'x_ft':          x,
            'y_ft':          y,
            'is_uncertain':  False,
            'uncertain_reason': '',
        })

    # ---- FULLBACKS ----
    for p in players:
        if p['number_uncertain']:
            continue
        if p['role'] not in FB_ROLE_CODES:
            continue
        side = role_side(p['role'])

        if qb_mode == 'N':
            x = FB_DEPTH_NORMAL
            y = CENTER_Y + FB_LATERAL if side == 'L' else (CENTER_Y - FB_LATERAL if side == 'R' else CENTER_Y)
        elif qb_mode == 'P':
            if side == 'M':
                x = FB_DEPTH_PISTOL_MID
                y = CENTER_Y
            else:
                x = FB_DEPTH_PISTOL_SIDE
                y = CENTER_Y + FB_LATERAL if side == 'L' else CENTER_Y - FB_LATERAL
        else:
            x = FB_DEPTH_SHOTGUN
            y = CENTER_Y + FB_LATERAL if side == 'L' else (CENTER_Y - FB_LATERAL if side == 'R' else CENTER_Y)

        coords.append({
            'player_number': p['number'],
            'player_name':   p['name'],
            'role':          p['role'],
            'x_ft':          x,
            'y_ft':          y,
            'is_uncertain':  False,
            'uncertain_reason': '',
        })

    # ---- UNRECOGNIZED ROLES ----
    placed_roles = {c['role'] for c in coords}
    for p in players:
        if p['number_uncertain']:
            continue
        if p['role'] not in placed_roles:
            print(f"WARNING: unrecognized role '{p['role']}' — placing at (0,0) in red")
            uncertain_rows.append(_placeholder_row(p['role'], p['number'], p['name'], 'unrecognized-role'))

    df_coords = pd.concat([pd.DataFrame(coords), pd.DataFrame(uncertain_rows)], ignore_index=True)
    return _ensure_eleven_players(df_coords)


def map_defense_to_coordinates(
    role_list: list,
    number_list: list,
    name_list: list,
    press_list: list,
    ol_coords: pd.DataFrame
) -> pd.DataFrame:

    def get_y(role):
        rows = ol_coords[ol_coords['role'] == role]
        return float(rows['y_ft'].iloc[0]) if not rows.empty else None

    C_y  = get_y('C')  if get_y('C')  is not None else 80.0
    LG_y = get_y('LG') if get_y('LG') is not None else 85.0
    LT_y = get_y('LT') if get_y('LT') is not None else 90.0
    RG_y = get_y('RG') if get_y('RG') is not None else 75.0
    RT_y = get_y('RT') if get_y('RT') is not None else 70.0
    LOR_y = get_y('LOR')
    ROR_y = get_y('ROR')
    LSR_y = get_y('LSR')
    RSR_y = get_y('RSR')
    LIR_y = get_y('LIR')
    RIR_y = get_y('RIR')

    players = []
    for role, number, name, press in zip(role_list, number_list, name_list, press_list):
        if pd.isna(role) or str(role).strip() in ('', 'nan'):
            continue
        players.append({
            'role': str(role).strip(),
            'number': number,
            'name': str(name).strip(),
            'press': int(press) if not pd.isna(press) else 0
        })

    coords = []

    for p in players:
        role = p['role']
        press = p['press']
        base_role = role[:-1] if role.lower().endswith('m') else role

        x = None
        y = None

        # ---- DEFENSIVE LINE ----
        # x=1 means 1 foot on the POSITIVE side of LOS (defensive side)
        # Directionality is OPPOSITE — R suffix = left side of offense, L suffix = right side
        if base_role in ('0T', 'NOSE', '0'):
            x, y = 1, C_y
        elif base_role == '1L':
            x, y = 1, (C_y + RG_y) / 2
        elif base_role == '1R':
            x, y = 1, (C_y + LG_y) / 2
        elif base_role == '2iL':
            x, y = 1, RG_y + 1
        elif base_role == '2iR':
            x, y = 1, LG_y - 1
        elif base_role == '2L':
            x, y = 1, RG_y
        elif base_role == '2R':
            x, y = 1, LG_y
        elif base_role == '3L':
            x, y = 1, (RG_y + RT_y) / 2
        elif base_role == '3R':
            x, y = 1, (LG_y + LT_y) / 2
        elif base_role == '4iL':
            x, y = 1, RT_y + 1
        elif base_role == '4iR':
            x, y = 1, LT_y - 1
        elif base_role == '4L':
            x, y = 1, RT_y
        elif base_role == '4R':
            x, y = 1, LT_y
        elif base_role == '5L':
            x, y = 1, RT_y - 2
        elif base_role == '5R':
            x, y = 1, LT_y + 2
        elif base_role == '5Lw':
            x, y = 1, RT_y - 5
        elif base_role == '5Rw':
            x, y = 1, LT_y + 5
        elif base_role == '6L':
            x, y = 1, RT_y - 8
        elif base_role == '6R':
            x, y = 1, LT_y + 8
        elif base_role == '7L':
            x, y = 1, RT_y - 10
        elif base_role == '7R':
            x, y = 1, LT_y + 10
        elif base_role == '9L':
            x, y = 1, RT_y - 12
        elif base_role == '9R':
            x, y = 1, LT_y + 12
        elif base_role == '9Lw':
            x, y = 1, RT_y - 15
        elif base_role == '9Rw':
            x, y = 1, LT_y + 15

        # ---- LINEBACKERS ----
        # 5 yards = 15 feet behind LOS on defensive side = x=15
        # MLB is 6 yards = 18 feet = x=18
        elif base_role == 'MLB':
            x, y = 18, C_y
        elif base_role == 'LILB':
            x, y = 15, (RT_y + RG_y) / 2
        elif base_role == 'RILB':
            x, y = 15, (LT_y + LG_y) / 2
        elif base_role == 'RLB':
            x, y = 15, LT_y + 5
        elif base_role == 'LLB':
            x, y = 15, RT_y - 5
        elif base_role == 'ROLB':
            x, y = 15, LT_y + 8
        elif base_role == 'LOLB':
            x, y = 15, RT_y - 8

        # ---- SAFETIES ----
        # All depths in feet (yards x 3)
        elif base_role == 'LSS':
            x, y = 22.5, RT_y - 3
        elif base_role == 'RSS':
            x, y = 22.5, LT_y + 3
        elif base_role == 'MSS':
            x, y = 22.5, C_y
        elif base_role == 'MS':
            x, y = 36, C_y
        elif base_role == 'LS':
            x, y = 45, 120
        elif base_role == 'RS':
            x, y = 45, 40
        elif base_role == 'CF':
            x, y = 54, C_y

        # ---- CORNERBACKS ----
        # Line up opposite matching receiver
        # LOC opposite ROR, ROC opposite LOR
        # LSC opposite RSR, RSC opposite LSR
        # LIC opposite RIR, RIC opposite LIR
        # Default depth: LOC/ROC = 8 yards = 24 feet, LSC/RSC/LIC/RIC = 6 yards = 18 feet
        elif base_role == 'LOC':
            x = 24
            y = ROR_y if ROR_y is not None else RT_y - 20
        elif base_role == 'ROC':
            x = 24
            y = LOR_y if LOR_y is not None else LT_y + 20
        elif base_role == 'LSC':
            x = 18
            y = RSR_y if RSR_y is not None else RT_y - 15
        elif base_role == 'RSC':
            x = 18
            y = LSR_y if LSR_y is not None else LT_y + 15
        elif base_role == 'LIC':
            x = 18
            y = RIR_y if RIR_y is not None else RT_y - 10
        elif base_role == 'RIC':
            x = 18
            y = LIR_y if LIR_y is not None else LT_y + 10
        elif base_role == 'LIIC':
            x, y = 18, RT_y - 8
        elif base_role == 'RIIC':
            x, y = 18, LT_y + 8

        else:
            print(f'WARNING: unrecognized defensive role {role} — placing at default position')
            x, y = 18, C_y

        # ---- PRESS COVERAGE OVERRIDE ----
        # Press moves defender up to the LOS on the defensive side
        if press == 1:
            x = 2

        coords.append({
            'player_number': p['number'],
            'player_name':   p['name'],
            'role':          role,
            'x_ft':          float(x),
            'y_ft':          float(y),
            'press':         press,
        })

    return pd.DataFrame(coords)


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_offense(df_coords: pd.DataFrame, title: str = "Offensive Formation"):
    fig, ax = plt.subplots(figsize=(4.8, 8.2))
    ax.set_facecolor('#2f7a34')
    fig.patch.set_facecolor('#2f7a34')

    ax.axvline(LOS_X, color='white', linewidth=2.4, zorder=1)

    point_colors = ['#d62828' if bool(v) else '#7c4ec8' for v in df_coords.get('is_uncertain', pd.Series([False] * len(df_coords)))]
    edge_colors = ['#ffffff' if bool(v) else '#f0b54a' for v in df_coords.get('is_uncertain', pd.Series([False] * len(df_coords)))]

    ax.scatter(
        df_coords['x_ft'], df_coords['y_ft'],
        s=250, c=point_colors, edgecolors=edge_colors,
        linewidths=1.8, zorder=3,
    )

    for _, row in df_coords.iterrows():
        num = row['player_number']
        if pd.isna(num):
            num = '?'
        elif isinstance(num, str) and num == '?':
            pass  # keep as '?'
        else:
            num = int(float(num))
        ax.text(row['x_ft'], row['y_ft'], str(num),
                ha='center', va='center',
                fontsize=8, fontweight='bold', color='white', zorder=4)
        ax.text(row['x_ft'] + 0.85, row['y_ft'], str(row['role']),
                ha='left', va='center',
                fontsize=5.2, fontweight='bold', color='#f3f3f3', zorder=4)

    ax.set_xlim(-23, 3)
    ax.set_ylim(0, FIELD_WIDTH_FT)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(title, fontsize=13, color='white', fontweight='bold', pad=8)
    plt.subplots_adjust(left=0.06, right=0.98, top=0.95, bottom=0.03)
    plt.tight_layout()
    return fig, ax


def plot_offense_v2(
    df_coords: pd.DataFrame,
    df_def_coords: pd.DataFrame = None,
    title: str = 'Offensive Formation',
    yard_line: int = 40,
    attacking_right: bool = True,
):
    fig, ax = plt.subplots(figsize=(10, 13))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#2d6e27')

    x_min, x_max = -20.0, 20.0
    y_min, y_max = 0.0, 53.3

    stripe_colors = ('#2d6e27', '#296b23')
    for stripe_idx, stripe_start in enumerate(range(int(x_min), int(x_max), 5)):
        left  = max(float(stripe_start),     x_min)
        right = min(float(stripe_start + 5), x_max)
        if left < right:
            ax.axvspan(left, right, color=stripe_colors[stripe_idx % 2], zorder=0)

    ax.axhline(0, color='white', linewidth=2.5, zorder=2)
    ax.axhline(53.3, color='white', linewidth=2.5, zorder=2)

    for yard_x in range(int(x_min), int(x_max) + 1):
        ax.plot([yard_x, yard_x], [y_min, y_min + 0.4], color='white', linewidth=0.8, alpha=0.5, zorder=2)
        ax.plot([yard_x, yard_x], [y_max - 0.4, y_max], color='white', linewidth=0.8, alpha=0.5, zorder=2)

    visible_markers = []
    for marker in range(0, 101, 10):
        yard_x = float(marker - yard_line)
        if x_min <= yard_x <= x_max and yard_x != 0:
            visible_markers.append((marker, yard_x))

    for marker, yard_x in visible_markers:
        ax.axvline(yard_x, color='white', linewidth=1.2, alpha=0.4, zorder=2)
        label_value = marker if marker <= 50 else (100 - marker)
        label = str(int(label_value))
        ax.text(yard_x, 2.0, label, ha='center', va='bottom', color='white', fontsize=48, fontweight='bold', zorder=3)
        ax.text(yard_x, 51.3, label, ha='center', va='top', color='white', fontsize=48, fontweight='bold', zorder=3)

    ax.axvline(0, color='white', linewidth=2.5, zorder=4)

    for hash_y in (17.4, 35.9):
        for x in range(int(x_min) - 1, int(x_max) + 2):
            ax.plot([x, x], [hash_y - 0.2, hash_y + 0.2],
                    color='white', linewidth=0.8, alpha=0.5, zorder=3)

    label_dx_pts = 30 if attacking_right else -30
    label_ha = 'left' if attacking_right else 'right'

    for _, row in df_coords.iterrows():
        px = row['x_ft'] / 3
        py = row['y_ft'] / 3

        if not attacking_right:
            py = 53.3 - py

        ax.scatter(px, py, s=400, c='#1a1a2e', edgecolors='#f0b54a', linewidths=2.5, zorder=5)

        ax.text(px, py, str(int(row['player_number'])),
            ha='center', va='center', fontsize=10, fontweight='bold',
                color='#f0b54a', zorder=6)

        ax.annotate(
            str(row['role']),
            xy=(px, py),
            xytext=(label_dx_pts, 0),
            textcoords='offset points',
            ha=label_ha,
            va='center',
            fontsize=9,
            fontweight='bold',
            color='#f3f3f3',
            zorder=6,
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(title, color='white', fontsize=14, fontweight='bold')

    # ---- DEFENSIVE PLAYERS ----
    # Plotted on POSITIVE x side of LOS (above LOS line in portrait view)
    # Same coordinate conversion as offense: px = y_ft/3 (lateral), py = x_ft/3 (depth)
    # Defensive x_ft values are POSITIVE so py will be positive = above LOS on screen
    if df_def_coords is not None and not df_def_coords.empty:
        print(f"  {title} axis ranges before defense: xlim={ax.get_xlim()}, ylim={ax.get_ylim()}")
        for _, row in df_def_coords.iterrows():
            # depth goes on matplotlib x-axis
            # lateral goes on matplotlib y-axis
            plot_x = row['x_ft'] / 3   # depth — POSITIVE for defense = right of LOS
            plot_y = row['y_ft'] / 3   # lateral — same as offense

            if not attacking_right:
                plot_y = 53.3 - plot_y

            ax.scatter(plot_x, plot_y,
                       s=400, c='#1a1a2e',
                       edgecolors='#e63946', linewidths=2.5, zorder=5)

            ax.text(plot_x, plot_y,
                    str(int(row['player_number'])),
                    ha='center', va='center',
                    fontsize=10, fontweight='bold',
                    color='#e63946', zorder=6)

            if attacking_right:
                label_offset = +30
                label_ha = 'left'
            else:
                label_offset = -30
                label_ha = 'right'

            ax.annotate(str(row['role']),
                        xy=(plot_x, plot_y),
                        xytext=(label_offset, 0),
                        textcoords='offset points',
                        ha=label_ha, va='center',
                        fontsize=9, fontweight='bold',
                        color='#e63946', zorder=6)

            if row.get('press', 0) == 1:
                ax.text(plot_x, plot_y + 1.5, 'P',
                        ha='center', va='bottom',
                        fontsize=8, fontweight='bold',
                        color='white', zorder=7)

    plt.tight_layout(pad=1.5)
    return fig, ax


# ============================================================================
# CSV HELPERS
# ============================================================================

def build_title(team_name, formation) -> str:
    team = '' if pd.isna(team_name) else str(team_name).strip()
    form = '' if pd.isna(formation) else str(formation).strip()
    if team and form:
        return f"{team} - {form}"
    return team or form or 'Offense'


def extract_from_wide_row(row) -> tuple:
    role_list   = [row.get(f'off_{i}_role')             for i in range(1, 12)]
    number_list = [row.get(f'off_{i}_number')           for i in range(1, 12)]
    name_list   = [row.get(f'off_{i}_player_last_name') for i in range(1, 12)]
    qb_pos = row.get('qb_pos', row.get('QB_POS', row.get('QB_pos', 'S')))
    title  = build_title(
        row.get('offensive_team_nickname', row.get('offensive_team_name', 'Offense')),
        row.get('offensive_formation', ''),
    )
    return role_list, number_list, name_list, qb_pos, title


def extract_from_long_df(df: pd.DataFrame, play_unique_id=None) -> tuple:
    if play_unique_id is None:
        play_unique_id = df['PLAY_UNIQUE_ID'].iloc[0]

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
            qb_pos = play_df[col].dropna().iloc[0]
            break

    title = build_title(
        play_df['OFFENSIVE_TEAM_NICKNAME'].iloc[0] if 'OFFENSIVE_TEAM_NICKNAME' in play_df.columns else 'Offense',
        play_df['OFFENSIVE_FORMATION'].iloc[0]     if 'OFFENSIVE_FORMATION'     in play_df.columns else '',
    )
    return role_list, number_list, name_list, qb_pos, title


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='xInfoViz Offensive Formation Mapper')
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
        if args.play_id is not None:
            matched = None
            for col in col_candidates:
                if col in df.columns:
                    m = df[df[col] == args.play_id]
                    if not m.empty:
                        matched = m.iloc[0]
                        break
            row = matched if matched is not None else df.iloc[args.row_index]
        else:
            row = df.iloc[args.row_index]
        role_list, number_list, name_list, qb_pos, title = extract_from_wide_row(row)

    if args.qb_pos:
        qb_pos = args.qb_pos

    df_coords = map_offense_to_coordinates(role_list, number_list, name_list, qb_pos=qb_pos)

    print(df_coords.sort_values(['x_ft', 'y_ft']).to_string(index=False))
    print(f"\nTotal players placed: {len(df_coords)} (expected 11)")
    print(f"QB mode: {normalize_qb_pos(qb_pos)}")

    fig, _ = plot_offense(df_coords, title=title)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    print(f"Saved: {out.resolve()}")
    plt.show()


if __name__ == '__main__':
    main()
    