"""
Render the 15 new S2 plays with the v2 offense visual style.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from examples import map_offense_to_coordinates, map_defense_to_coordinates, plot_offense_v2


PLAYS = [
    {
        'title':       'Cowboys - T',
        'yard_line':   4,
        'attacking_right': True,
        'play_id':     2639200,
        'game_code':   2879291,
        'qb_pos':      'S',
        'role_list':   ['LTE',      'LOR',      'ROR',      'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'RTE'      ],
        'number_list': [86,         88,         3,          4,          73,         66,         56,         52,         78,         24,         87         ],
        'name_list':   ['Schoonmaker','Lamb',   'Pickens',  'Prescott', 'Smith',    'Bass',     'Beebe',    'Booker',   'Steele',   'Davis',    'Ferguson' ],
    },
    {
        'title':       'Saints - TL',
        'yard_line':   48,
        'attacking_right': False,
        'play_id':     2571587,
        'game_code':   2879314,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LOR',      'LW',       'LT',       'LG',       'C',        'RG',       'RT',       'RBR',      'RTE',      'LSR'      ],
        'number_list': [2,          12,         7,          71,         75,         78,         68,         75,         5,          83,         22         ],
        'name_list':   ['Rattler',  'Olave',    'Hill',     'Banks Jr.','Penning',  'McCoy',    'Simpkins III','Fuaga',  'Miller',   'Johnson',  'Shaheed'  ],
    },
    {
        'title':       'Bills - TR',
        'yard_line':   46,
        'attacking_right': True,
        'play_id':     2608972,
        'game_code':   2879297,
        'qb_pos':      'N',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBL',      'RSR',      'LW',       'LTE',      'ROR'      ],
        'number_list': [17,         73,         76,         66,         64,         79,         4,          44,         88,         85,         14         ],
        'name_list':   ['Allen',    'Dawkins',  'Edwards',  'McGovern', 'Torrence', 'Brown',    'Cook III', 'Gilliam',  'Knox',     'Hawes',    'Shavers'  ],
    },
    {
        'title':       'Seahawks - N',
        'yard_line':   23,
        'attacking_right': True,
        'play_id':     2572999,
        'game_code':   2879327,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBL',      'RTE',      'LOR',      'ROR',      'RBR'      ],
        'number_list': [14,         67,         76,         61,         75,         72,         38,         88,         81,         10,         9          ],
        'name_list':   ['Darnold',  'Cross',    'Zabel',    'Sundell',  'Bradford', 'Lucas',    'Russell',  'Barner',   'Young',    'Kupp',     'Walker III'],
    },
    {
        'title':       'Steelers - 3L3',
        'yard_line':   33,
        'attacking_right': False,
        'play_id':     2563716,
        'game_code':   2879236,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBR',      'RTE',      'LOR',      'LSR',      'LIR'      ],
        'number_list': [8,          77,         73,         54,         66,         76,         20,         80,         15,         82,         4          ],
        'name_list':   ['Rodgers',  'Jones',    'Seumalo',  'Frazier',  'McCormick','Fautanu',  'Johnson',  'Washington','Skowronek','Austin III','Metcalf'  ],
    },
    {
        'title':       'Dolphins - 3R3',
        'yard_line':   31,
        'attacking_right': True,
        'play_id':     2636512,
        'game_code':   2879417,
        'qb_pos':      'S',
        'role_list':   ['ROR',      'LTE',      'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RSR',      'RBM',      'RIR'      ],
        'number_list': [17,         83,         14,         52,         72,         55,         69,         73,         85,         0,          28         ],
        'name_list':   ['Waddle',   'Waller',   'Ewers',    'Paul',     'Savaiinaea','Brewer',   'Strange',  'Jackson',  'Dulcich',  'Gordon II','Achane'   ],
    },
    {
        'title':       'Buccaneers - 5R',
        'yard_line':   35,
        'attacking_right': True,
        'play_id':     2614373,
        'game_code':   2879336,
        'qb_pos':      'S',
        'role_list':   ['LT',       'LG',       'C',        'RG',       'RT',       'LSR',      'LOR',      'RIR',      'RSR',      'ROR',      'QB'       ],
        'number_list': [78,         60,         62,         65,         67,         1,          44,         88,         2,          15,         5          ],
        'name_list':   ['Wirfs',    'Jordan',   'Barton',   'Feeney',   'Goedeke',  'White',    'Tucker',   'Otton',    'Egbuka',   'Johnson',  'Bridgewater'],
    },
    {
        'title':       'Broncos - 5L',
        'yard_line':   20,
        'attacking_right': False,
        'play_id':     2575917,
        'game_code':   2879238,
        'qb_pos':      'S',
        'role_list':   ['RT',       'LIR',      'RSR',      'LOR',      'LSR',      'ROR',      'RG',       'QB',       'LT',       'LG',       'C'        ],
        'number_list': [69,         1,          13,         19,         14,         11,         77,         10,         72,         79,         60         ],
        'name_list':   ['McGlinchey','Engram',   'Bryant',   'Mims Jr.', 'Sutton',   'Franklin', 'Meinerz',  'Nix',      'Bolles',   'Peart',    'Wattenberg'],
    },
    {
        'title':       'Browns - OS',
        'yard_line':   40,
        'attacking_right': True,
        'play_id':     2558807,
        'game_code':   2879501,
        'qb_pos':      'P',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'LW',       'ROR',      'FBL',      'LOR'      ],
        'number_list': [16,         71,         75,         55,         75,         72,         10,         83,         44,         86,         0          ],
        'name_list':   ['Flacco',   'Lucas',    'Bitonio',  'Pocic',    'Teller',   'Leveston', 'Judkins',  'Njoku',    'Fannin Jr.','Whiteheart','Bond'     ],
    },
    {
        'title':       'Broncos - I',
        'yard_line':   9,
        'attacking_right': True,
        'play_id':     2561934,
        'game_code':   2879520,
        'qb_pos':      'N',
        'role_list':   ['RG',       'RT',       'RTE',      'RBM',      'FBM',      'ROR',      'LOR',      'QB',       'LT',       'LG',       'C'        ],
        'number_list': [77,         69,         63,         27,         46,         14,         11,         10,         72,         74,         60         ],
        'name_list':   ['Meinerz',  'McGlinchey','Palczewski','Dobbins',  'Prentice', 'Sutton',   'Franklin', 'Nix',      'Bolles',   'Powers',   'Wattenberg'],
    },
    {
        'title':       'Jets - TIL',
        'yard_line':   43,
        'attacking_right': False,
        'play_id':     2629860,
        'game_code':   2879326,
        'qb_pos':      'N',
        'role_list':   ['LG',       'C',        'RG',       'RT',       'RTE',      'RBM',      'FBM',      'RW',       'LOR',      'QB',       'LT'       ],
        'number_list': [74,         71,         66,         70,         61,         20,         47,         89,         10,         4,          74         ],
        'name_list':   ['Simpson',  'Myers',    'Tippmann', 'Membou',   'Mitchell','Hall',     'Beck',     'Ruckert',  'Lazard',   'Cook',     'Fashanu'  ],
    },
    {
        'title':       'Saints - TIR',
        'yard_line':   49,
        'attacking_right': True,
        'play_id':     2635916,
        'game_code':   2879396,
        'qb_pos':      'N',
        'role_list':   ['FBM',      'RW',       'LTE',      'ROR',      'QB',       'LT',       'LG',       'C',        'RT',       'RG',       'RBM'      ],
        'number_list': [7,          83,         87,         12,         6,          71,         77,         77,         75,         68,         30         ],
        'name_list':   ['Hill',     'Johnson',  'Moreau',   'Olave',    'Shough',   'Banks Jr.','Radunz',   'Fortner',  'Fuaga',    'Simpkins III','Estime'],
    },
    {
        'title':       'Titans - TWL',
        'yard_line':   33,
        'attacking_right': True,
        'play_id':     2573927,
        'game_code':   2879323,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RW',       'LW',       'LOR',      'LSR',      'ROR'      ],
        'number_list': [1,          75,         77,         53,         70,         68,         2,          85,         17,         0,          5          ],
        'name_list':   ['Ward',     'Moore Jr.','Skoronski', 'Cushenberry III','Zeitler','Udoh',    'Spears',   'Okonkwo',  'Lockett',  'Ridley',   'Ayomanor' ],
    },
    {
        'title':       'Patriots - TWR',
        'yard_line':   14,
        'attacking_right': True,
        'play_id':     2609910,
        'game_code':   2879303,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'LOR',      'LTE',      'LW',       'RSR',      'ROR'      ],
        'number_list': [10,         66,         77,         67,         71,         76,         32,         81,         85,         8,          37         ],
        'name_list':   ['Maye',     'Campbell', 'Brown',    'Bradbury', 'Onwenu',   'Moses',    'Henderson','Hooper',   'Henry',    'Diggs',    'Westover' ],
    },
    {
        'title':       'Cowboys - 3TBL',
        'yard_line':   28,
        'attacking_right': True,
        'play_id':     2572283,
        'game_code':   2879318,
        'qb_pos':      'N',
        'role_list':   ['RW',       'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'LTE',      'RTE',      'LOR'      ],
        'number_list': [89,         4,          71,         75,         67,         66,         78,         33,         87,         86,         3          ],
        'name_list':   ['Spann-Ford','Prescott', 'Thomas',   'Adeniji',  'Hoffman',  'Bass',     'Steele',   'Williams', 'Ferguson', 'Schoonmaker','Pickens'],
    },
]


def main():
    output_dir = PROJECT_ROOT / 'outputs' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = PROJECT_ROOT / 'data' / 'raw' / 'xinfo_catalog2025_similar_plays'
    catalog_df = pd.read_csv(catalog_path, low_memory=False)

    play_col = 'play_unique_id' if 'play_unique_id' in catalog_df.columns else 'PLAY_UNIQUE_ID'
    game_col = 'game_code' if 'game_code' in catalog_df.columns else 'GAME_CODE'

    print(f"Rendering {len(PLAYS)} plays with v2 visuals")

    for play in PLAYS:
        df_off_coords = map_offense_to_coordinates(
            role_list=play['role_list'],
            number_list=play['number_list'],
            name_list=play['name_list'],
            qb_pos=play['qb_pos'],
        )

        row_match = catalog_df[
            (catalog_df[play_col] == play['play_id']) &
            (catalog_df[game_col] == play['game_code'])
        ]
        if row_match.empty:
            row_match = catalog_df[catalog_df[play_col] == play['play_id']]
        row = row_match.iloc[0] if not row_match.empty else pd.Series(dtype=object)

        # ---- LOAD DEFENSIVE DATA FROM xinfo_catalog2025_similar_plays ----
        def_role_list   = []
        def_number_list = []
        def_name_list   = []
        def_press_list  = []

        for i in range(1, 12):
            role  = row.get(f'def_{i}_role')
            num   = row.get(f'def_{i}_number')
            name  = row.get(f'def_{i}_player_last_name')
            press = row.get(f'def_{i}_press', 0)

            if pd.notna(role) and str(role).strip() not in ('', 'nan'):
                def_role_list.append(str(role).strip())
                def_number_list.append(int(float(num)) if pd.notna(num) else 0)
                def_name_list.append(str(name).strip() if pd.notna(name) else '')
                def_press_list.append(int(float(press)) if pd.notna(press) else 0)

        print(f'  {play["title"]} — defensive roles: {def_role_list}')

        df_def_coords = map_defense_to_coordinates(
            role_list=def_role_list,
            number_list=def_number_list,
            name_list=def_name_list,
            press_list=def_press_list,
            ol_coords=df_off_coords
        )

        print(f'  {play["title"]} — {len(df_def_coords)} defensive players placed')

        fig, _ = plot_offense_v2(
            df_coords=df_off_coords,
            df_def_coords=df_def_coords,
            title=play['title'],
            yard_line=play['yard_line'],
            attacking_right=play['attacking_right']
        )

        safe_title = play['title'].replace(' ', '_').replace('/', '_')
        out_path = output_dir / f"S2_V2_{safe_title}.png"
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {out_path.resolve()}")
        plt.close(fig)

    print(f"Rendered {len(PLAYS)} v2 figures successfully.")


if __name__ == '__main__':
    main()
