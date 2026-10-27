import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from examples import plot_offense


def main():
    df_coords = pd.DataFrame([
        {'player_number': 2,  'player_name': 'Willis',      'role': 'QB',  'x_ft': -15, 'y_ft': 52},
        {'player_number': 75, 'player_name': 'Rhyan',       'role': 'C',   'x_ft': 0,   'y_ft': 52},
        {'player_number': 65, 'player_name': 'Banks',       'role': 'LG',  'x_ft': 0,   'y_ft': 57},
        {'player_number': 63, 'player_name': 'Walker',      'role': 'LT',  'x_ft': 0,   'y_ft': 62},
        {'player_number': 71, 'player_name': 'Belton',      'role': 'RG',  'x_ft': 0,   'y_ft': 47},
        {'player_number': 77, 'player_name': 'Morgan',      'role': 'RT',  'x_ft': 0,   'y_ft': 42},
        {'player_number': 86, 'player_name': 'FitzPatrick', 'role': 'LW',  'x_ft': 0,   'y_ft': 67},
        {'player_number': 13, 'player_name': 'Wicks',       'role': 'LOR', 'x_ft': 0,   'y_ft': 95},
        {'player_number': 87, 'player_name': 'Doubs',       'role': 'RSR', 'x_ft': 0,   'y_ft': 32},
        {'player_number': 11, 'player_name': 'Reed',        'role': 'ROR', 'x_ft': -7,  'y_ft': 65},
        {'player_number': 8,  'player_name': 'Jacobs',      'role': 'RBL', 'x_ft': -16, 'y_ft': 56},
    ])

    output_dir = PROJECT_ROOT / 'outputs' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, _ = plot_offense(df_coords, title='Packers - 3L (Manual)')
    output_path = output_dir / 'Packers_3L_Manual.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print('Saved: Packers_3L_Manual.png')


if __name__ == '__main__':
    main()