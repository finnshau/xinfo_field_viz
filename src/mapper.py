"""
Map X-Info offensive players to pre-snap field coordinates.

This script reads X-Info football data and converts player roles into
2D field coordinates based on typical NFL pre-snap positioning rules.

Phase 1: Offensive-side only. Defense will be added in Phase 2.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
from roles import (
    OFFENSIVE_LINE_ROLES, TIGHT_END_ROLES, WIDE_RECEIVER_ROLES,
    RUNNING_BACK_ROLES, FULLBACK_ROLES, QB_ROLES,
    get_role_category, is_left_side, is_right_side
)

# ============================================================================
# FIELD CONSTANTS
# ============================================================================

FIELD_WIDTH = 160  # 160 feet (sideline to sideline)
CENTER_Y = 80  # Middle of field
LOS_X = 0  # Line of scrimmage
QB_NEAR_LOS_X = -2  # QB in normal/under-center position
QB_PISTOL_X = -12  # Pistol formation
QB_SHOTGUN_X = -15  # Shotgun formation

# Offensive line y-positions
OL_POSITIONS = {
    'C': 80,
    'LG': 85,
    'RG': 75,
    'LT': 90,
    'RT': 70,
}

# TE spacing from the tackle (5 feet per TE)
TE_SPACING = 5
TE_START_LEFT_Y = 95  # First left TE at y=95, then 100, 105, etc.
TE_START_RIGHT_Y = 65  # First right TE at y=65, then 60, 55, etc.

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


def map_offense_to_coordinates(role_list, number_list, name_list):
    """
    Map offensive role/number/name lists to pre-snap coordinates.

    Args:
        role_list: List of offensive role codes (e.g., QB, LT, ROR)
        number_list: List of jersey numbers aligned with role_list
        name_list: List of player names aligned with role_list

    Returns:
        DataFrame with columns: player_number, player_name, role, x_ft, y_ft
    """
    if not (len(role_list) == len(number_list) == len(name_list)):
        raise ValueError("role_list, number_list, and name_list must have the same length")

    players_dict = {}
    for role, number, name in zip(role_list, number_list, name_list):
        if pd.isna(role):
            continue

        role_code = str(role).strip()
        if not role_code or role_code.lower() == 'nan':
            continue

        players_dict[role_code] = {
            'number': number,
            'name': name,
            'role': role_code,
        }

    coordinates = []

    # QB defaults to under-center depth for this list-based API.
    if 'QB' in players_dict:
        coordinates.append({
            'player_number': players_dict['QB']['number'],
            'player_name': players_dict['QB']['name'],
            'role': 'QB',
            'x_ft': QB_NEAR_LOS_X,
            'y_ft': CENTER_Y,
        })

    for role, y_pos in OL_POSITIONS.items():
        if role in players_dict:
            player = players_dict[role]
            coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': LOS_X,
                'y_ft': y_pos,
            })

    te_roles = list(TIGHT_END_ROLES.keys())
    left_tes = []
    right_tes = []
    for role in te_roles:
        if role in players_dict:
            player = players_dict[role]
            if is_left_side(role):
                left_tes.append((role, player))
            elif is_right_side(role):
                right_tes.append((role, player))
            else:
                left_tes.append((role, player))

    for i, (role, player) in enumerate(left_tes):
        coordinates.append({
            'player_number': player['number'],
            'player_name': player['name'],
            'role': role,
            'x_ft': LOS_X,
            'y_ft': TE_START_LEFT_Y - (i * TE_SPACING),
        })

    for i, (role, player) in enumerate(right_tes):
        coordinates.append({
            'player_number': player['number'],
            'player_name': player['name'],
            'role': role,
            'x_ft': LOS_X,
            'y_ft': TE_START_RIGHT_Y + (i * TE_SPACING),
        })

    existing_ys = [c['y_ft'] for c in coordinates]
    if not existing_ys:
        left_min_y, left_max_y = CENTER_Y, FIELD_WIDTH
        right_min_y, right_max_y = 0, CENTER_Y
    else:
        left_bound = max(existing_ys)
        right_bound = min(existing_ys)
        left_min_y, left_max_y = left_bound + 2, FIELD_WIDTH
        right_min_y, right_max_y = 0, right_bound - 2

    wr_roles = list(WIDE_RECEIVER_ROLES.keys())
    left_wrs = []
    right_wrs = []
    for role in wr_roles:
        if role in players_dict:
            player = players_dict[role]
            if is_left_side(role):
                left_wrs.append((role, player))
            elif is_right_side(role):
                right_wrs.append((role, player))

    left_wrs.sort(key=lambda item: wr_alignment_rank(item[0]), reverse=True)
    right_wrs.sort(key=lambda item: wr_alignment_rank(item[0]))

    wr_x = -3
    if len(left_wrs) > 0:
        y_positions = np.linspace(left_min_y, left_max_y, len(left_wrs))
        for (role, player), y_pos in zip(left_wrs, y_positions):
            coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': wr_x,
                'y_ft': y_pos,
            })

    if len(right_wrs) > 0:
        y_positions = np.linspace(right_min_y, right_max_y, len(right_wrs))
        for (role, player), y_pos in zip(right_wrs, y_positions):
            coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': wr_x,
                'y_ft': y_pos,
            })

    rb_roles = list(RUNNING_BACK_ROLES.keys())
    fb_roles = list(FULLBACK_ROLES.keys())
    for role in rb_roles + fb_roles:
        if role in players_dict:
            player = players_dict[role]
            if role in {'RBL', 'FBL'}:
                rb_y = CENTER_Y + 8
            elif role in {'RBR', 'FBR'}:
                rb_y = CENTER_Y - 8
            else:
                rb_y = CENTER_Y

            coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': -5,
                'y_ft': rb_y,
            })

    return pd.DataFrame(coordinates)


# ============================================================================
# COORDINATE MAPPING LOGIC
# ============================================================================

class OffensiveMapper:
    """Maps offensive players to field coordinates."""
    
    def __init__(self):
        """Initialize the mapper."""
        self.coordinates = []
        self.te_left_count = 0  # Track how many left TEs we've placed
        self.te_right_count = 0  # Track how many right TEs we've placed
        
    def reset(self):
        """Reset state for a new play."""
        self.coordinates = []
        self.te_left_count = 0
        self.te_right_count = 0
    
    def get_qb_position(self, qb_position_str):
        """
        Determine QB x-coordinate based on formation.
        
        Args:
            qb_position_str: String like 'Shotgun', 'Under Center', 'Pistol', or similar
        
        Returns:
            Tuple (x, y) for QB position
        """
        # Normalize the input
        if qb_position_str is None or pd.isna(qb_position_str):
            qb_x = QB_NEAR_LOS_X
        else:
            qb_str = str(qb_position_str).lower().strip()
            if 'shotgun' in qb_str:
                qb_x = QB_SHOTGUN_X
            elif 'pistol' in qb_str:
                qb_x = QB_PISTOL_X
            else:  # Under Center or Unknown
                qb_x = QB_NEAR_LOS_X
        
        return (qb_x, CENTER_Y)
    
    def add_offensive_line(self, players_dict):
        """Place offensive line players at exact positions."""
        for role, y_pos in OL_POSITIONS.items():
            if role in players_dict:
                player = players_dict[role]
                self.coordinates.append({
                    'player_number': player['number'],
                    'player_name': player['name'],
                    'role': role,
                    'x_ft': LOS_X,
                    'y_ft': y_pos,
                })
    
    def add_tight_ends(self, players_dict):
        """
        Position tight ends starting from the tackles and spreading outward.
        
        Left TEs: Start at y=95, then 100, 105, etc. (moving toward sideline)
        Right TEs: Start at y=65, then 60, 55, etc. (moving toward sideline)
        """
        # Collect left and right tight ends separately
        te_roles = list(TIGHT_END_ROLES.keys())
        left_tes = []
        right_tes = []
        
        for role in te_roles:
            if role in players_dict:
                player = players_dict[role]
                if is_left_side(role):
                    left_tes.append((role, player))
                elif is_right_side(role):
                    right_tes.append((role, player))
                else:
                    # Unclassified TE, default to left
                    left_tes.append((role, player))
        
        # Place left TEs (moving up: 95, 100, 105, ...)
        for i, (role, player) in enumerate(left_tes):
            te_x = LOS_X
            te_y = TE_START_LEFT_Y + (i * TE_SPACING)  # 95, 100, 105, ...
            self.coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': te_x,
                'y_ft': te_y,
            })
        
        # Place right TEs (moving down: 65, 60, 55, ...)
        for i, (role, player) in enumerate(right_tes):
            te_x = LOS_X
            te_y = TE_START_RIGHT_Y - (i * TE_SPACING)  # 65, 60, 55, ...
            self.coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': te_x,
                'y_ft': te_y,
            })
    
    def get_wr_bounds(self):
        """
        Determine the bounds for WR positioning based on already-placed players.
        
        Returns:
            (left_min_y, left_max_y, right_min_y, right_max_y)
        """
        # Find the outermost placed players on each side
        existing_ys = [c['y_ft'] for c in self.coordinates]
        
        if not existing_ys:
            left_min_y, left_max_y = CENTER_Y, FIELD_WIDTH
            right_min_y, right_max_y = 0, CENTER_Y
        else:
            left_bound = max(existing_ys)
            right_bound = min(existing_ys)
            
            left_min_y, left_max_y = left_bound + 2, FIELD_WIDTH
            right_min_y, right_max_y = 0, right_bound - 2
        
        return left_min_y, left_max_y, right_min_y, right_max_y
    
    def add_wide_receivers(self, players_dict):
        """
        Position wide receivers across the field width.
        
        Left-side WRs: spread between outermost left player and upper sideline (y=160)
        Right-side WRs: spread between lower sideline (y=0) and outermost right player
        """
        wr_roles = list(WIDE_RECEIVER_ROLES.keys())
        left_wrs = []
        right_wrs = []
        
        for role in wr_roles:
            if role in players_dict:
                player = players_dict[role]
                if is_left_side(role):
                    left_wrs.append((role, player))
                elif is_right_side(role):
                    right_wrs.append((role, player))

        left_wrs.sort(key=lambda item: wr_alignment_rank(item[0]), reverse=True)
        right_wrs.sort(key=lambda item: wr_alignment_rank(item[0]))
        
        left_min_y, left_max_y, right_min_y, right_max_y = self.get_wr_bounds()
        
        # Place left WRs with some spacing
        wr_x = -3  # WRs typically 2-3 yards back from the line
        if len(left_wrs) > 0:
            y_positions = np.linspace(left_min_y, left_max_y, len(left_wrs))
            for (role, player), y_pos in zip(left_wrs, y_positions):
                self.coordinates.append({
                    'player_number': player['number'],
                    'player_name': player['name'],
                    'role': role,
                    'x_ft': wr_x,
                    'y_ft': y_pos,
                })
        
        # Place right WRs with some spacing
        if len(right_wrs) > 0:
            y_positions = np.linspace(right_min_y, right_max_y, len(right_wrs))
            for (role, player), y_pos in zip(right_wrs, y_positions):
                self.coordinates.append({
                    'player_number': player['number'],
                    'player_name': player['name'],
                    'role': role,
                    'x_ft': wr_x,
                    'y_ft': y_pos,
                })
    
    def add_running_backs(self, players_dict):
        """
        Position running backs and fullbacks behind the QB.
        
        General rule: 3-5 yards deep, offset by direction or centered.
        """
        rb_roles = list(RUNNING_BACK_ROLES.keys())
        fb_roles = list(FULLBACK_ROLES.keys())
        
        backfield_players = []
        for role in rb_roles + fb_roles:
            if role in players_dict:
                backfield_players.append((role, players_dict[role]))
        
        # Typical backfield depth: 4-5 yards
        rb_depth = -5
        
        # QB is at (QB_NEAR_LOS_X, CENTER_Y) for reference
        # Position RBs/FBs relative to QB
        for i, (role, player) in enumerate(backfield_players):
            if role in {'RBL', 'FBL'}:
                # Left side RB: offset left
                rb_y = CENTER_Y + 8
            elif role in {'RBR', 'FBR'}:
                # Right side RB: offset right
                rb_y = CENTER_Y - 8
            else:
                # Center/Middle RB: directly behind QB
                rb_y = CENTER_Y
            
            self.coordinates.append({
                'player_number': player['number'],
                'player_name': player['name'],
                'role': role,
                'x_ft': rb_depth,
                'y_ft': rb_y,
            })
    
    def add_quarterback(self, player_dict, qb_position_str):
        """Place the quarterback based on formation."""
        qb_x, qb_y = self.get_qb_position(qb_position_str)
        self.coordinates.append({
            'player_number': player_dict['number'],
            'player_name': player_dict['name'],
            'role': 'QB',
            'x_ft': qb_x,
            'y_ft': qb_y,
        })
    
    def map_play(self, play_row, qb_position_str=None):
        """
        Convert a single play row into offensive player coordinates.
        
        Args:
            play_row: A pandas Series from the X-Info CSV
            qb_position_str: Optional QB position string (Shotgun, Pistol, etc.)
        
        Returns:
            DataFrame with columns: player_number, player_name, role, x_ft, y_ft
        """
        self.reset()
        
        # Extract the 11 offensive players
        players_dict = {}
        for i in range(1, 12):  # off_1 through off_11
            prefix = f'off_{i}'
            
            # Check if we have data for this player slot
            if f'{prefix}_role' not in play_row or pd.isna(play_row[f'{prefix}_role']):
                continue
            
            role = str(play_row[f'{prefix}_role']).strip()
            if not role or role == '' or role == 'nan':
                continue
            
            # Build player dict
            player = {
                'number': play_row[f'{prefix}_number'],
                'name': f"{play_row[f'{prefix}_player_first_name']} {play_row[f'{prefix}_player_last_name']}",
                'role': role,
            }
            players_dict[role] = player
        
        # Map players by category (order matters for positioning logic)
        if 'QB' in players_dict:
            self.add_quarterback(players_dict['QB'], qb_position_str)
        
        self.add_offensive_line(players_dict)
        self.add_tight_ends(players_dict)
        self.add_wide_receivers(players_dict)
        self.add_running_backs(players_dict)
        
        return pd.DataFrame(self.coordinates)


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_offensive_formation(df_coords, title="Offensive Formation", show_role_labels=True):
    """
    Plot offensive players on a professional football field.
    Focuses on the field and players only - broadcast style visualization.
    
    Args:
        df_coords: DataFrame with player_number, player_name, role, x_ft, y_ft
        title: Title for the plot
        show_role_labels: Whether to show position labels on field
    """
    # Wide broadcast-style canvas.
    fig, ax = plt.subplots(figsize=(13, 6))
    
    # ========== AXIS SETUP (BEFORE PLAYERS) ==========
    # Keep sideline-to-sideline on y-axis, and tighten x-range to player depth.
    if len(df_coords) > 0:
        min_x = float(df_coords['x_ft'].min())
        max_x = float(df_coords['x_ft'].max())
    else:
        min_x, max_x = -20.0, 5.0

    x_pad = 2.0
    left_x = min(min_x - x_pad, -8.0)
    right_x = max(max_x + x_pad, 2.0)
    ax.set_xlim(left_x, right_x)
    ax.set_ylim(0, FIELD_WIDTH)

    # Use auto aspect for a compact football-broadcast framing.
    ax.set_aspect('auto', adjustable='box')

    # Draw line of scrimmage.
    ax.axvline(LOS_X, color='white', linewidth=2.0, alpha=0.95, zorder=1)
    
    # ========== PLAYER POSITIONING ==========
    for idx, row in df_coords.iterrows():
        # Color by position category
        category = get_role_category(row['role'])
        
        # Use team colors - offense in one color
        # (In Phase 2, we can differentiate by actual team)
        color_map = {
            'QB': '#FF1744',       # Bright red
            'OL': '#4DB8FF',       # Bright blue
            'TE': '#66FFCC',       # Cyan
            'WR': '#FFD700',       # Gold
            'RB': '#00E676',       # Bright green
            'FB': '#D946EF',       # Purple/Magenta
            'OTHER': '#CCCCCC',    # Light gray
        }
        
        color = color_map.get(category, '#CCCCCC')
        
        # Marker size tuned to avoid overlap while keeping labels readable.
        ax.scatter(
            row['x_ft'],
            row['y_ft'],
            s=360,
            c=color,
            edgecolors='white',
            linewidths=2,
            zorder=5,
            alpha=0.95,
        )
        
        # Add jersey number inside circle
        jersey_num = int(row['player_number']) if not pd.isna(row['player_number']) else '?'
        ax.text(
            row['x_ft'],
            row['y_ft'],
            f"{jersey_num}",
            ha='center',
            va='center',
            fontsize=8,
            fontweight='bold',
            color='white',
            zorder=6
        )
        
        # Optional: role label above/below circle
        if show_role_labels:
            ax.text(
                row['x_ft'],
                row['y_ft'] + 2.5,
                row['role'],
                ha='center',
                va='bottom',
                fontsize=7,
                color='white',
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7),
                zorder=4
            )
    
    # ========== AXIS FORMATTING ==========
    # Remove axes and ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Invert x-axis so QB depth goes away from camera
    # ax.invert_xaxis()
    
    # Add title above plot if provided
    if title:
        ax.text(0.5, 1.02, title, transform=ax.transAxes,
               fontsize=12, fontweight='bold', color='black',
               ha='center', va='bottom',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
    
    # Field styling to match TV-style reference.
    fig.patch.set_facecolor('#0c3b1f')
    ax.set_facecolor('#1f5f2c')
    
    plt.tight_layout()
    return fig, ax


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main script: Read CSV, map one play, visualize, and save output."""
    
    # Paths
    csv_path = Path(__file__).parent.parent / 'data' / 'raw' / 'final_x_info_catalog_with_event.csv'
    output_coords_path = Path(__file__).parent.parent / 'data' / 'processed' / 'sample_offense_coordinates.csv'
    output_figure_path = Path(__file__).parent.parent / 'outputs' / 'figures' / 'sample_offense.png'
    
    # For demo, we'll use the CSV from the attachment location
    # If not found, use the provided path
    if not csv_path.exists():
        csv_path = Path(r'c:\Users\Finn.Shaughnessy\OneDrive - Stats Perform\Microsoft Teams Chat Files\final_x_info_catalog_with_event.csv')
    
    print(f"Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} plays from X-Info data")
    
    # Get first play as sample
    sample_play = df.iloc[0]
    
    # Check for unique_play_id
    if 'unique_play_id' in sample_play:
        print(f"\nUnique Play ID: {sample_play['unique_play_id']}")
    
    print(f"\nMapping first play:")
    print(f"  Game: {sample_play['home_team_name']} vs {sample_play['away_team_name']}")
    print(f"  Offensive team: {sample_play['offensive_team_name']}")
    print(f"  Formation: {sample_play['offensive_formation']}")
    print(f"  QB Position: {sample_play.get('QB_pos', 'Unknown')}")
    
    # Print game code if available
    if 'game_code' in sample_play:
        print(f"  Game Code: {sample_play['game_code']}")
    if 'game_id' in sample_play:
        print(f"  Game ID: {sample_play['game_id']}")
    if 'nfl_game_id' in sample_play:
        print(f"  NFL Game ID: {sample_play['nfl_game_id']}")
    if 'unique_play_id' in sample_play:
        print(f"  Unique Play ID: {sample_play['unique_play_id']}")
    
    # Map the offensive players
    mapper = OffensiveMapper()
    df_coords = mapper.map_play(sample_play)
    
    print(f"\nMapped {len(df_coords)} offensive players")
    print("\nPlayer Coordinates:")
    print(df_coords.to_string())
    
    # Save coordinates
    output_coords_path.parent.mkdir(parents=True, exist_ok=True)
    df_coords.to_csv(output_coords_path, index=False)
    print(f"\nSaved coordinates to: {output_coords_path}")
    
    # Create visualization
    fig, ax = plot_offensive_formation(
        df_coords,
        title=f"{sample_play['offensive_team_name']} Offensive Formation"
    )
    
    # Save figure
    output_figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure_path, dpi=120, bbox_inches='tight', facecolor='white')
    print(f"Saved figure to: {output_figure_path}")
    
    plt.close(fig)
    print("\n✓ Complete!")


if __name__ == '__main__':
    main()
