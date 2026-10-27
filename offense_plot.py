import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# FIELD CONSTANTS
# ----------------------------------------------------------------------
FIELD_WIDTH = 160
CENTER_Y = 80
LOS_X = 0

QB_DEPTHS = {
    'N': -2.0,
    'P': -12.0,
    'S': -15.0,
}

RB_DEPTHS = {
    'N': -21.0,
    'P': -21.0,
    'S': -15.0,
}

FB_DEPTHS = {
    'N': -14.0,
    'P_SIDE': -15.0,
    'P_MID': -17.5,
    'S': -13.0,
}

OL_POSITIONS = {'C': 80, 'LG': 85, 'LT': 90, 'RG': 75, 'RT': 70}
TE_SPACING = 5
TE_START_LEFT_Y = 95
TE_START_RIGHT_Y = 65

LEFT_ROLES = {'LTE','LIT','LW','LIW','PAL','PBL','LOR','LSR','LIR','LIIR','LIIIR','RBL','FBL'}
RIGHT_ROLES = {'RTE','RIT','RW','RIW','PAR','PBR','ROR','RSR','RIR','RIIR','RIIIR','RBR','FBR'}
TE_ROLES = {'LTE','LIT','LW','LIW','PAL','PBL','RTE','RIT','RW','RIW','PAR','PBR'}
WR_ROLES = {'LOR','LSR','LIR','LIIR','LIIIR','ROR','RSR','RIR','RIIR','RIIIR'}
RB_FB_ROLES = {'RBL','RBR','RBM','SBL','SBR','VSF','FBL','FBR','FBM'}

WR_OUTSIDE_TO_INSIDE_ORDER = {
    'OR': 0,
    'SR': 1,
    'IR': 2,
    'IIR': 3,
    'IIIR': 4,
}


def wr_alignment_rank(role_code):
    suffix = role_code[1:] if len(role_code) > 1 else role_code
    return WR_OUTSIDE_TO_INSIDE_ORDER.get(suffix, 99)


def infer_role_side(role_code):
    role_text = str(role_code).strip().upper()
    if role_text in LEFT_ROLES:
        return 'L'
    if role_text in RIGHT_ROLES:
        return 'R'
    if 'LEFT' in role_text or role_text.startswith('L'):
        return 'L'
    if 'RIGHT' in role_text or role_text.startswith('R'):
        return 'R'
    return 'M'


def normalize_qb_pos(qb_pos):
    if pd.isna(qb_pos):
        return 'S'
    normalized = str(qb_pos).strip().upper()
    if not normalized:
        return 'S'
    if normalized in QB_DEPTHS:
        return normalized
    first = normalized[0]
    if first in QB_DEPTHS:
        return first
    return 'S'


def build_title(team_name, formation):
    team = '' if pd.isna(team_name) else str(team_name).strip()
    form = '' if pd.isna(formation) else str(formation).strip()
    if team and form:
        return f"{team} - {form}"
    return team or form or 'Offense'


def map_offense_to_coordinates(role_list, number_list, name_list, qb_pos='S'):
    qb_mode = normalize_qb_pos(qb_pos)
    players = []
    for role, number, name in zip(role_list, number_list, name_list):
        if pd.isna(role):
            continue
        role_code = str(role).strip()
        if not role_code or role_code.lower() == 'nan':
            continue
        players.append({'role': role_code, 'number': number, 'name': name})

    placed = set()
    coords = []

    # Offensive line - on the LOS (x=0), fixed y positions
    for p in players:
        if p['role'] in OL_POSITIONS:
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': p['role'], 'x_ft': LOS_X, 'y_ft': OL_POSITIONS[p['role']]})
            placed.add(p['role'])

    # Tight ends / wings - also on the LOS, stepping outward from tackles
    left_te_i, right_te_i = 0, 0
    for p in players:
        if p['role'] in TE_ROLES and p['role'] not in placed:
            side = infer_role_side(p['role'])
            if side == 'L':
                y = TE_START_LEFT_Y + (left_te_i * TE_SPACING); left_te_i += 1
            elif side == 'R':
                y = TE_START_RIGHT_Y - (right_te_i * TE_SPACING); right_te_i += 1
            else:
                y = TE_START_LEFT_Y + (left_te_i * TE_SPACING); left_te_i += 1
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': p['role'], 'x_ft': LOS_X, 'y_ft': y})
            placed.add(p['role'])

    # Wide receivers - on the LOS, spaced from sideline to next inside player.
    left_attached_ys = [c['y_ft'] for c in coords if infer_role_side(c['role']) == 'L']
    right_attached_ys = [c['y_ft'] for c in coords if infer_role_side(c['role']) == 'R']
    left_bound = max(left_attached_ys) if left_attached_ys else CENTER_Y
    right_bound = min(right_attached_ys) if right_attached_ys else CENTER_Y

    left_wrs = [p for p in players if p['role'] in WR_ROLES and infer_role_side(p['role']) == 'L']
    right_wrs = [p for p in players if p['role'] in WR_ROLES and infer_role_side(p['role']) == 'R']

    left_wrs = sorted(left_wrs, key=lambda player: wr_alignment_rank(player['role']))
    right_wrs = sorted(right_wrs, key=lambda player: wr_alignment_rank(player['role']))

    if left_wrs:
        left_step = (FIELD_WIDTH - left_bound) / (len(left_wrs) + 1)
        for idx, p in enumerate(left_wrs, start=1):
            y = FIELD_WIDTH - (left_step * idx)
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': p['role'], 'x_ft': LOS_X, 'y_ft': y})
            placed.add(p['role'])

    if right_wrs:
        right_step = right_bound / (len(right_wrs) + 1)
        for idx, p in enumerate(right_wrs, start=1):
            y = right_step * idx
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': p['role'], 'x_ft': LOS_X, 'y_ft': y})
            placed.add(p['role'])

    # QB - behind the LOS, centered
    for p in players:
        if p['role'] == 'QB':
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': 'QB', 'x_ft': QB_DEPTHS[qb_mode], 'y_ft': CENTER_Y})
            placed.add('QB')

    # RB / FB placements by QB mode and side.
    rb_side_counts = {'L': 0, 'R': 0}
    for p in players:
        if p['role'] in RB_FB_ROLES and p['role'] not in placed:
            role = p['role']
            is_fb = role.startswith('FB')

            side = infer_role_side(role)

            if is_fb:
                if qb_mode == 'N':
                    x = FB_DEPTHS['N']
                elif qb_mode == 'P':
                    x = FB_DEPTHS['P_MID'] if side == 'M' else FB_DEPTHS['P_SIDE']
                else:
                    x = FB_DEPTHS['S']
            else:
                x = RB_DEPTHS[qb_mode]

            if qb_mode == 'S' and not is_fb and side in {'L', 'R'}:
                rb_side_counts[side] += 1
                base = 4 + ((rb_side_counts[side] - 1) * 4)
                y = CENTER_Y + base if side == 'L' else CENTER_Y - base
            else:
                if side == 'L':
                    y = CENTER_Y + 5
                elif side == 'R':
                    y = CENTER_Y - 5
                else:
                    y = CENTER_Y

            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': role, 'x_ft': x, 'y_ft': y})
            placed.add(p['role'])

    # Anything unrecognized - placeholder so we still end up with 11 players
    for p in players:
        if p['role'] not in placed:
            print(f"WARNING: unrecognized role '{p['role']}' -- placing at placeholder")
            coords.append({'player_number': p['number'], 'player_name': p['name'],
                            'role': p['role'], 'x_ft': 0, 'y_ft': CENTER_Y})
            placed.add(p['role'])

    return pd.DataFrame(coords)


def extract_lists_from_wide_row(row):
    role_list = [row.get(f'off_{i}_role') for i in range(1, 12)]
    number_list = [row.get(f'off_{i}_number') for i in range(1, 12)]
    name_list = [row.get(f'off_{i}_player_last_name') for i in range(1, 12)]
    qb_pos = row.get('qb_pos', row.get('QB_POS', 'S'))
    title = build_title(row.get('offensive_team_nickname', 'Offense'), row.get('offensive_formation', ''))
    return role_list, number_list, name_list, qb_pos, title


def select_wide_row(df, row_index=0, play_id=None):
    if play_id is None:
        return df.iloc[row_index]

    play_col = None
    if 'play_unique_id' in df.columns:
        play_col = 'play_unique_id'
    elif 'PLAY_UNIQUE_ID' in df.columns:
        play_col = 'PLAY_UNIQUE_ID'

    if play_col is not None:
        matched = df[df[play_col] == play_id]
        if not matched.empty:
            return matched.iloc[0]

    return df.iloc[row_index]


def extract_lists_from_long_df(df, play_unique_id=None):
    play_df = df
    if play_unique_id is None:
        play_unique_id = df['PLAY_UNIQUE_ID'].iloc[0]
    play_df = play_df[play_df['PLAY_UNIQUE_ID'] == play_unique_id].copy()

    positioning = play_df[play_df['ROLE_CATEGORY'].str.upper() == 'POSITIONING'].copy()
    positioning = positioning.drop_duplicates(subset=['PLAYER_ID', 'ROLE_ABBREV'])

    if 'FORMATION_ORDER' in positioning.columns:
        positioning = positioning.sort_values(['FORMATION_ORDER', 'PLAYER_ID'])

    role_list = positioning['ROLE_ABBREV'].tolist()
    number_list = positioning['PLAYER_NUMBER'].tolist()
    name_list = positioning['PLAYER_LAST_NAME'].tolist()

    qb_pos = 'S'
    if 'QB_POS' in play_df.columns and not play_df['QB_POS'].dropna().empty:
        qb_pos = play_df['QB_POS'].dropna().iloc[0]
    elif 'OFFENSIVE_FORMATION' in play_df.columns and not play_df['OFFENSIVE_FORMATION'].dropna().empty:
        formation = str(play_df['OFFENSIVE_FORMATION'].dropna().iloc[0]).upper()
        if formation.startswith('N'):
            qb_pos = 'N'
        elif formation.startswith('P'):
            qb_pos = 'P'
        elif formation.startswith('S'):
            qb_pos = 'S'

    offense_name = play_df['OFFENSIVE_TEAM_NICKNAME'].iloc[0] if 'OFFENSIVE_TEAM_NICKNAME' in play_df.columns else 'Offense'
    offense_form = play_df['OFFENSIVE_FORMATION'].iloc[0] if 'OFFENSIVE_FORMATION' in play_df.columns else ''
    title = build_title(offense_name, offense_form)

    return role_list, number_list, name_list, qb_pos, title


def plot_offense(df_coords, title="Offensive Formation"):
    fig, ax = plt.subplots(figsize=(4.8, 8.2))

    # Match the clean broadcast-style field look from the reference.
    ax.set_facecolor('#2f7a34')
    fig.patch.set_facecolor('#2f7a34')

    # Single LOS stripe.
    ax.axvline(LOS_X, color='white', linestyle='-', linewidth=2.4, zorder=1)

    # Players: purple fill with warm gold ring.
    ax.scatter(df_coords['x_ft'], df_coords['y_ft'],
               s=250, c='#7c4ec8', edgecolors='#f0b54a', linewidths=1.8, zorder=3)

    for _, row in df_coords.iterrows():
        num = int(row['player_number']) if not pd.isna(row['player_number']) else '?'
        ax.text(row['x_ft'], row['y_ft'], str(num),
                ha='center', va='center', fontsize=8, fontweight='bold', color='white', zorder=4)
        ax.text(row['x_ft'] + 0.85, row['y_ft'], str(row['role']),
                ha='left', va='center', fontsize=5.2, fontweight='bold', color='#f3f3f3', zorder=4)

    # Clean up axes - no numbers, no ticks, no spines
    ax.set_xlim(-23, 3)
    ax.set_ylim(0, FIELD_WIDTH)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(title, fontsize=15, color='white', fontweight='bold', pad=8)

    plt.subplots_adjust(left=0.06, right=0.98, top=0.95, bottom=0.03)
    plt.tight_layout()
    return fig, ax


def main():
    parser = argparse.ArgumentParser(description='Map offensive players to field coordinates.')
    parser.add_argument('--input', type=str, default='final_x_info_catalog_with_event.csv')
    parser.add_argument('--play-id', type=int, default=None)
    parser.add_argument('--row-index', type=int, default=0)
    parser.add_argument('--qb-pos', type=str, default=None, help='Override qb position code: N, P, or S')
    parser.add_argument('--output', type=str, default='outputs/figures/sample_offense.png')
    args = parser.parse_args()

    input_path = Path(args.input)
    df = pd.read_csv(input_path, low_memory=False)

    if {'PLAY_UNIQUE_ID', 'ROLE_CATEGORY', 'ROLE_ABBREV'}.issubset(df.columns):
        role_list, number_list, name_list, qb_pos, title = extract_lists_from_long_df(df, args.play_id)
    else:
        row = select_wide_row(df, row_index=args.row_index, play_id=args.play_id)
        role_list, number_list, name_list, qb_pos, title = extract_lists_from_wide_row(row)

    if args.qb_pos is not None:
        qb_pos = args.qb_pos

    df_coords = map_offense_to_coordinates(role_list, number_list, name_list, qb_pos=qb_pos)
    print(df_coords.sort_values(['x_ft', 'y_ft']).to_string(index=False))
    print(f"\nPlotted {len(df_coords)} offensive players (expected 11).")
    print(f"QB mode used: {normalize_qb_pos(qb_pos)}")

    fig, _ = plot_offense(df_coords, title=title)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    print(f"Saved figure to: {output_path.resolve()}")
    plt.show()


if __name__ == '__main__':
    main()