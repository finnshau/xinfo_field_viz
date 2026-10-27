"""
xInfoViz - 6 Formation Visualizations
=================================================
Uses the exact same rule-based logic as examples.py.
Player data pulled directly from final_x_info_catalog_with_event.csv.

Plays:
  1. Steelers  3L3  - play_unique_id: 2563652 | game_code: 2879236
  2. Seahawks  GI   - play_unique_id: 2622261 | game_code: 2879409
  3. Jets      TIL  - play_unique_id: 2629860 | game_code: 2879326
  4. Cowboys   3RBG - play_unique_id: 2614078 | game_code: 2879329
  5. Browns    3L   - play_unique_id: 2607473 | game_code: 2879549
  6. Packers   3L   - play_unique_id: 2633838 | game_code: 2879223
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from examples import map_offense_to_coordinates, plot_offense

# ============================================================================
# PLAY DEFINITIONS
# Data pulled exactly from the x_info catalog - no placeholders.
# Same structure as the Cowboys 3L example in examples.py.
# ============================================================================

PLAYS = [

    # --------------------------------------------------------------------------
    # Play 1: Steelers 3L3
    # play_unique_id: 2563652 | game_code: 2879236
    # Week 4 | Period 3 | 11:43 remaining | Steelers vs Vikings | 14-6
    # All 3 WRs trips left (LOR, LSR, LIR), 1 TE right, 1 RB right, P role
    # --------------------------------------------------------------------------
    {
        'title':       'Steelers - 3L3',
        'play_id':     2563652,
        'game_code':   2879236,
        'qb_pos':      'S',
        'role_list':   ['P',               'LOR',          'QB',           'LT',             'LG',           'C',           'RT',          'RBR',            'RTE',              'LIR',      'LSR'           ],
        'number_list': [66,                15,             8,              77,               73,             54,            76,            1,                80,                 4,          82              ],
        'name_list':   ['McCormick',       'Skowronek',    'Rodgers',      'Jones',          'Seumalo',      'Frazier',     'Fautanu',     'Gainwell',       'Washington',       'Metcalf',  'Austin'        ],
    },

    # --------------------------------------------------------------------------
    # Play 2: Seahawks GI (Goal Line I-Formation)
    # play_unique_id: 2622261 | game_code: 2879409
    # Week 14 | Period 4 | 9:22 remaining | Falcons vs Seahawks | 9-30
    # 2 TEs, 1 Wing, FB + RB stacked in I-form, 0 WRs
    # --------------------------------------------------------------------------
    {
        'title':       'Seahawks - GI',
        'play_id':     2622261,
        'game_code':   2879409,
        'qb_pos':      'N',
        'role_list':   ['QB',      'LT',    'LG',    'C',         'RG',       'RT',     'RBM',   'FBM',   'RW',       'LTE',    'RTE'  ],
        'number_list': [14,        67,      76,      55,          75,         72,        9,       40,      89,         88,       99     ],
        'name_list':   ['Darnold', 'Cross', 'Zabel', 'Oluwatimi', 'Bradford', 'Lucas',  'Walker','Ouzts', 'Kallerup', 'Barner', 'Jones'],
    },

    # --------------------------------------------------------------------------
    # Play 3: Jets TIL (2 TE + I-Form Backs)
    # play_unique_id: 2629860 | game_code: 2879326
    # Week 15 | Period 2 | 11:32 remaining | Jaguars vs Jets | 21-7
    # 2 TEs (RTE + RW), FB + RB in I-form, 1 WR left
    # --------------------------------------------------------------------------
    {
        'title':       'Jets - TIL',
        'play_id':     2629860,
        'game_code':   2879326,
        'qb_pos':      'N',
        'role_list':   ['LG',      'C',     'RG',       'RT',     'RTE',     'RBM',  'FBM',  'RW',      'LOR',    'QB',   'LT'      ],
        'number_list': [74,        71,      66,         70,       61,        20,     47,     89,        10,       4,      74        ],
        'name_list':   ['Simpson', 'Myers', 'Tippmann', 'Membou', 'Mitchell','Hall', 'Beck', 'Ruckert', 'Lazard', 'Cook', 'Fashanu' ],
    },

    # --------------------------------------------------------------------------
    # Play 4: Cowboys 3RBG (Three backs + 2 TEs, no WRs)
    # play_unique_id: 2614078 | game_code: 2879329
    # Week 12 | Period 4 | 0:04 remaining | Cowboys vs Eagles | 21-21
    # QB, VSF, PAL, PAR, LTE, RTE - completely breaks rule-based logic
    # --------------------------------------------------------------------------
    {
        'title':       'Cowboys - 3RBG',
        'play_id':     2614078,
        'game_code':   2879329,
        'qb_pos':      'N',
        'role_list':   ['QB',       'LG',    'C',     'RG',     'RT',     'LT',     'PAL',      'PAR',    'LTE',        'RTE',         'VSF'      ],
        'number_list': [4,          73,      56,      52,       78,       71,       33,         40,       89,           86,            19         ],
        'name_list':   ['Prescott', 'Smith', 'Beebe', 'Booker', 'Steele', 'Thomas', 'Williams', 'Luepke', 'Spann-Ford', 'Schoonmaker', 'Flournoy' ],
    },

    # --------------------------------------------------------------------------
    # Play 5: Browns 3L
    # play_unique_id: 2607473 | game_code: 2879549
    # Week 11 | Period 4 | 1:08 remaining | Browns vs Ravens | 16-23
    # Same exact roles as Cowboys 3L (play 2545171) - gap demo pairing
    # --------------------------------------------------------------------------
    {
        'title':       'Browns - 3L',
        'play_id':     2607473,
        'game_code':   2879549,
        'qb_pos':      'S',
        'role_list':   ['RT',      'QB',      'LG',      'C',     'RG',     'LT',       'RBL',  'RW',    'ROR',     'LOR',       'LSR'  ],
        'number_list': [78,        2,         75,        55,      75,       72,         34,     83,      19,        84,          3      ],
        'name_list':   ['Conklin', 'Sanders', 'Bitonio', 'Pocic', 'Teller', 'Leveston', 'Ford', 'Njoku', 'Tillman', 'Larvadain', 'Jeudy'],
    },

    # --------------------------------------------------------------------------
    # Play 6: Packers 3L
    # play_unique_id: 2633838 | game_code: 2879223
    # Week 16 | Period 3 | 11:27 remaining | Bears vs Packers | 3-6
    # Same exact roles as Cowboys 3L (play 2545171) - gap demo pairing
    # --------------------------------------------------------------------------
    {
        'title':       'Packers - 3L',
        'play_id':     2633838,
        'game_code':   2879223,
        'qb_pos':      'S',
        'role_list':   ['QB',    'LT',     'LG',    'C',     'RG',     'RT',     'RBL',   'LW',          'RSR',   'LOR',   'ROR'  ],
        'number_list': [2,       63,       65,      75,      71,       77,       8,       86,            87,      13,      11     ],
        'name_list':   ['Willis','Walker', 'Banks', 'Rhyan', 'Belton', 'Morgan', 'Jacobs','FitzPatrick', 'Doubs', 'Wicks', 'Reed' ],
    },

    # --------------------------------------------------------------------------
    # Play 7: Bears T
    # play_unique_id: 2616281 | game_code: 2879225
    # Week 13 | Period 4 | 13:34 remaining | Eagles vs Bears | 122(0)
    # T-formation with RBM (under center), LTE, and spread receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Bears - T',
        'play_id':     2616281,
        'game_code':   2879225,
        'qb_pos':      'N',
        'role_list':   ['QB',       'LT',       'LG',       'C',       'RG',       'RT',       'RBM',      'LTE',     'LOR',      'LW'       ],
        'number_list': [18,         75,         62,         52,         73,         58,         25,         85,        15,         84         ],
        'name_list':   ['Williams', 'Trapilo',  'Thuney',   'Dalman',   'Jackson',  'Wright',   'Monangai', 'Kmet',    'Odunze',   'Loveland'],
    },

    # --------------------------------------------------------------------------
    # Play 8: Colts TL
    # play_unique_id: 2597951 | game_code: 2879240
    # Week 10 | Period 1 | 2:39 remaining | Colts vs Falcons | 122(0)
    # Tight left with SL (side back left), multiple TEs and receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Colts - TL',
        'play_id':     2597951,
        'game_code':   2879240,
        'qb_pos':      'P',
        'role_list':   ['SL',      'RTE',       'RW',       'LSR',       'LOR',      'QB',      'LT',       'LG',      'C',        'RG',       'RT'       ],
        'number_list': [28,        81,          84,         11,          14,         17,        79,         56,        60,         71,         71         ],
        'name_list':   ['Taylor',  'Alie-Cox',  'Warren',   'Pittman Jr.','Pierce',   'Jones',   'Raimann',  'Nelson',  'Bortolini','Goncalves','Smith'    ],
    },

    # --------------------------------------------------------------------------
    # Play 9: Broncos TR
    # play_unique_id: 2639880 | game_code: 2879224
    # Week 17 | Period 1 | 13:39 remaining | Chiefs vs Broncos | 212(1)
    # Tight right with Pistol, LW, LTE, and multiple receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Broncos - TR',
        'play_id':     2639880,
        'game_code':   2879224,
        'qb_pos':      'P',
        'role_list':   ['P',       'LW',        'LTE',      'RSR',      'ROR',      'QB',      'LT',       'LG',         'C',        'RG',       'RT'       ],
        'number_list': [12,        46,          82,         83,         14,         10,        72,         63,           54,         77,         69         ],
        'name_list':   ['Harvey',  'Prentice', 'Trautman', 'Bandy',    'Sutton',   'Nix',     'Bolles',   'Palczewski', 'Forsyth',  'Meinerz',  'McGlinchey'],
    },

    # --------------------------------------------------------------------------
    # Play 10: Vikings N
    # play_unique_id: 2639565 | game_code: 2879292
    # Week 17 | Period 1 | 2:24 remaining | Vikings vs Lions | 212(1)
    # Under center with NP (neutral back), RTE, and balanced receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Vikings - N',
        'play_id':     2639565,
        'game_code':   2879292,
        'qb_pos':      'N',
        'role_list':   ['QB',      'LG',       'C',       'NP',      'RTE',     'ROR',      'RG',       'RT',       'RBR',      'LOR'      ],
        'number_list': [12,        74,         65,        30,        84,        9,          76,         64,         33,         18         ],
        'name_list':   ['Brosmer', 'Jackson',  'Jurgens', 'Ham',     'Oliver',  'Nailor',   'Fries',    'Brandel',  'Jones Sr.','Jefferson'],
    },

    # --------------------------------------------------------------------------
    # Play 11: Eagles 3R3
    # play_unique_id: 2633290 | game_code: 2879222
    # Week 16 | Period 1 | 10:08 remaining | Commanders vs Eagles | 113(0)
    # 3 receivers right, balanced line with multiple options
    # --------------------------------------------------------------------------
    {
        'title':       'Eagles - 3R3',
        'play_id':     2633290,
        'game_code':   2879222,
        'qb_pos':      'S',
        'role_list':   ['RG',      'RT',       'RBR',      'LTE',      'RIR',      'ROR',      'RSR',      'QB',      'LT',       'LG',       'C'        ],
        'number_list': [56,        74,         28,         81,         11,         4,          6,          1,         68,         69,         51         ],
        'name_list':   ['Steen',   'Johnson',  'Shipley',  'Calcaterra','Brown',    'Dotson',   'Smith',    'Hurts',   'Mailata',  'Dickerson','Jurgens'  ],
    },

    # --------------------------------------------------------------------------
    # Play 12: Eagles 5R
    # play_unique_id: 2633325 | game_code: 2879222
    # Week 16 | Period 1 | 4:08 remaining | Commanders vs Eagles | 113(0)
    # 5 receivers right with spread formation
    # --------------------------------------------------------------------------
    {
        'title':       'Eagles - 5R',
        'play_id':     2633325,
        'game_code':   2879222,
        'qb_pos':      'N',
        'role_list':   ['LG',      'C',       'RG',       'RT',       'ROR',      'LOR',      'RIR',      'RSR',      'LSR',      'QB',       'LT'       ],
        'number_list': [69,        51,        56,         74,         26,         88,         11,         4,          6,          1,          68         ],
        'name_list':   ['Dickerson','Jurgens', 'Steen',    'Johnson',  'Barkley',  'Goedert',  'Brown',    'Dotson',   'Smith',    'Hurts',    'Mailata'  ],
    },

    # --------------------------------------------------------------------------
    # Play 13: Eagles 5L
    # play_unique_id: 2545213 | game_code: 2879178
    # Week 1 | Period 2 | 14:12 remaining | Eagles vs Cowboys | 113(0)
    # 5 receivers left in spread formation
    # --------------------------------------------------------------------------
    {
        'title':       'Eagles - 5L',
        'play_id':     2545213,
        'game_code':   2879178,
        'qb_pos':      'N',
        'role_list':   ['LSR',     'RSR',      'ROR',      'QB',      'LT',       'LG',       'C',        'RG',       'RT',       'LOR',      'LIR'      ],
        'number_list': [4,         6,          11,         1,         68,         69,         51,         56,         65,         26,         88         ],
        'name_list':   ['Dotson',  'Smith',    'Brown',    'Hurts',   'Mailata',  'Dickerson','Jurgens',  'Steen',    'Johnson',  'Barkley',  'Goedert'  ],
    },

    # --------------------------------------------------------------------------
    # Play 14: Cowboys OS
    # play_unique_id: 2615231 | game_code: 2879287
    # Week 13 | Period 2 | 15:00 remaining | Cowboys vs Chiefs | 212(0)
    # Offset spread with Pistol, FBR, RBM, and multiple TEs
    # --------------------------------------------------------------------------
    {
        'title':       'Cowboys - OS',
        'play_id':     2615231,
        'game_code':   2879287,
        'qb_pos':      'P',
        'role_list':   ['QB',       'ROR',      'LOR',      'P',       'RG',       'RT',       'RBM',      'FBR',      'RTE',      'LT',       'LG'       ],
        'number_list': [4,          19,         88,         56,        52,         78,         24,         40,         89,         71,         73         ],
        'name_list':   ['Prescott', 'Flournoy', 'Lamb',     'Beebe',   'Booker',   'Steele',   'Davis',    'Luepke',   'Spann-Ford','Thomas',  'Smith'    ],
    },

    # --------------------------------------------------------------------------
    # Play 15: Seahawks I
    # play_unique_id: 2645543 | game_code: 2879511
    # Week 18 | Period 1 | 5:16 remaining | 49ers vs Seahawks | 212(1)
    # I-formation with FBM, RBM, LTE, and balanced receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Seahawks - I',
        'play_id':     2645543,
        'game_code':   2879511,
        'qb_pos':      'N',
        'role_list':   ['QB',      'LG',       'C',        'RG',       'RT',       'RBM',      'FBM',      'LTE',      'ROR',      'LOR'      ],
        'number_list': [14,        76,         61,         75,         72,         9,          40,         88,         22,         11         ],
        'name_list':   ['Darnold', 'Zabel',    'Sundell',  'Bradford', 'Lucas',    'Walker III','Ouzts',    'Barner',   'Shaheed',  'Smith-Njigba'],
    },

    # --------------------------------------------------------------------------
    # Play 16: Cardinals TIR
    # play_unique_id: 2616601 | game_code: 2879370
    # Week 13 | Period 3 | 12:09 remaining | Buccaneers vs Cardinals | 121(0)
    # Tight I-form right with Pistol, two TEs, and spread receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Cardinals - TIR',
        'play_id':     2616601,
        'game_code':   2879370,
        'qb_pos':      'P',
        'role_list':   ['P',       'RTE',      'LTE',      'ROR',      'QB',      'LT',       'LG',       'C',        'RG',       'RT',       'RBM'      ],
        'number_list': [84,        85,         78,         89,         7,         70,         67,         72,         74,         68,         20         ],
        'name_list':   ['Higgins', 'McBride',  'Fryar',    'Weaver',   'Brissett','Johnson Jr.','Brown',   'Froholdt', 'Adams',    'Beachum',  'Knight'   ],
    },

    # --------------------------------------------------------------------------
    # Play 17: Bears TWL
    # play_unique_id: 2610927 | game_code: 2879300
    # Week 12 | Period 4 | 5:30 remaining | Bears vs Steelers | 113(0)
    # Tight with left spread, shotgun with RW/LW and multiple receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Bears - TWL',
        'play_id':     2610927,
        'game_code':   2879300,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RW',       'LW',       'LSR',      'LOR'      ],
        'number_list': [18,         75,         62,         52,         73,         58,         4,          84,         10,         15         ],
        'name_list':   ['Williams', 'Trapilo',  'Thuney',   'Dalman',   'Jackson',  'Wright',   'Swift',    'Loveland', 'Burden III','Odunze'   ],
    },

    # --------------------------------------------------------------------------
    # Play 18: Vikings TWR
    # play_unique_id: 2563672 | game_code: 2879236
    # Week 4 | Period 3 | 7:42 remaining | Steelers vs Vikings | 113(0)
    # Tight with right spread, NP (neutral back) and multiple receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Vikings - TWR',
        'play_id':     2563672,
        'game_code':   2879236,
        'qb_pos':      'N',
        'role_list':   ['QB',      'NP',       'LT',       'LG',       'RG',       'C',        'RW',       'LW',       'RSR',      'ROR'      ],
        'number_list': [11,        3,          71,         64,         76,         65,         36,         87,         19,         18         ],
        'name_list':   ['Wentz',   'Addison',  'Darrisaw', 'Brandel',  'Fries',    'Jurgens',  'Scott',    'Hockenson','Thielen',  'Jefferson'],
    },

    # --------------------------------------------------------------------------
    # Play 19: Cowboys 3TBL
    # play_unique_id: 2572283 | game_code: 2879318
    # Week 5 | Period 4 | 13:06 remaining | Jets vs Cowboys | 131(0)
    # 3-tight backfield left with RBM, two TEs, and balanced receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Cowboys - 3TBL',
        'play_id':     2572283,
        'game_code':   2879318,
        'qb_pos':      'N',
        'role_list':   ['RW',       'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'LTE',      'RTE',      'LOR'      ],
        'number_list': [89,         4,          71,         75,         67,         66,         78,         33,         87,         86,         3          ],
        'name_list':   ['Spann-Ford','Prescott','Thomas',   'Adeniji',  'Hoffman',  'Bass',     'Steele',   'Williams', 'Ferguson', 'Schoonmaker','Pickens'],
    },

    # --------------------------------------------------------------------------
    # Play 20: Giants N3L
    # play_unique_id: 2612232 | game_code: 2879305
    # Week 12 | Period 4 | 8:10 remaining | Lions vs Giants | 113(0)
    # Neutral 3 left with FBL, RBR, and multiple receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Giants - N3L',
        'play_id':     2612232,
        'game_code':   2879305,
        'qb_pos':      'N',
        'role_list':   ['LG',       'C',        'P',        'RT',       'RBR',      'FBL',      'LSR',      'LOR',      'ROR',      'P',        'QB'       ],
        'number_list': [76,         61,         74,         72,         29,         84,         4,          18,         89,         78,         19         ],
        'name_list':   ['Runyan Jr.','Schmitz Jr.','Van Roten','Eluemunor','Tracy Jr.','Johnson',  'Robinson', 'Slayton',  'Hodgins',  'Thomas',   'Winston'  ],
    },

    # --------------------------------------------------------------------------
    # Play 21: Patriots N3R
    # play_unique_id: 2546283 | game_code: 2879301
    # Week 1 | Period 3 | 14:55 remaining | Patriots vs Raiders | 212(0)
    # Neutral 3 right with RBL/RBR stacked and balanced receivers
    # --------------------------------------------------------------------------
    {
        'title':       'Patriots - N3R',
        'play_id':     2546283,
        'game_code':   2879301,
        'qb_pos':      'N',
        'role_list':   ['LG',       'C',        'LT',       'RG',       'RT',       'RBL',      'RBR',      'LOR',      'RSR',      'ROR',      'QB'       ],
        'number_list': [55,         67,         66,         71,         76,         32,         38,         85,         9,          13,         10         ],
        'name_list':   ['Wilson',   'Bradbury', 'Campbell', 'Onwenu',   'Moses',    'Henderson','Stevenson','Henry',    'Boutte',   'Hollins',  'Maye'     ],
    },

    # --------------------------------------------------------------------------
    # Play 22: Cowboys T
    # play_id: 2639200 | game_code: 2879291
    # Week 17 | P2 | 8:34 | Commanders vs Cowboys | 122(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Cowboys - T',
        'play_id':     2639200,
        'game_code':   2879291,
        'qb_pos':      'S',
        'role_list':   ['LTE',      'LOR',      'ROR',      'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'RTE'      ],
        'number_list': [86,         88,         3,          4,          73,         66,         56,         52,         78,         24,         87         ],
        'name_list':   ['Schoonmaker','Lamb',   'Pickens',  'Prescott', 'Smith',    'Bass',     'Beebe',    'Booker',   'Steele',   'Davis',    'Ferguson' ],
    },

    # --------------------------------------------------------------------------
    # Play 23: Saints TL
    # play_id: 2571587 | game_code: 2879314
    # Week 5 | P1 | 7:08 | Saints vs Giants | 112(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Saints - TL',
        'play_id':     2571587,
        'game_code':   2879314,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LOR',      'LW',       'LT',       'LG',       'C',        'RG',       'RT',       'RBR',      'RTE',      'LSR'      ],
        'number_list': [2,          12,         7,          71,         75,         78,         68,         75,         5,          83,         22         ],
        'name_list':   ['Rattler',  'Olave',    'Hill',     'Banks Jr.','Penning',  'McCoy',    'Simpkins III','Fuaga',  'Miller',   'Johnson',  'Shaheed'  ],
    },

    # --------------------------------------------------------------------------
    # Play 24: Bills TR
    # play_id: 2608972 | game_code: 2879297
    # Week 12 | P4 | 13:29 | Texans vs Bills | 221(1)
    # --------------------------------------------------------------------------
    {
        'title':       'Bills - TR',
        'play_id':     2608972,
        'game_code':   2879297,
        'qb_pos':      'N',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBL',      'RSR',      'LW',       'LTE',      'ROR'      ],
        'number_list': [17,         73,         76,         66,         64,         79,         4,          44,         88,         85,         14         ],
        'name_list':   ['Allen',    'Dawkins',  'Edwards',  'McGovern', 'Torrence', 'Brown',    'Cook III', 'Gilliam',  'Knox',     'Hawes',    'Shavers'  ],
    },

    # --------------------------------------------------------------------------
    # Play 25: Seahawks N
    # play_id: 2572999 | game_code: 2879327
    # Week 5 | P3 | 14:54 | Seahawks vs Buccaneers | 212(1)
    # --------------------------------------------------------------------------
    {
        'title':       'Seahawks - N',
        'play_id':     2572999,
        'game_code':   2879327,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBL',      'RTE',      'LOR',      'ROR',      'RBR'      ],
        'number_list': [14,         67,         76,         61,         75,         72,         38,         88,         81,         10,         9          ],
        'name_list':   ['Darnold',  'Cross',    'Zabel',    'Sundell',  'Bradford', 'Lucas',    'Russell',  'Barner',   'Young',    'Kupp',     'Walker III'],
    },

    # --------------------------------------------------------------------------
    # Play 26: Steelers 3L3
    # play_id: 2563716 | game_code: 2879236
    # Week 4 | P4 | 14:21 | Steelers vs Vikings | 113(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Steelers - 3L3',
        'play_id':     2563716,
        'game_code':   2879236,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBR',      'RTE',      'LOR',      'LSR',      'LIR'      ],
        'number_list': [8,          77,         73,         54,         66,         76,         20,         80,         15,         82,         4          ],
        'name_list':   ['Rodgers',  'Jones',    'Seumalo',  'Frazier',  'McCormick','Fautanu',  'Johnson',  'Washington','Skowronek','Austin III','Metcalf'  ],
    },

    # --------------------------------------------------------------------------
    # Play 27: Dolphins 3R3
    # play_id: 2636512 | game_code: 2879417
    # Week 16 | P3 | 9:37 | Dolphins vs Bengals | 221(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Dolphins - 3R3',
        'play_id':     2636512,
        'game_code':   2879417,
        'qb_pos':      'S',
        'role_list':   ['ROR',      'LTE',      'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RSR',      'RBM',      'RIR'      ],
        'number_list': [17,         83,         14,         52,         72,         55,         69,         73,         85,         0,          28         ],
        'name_list':   ['Waddle',   'Waller',   'Ewers',    'Paul',     'Savaiinaea','Brewer',   'Strange',  'Jackson',  'Dulcich',  'Gordon II','Achane'   ],
    },

    # --------------------------------------------------------------------------
    # Play 28: Buccaneers 5R
    # play_id: 2614373 | game_code: 2879336
    # Week 12 | P4 | 13:35 | Rams vs Buccaneers | 212(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Buccaneers - 5R',
        'play_id':     2614373,
        'game_code':   2879336,
        'qb_pos':      'S',
        'role_list':   ['LT',       'LG',       'C',        'RG',       'RT',       'LSR',      'LOR',      'RIR',      'RSR',      'ROR',      'QB'       ],
        'number_list': [78,         60,         62,         65,         67,         1,          44,         88,         2,          15,         5          ],
        'name_list':   ['Wirfs',    'Jordan',   'Barton',   'Feeney',   'Goedeke',  'White',    'Tucker',   'Otton',    'Egbuka',   'Johnson',  'Bridgewater'],
    },

    # --------------------------------------------------------------------------
    # Play 29: Broncos 5L
    # play_id: 2575917 | game_code: 2879238
    # Week 6 | P4 | 6:43 | Jets vs Broncos | 014(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Broncos - 5L',
        'play_id':     2575917,
        'game_code':   2879238,
        'qb_pos':      'S',
        'role_list':   ['RT',       'LIR',      'RSR',      'LOR',      'LSR',      'ROR',      'RG',       'QB',       'LT',       'LG',       'C'        ],
        'number_list': [69,         1,          13,         19,         14,         11,         77,         10,         72,         79,         60         ],
        'name_list':   ['McGlinchey','Engram',   'Bryant',   'Mims Jr.', 'Sutton',   'Franklin', 'Meinerz',  'Nix',      'Bolles',   'Peart',    'Wattenberg'],
    },

    # --------------------------------------------------------------------------
    # Play 30: Browns OS
    # play_id: 2558807 | game_code: 2879501
    # Week 3 | P3 | 2:05 | Browns vs Packers | 131(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Browns - OS',
        'play_id':     2558807,
        'game_code':   2879501,
        'qb_pos':      'P',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'LW',       'ROR',      'FBL',      'LOR'      ],
        'number_list': [16,         71,         75,         55,         75,         72,         10,         83,         44,         86,         0          ],
        'name_list':   ['Flacco',   'Lucas',    'Bitonio',  'Pocic',    'Teller',   'Leveston', 'Judkins',  'Njoku',    'Fannin Jr.','Whiteheart','Bond'     ],
    },

    # --------------------------------------------------------------------------
    # Play 31: Broncos I
    # play_id: 2561934 | game_code: 2879520
    # Week 3 | P2 | 10:23 | Chargers vs Broncos | 202(1)
    # --------------------------------------------------------------------------
    {
        'title':       'Broncos - I',
        'play_id':     2561934,
        'game_code':   2879520,
        'qb_pos':      'N',
        'role_list':   ['RG',       'RT',       'RTE',      'RBM',      'FBM',      'ROR',      'LOR',      'QB',       'LT',       'LG',       'C'        ],
        'number_list': [77,         69,         63,         27,         46,         14,         11,         10,         72,         74,         60         ],
        'name_list':   ['Meinerz',  'McGlinchey','Palczewski','Dobbins',  'Prentice', 'Sutton',   'Franklin', 'Nix',      'Bolles',   'Powers',   'Wattenberg'],
    },

    # --------------------------------------------------------------------------
    # Play 32: Jets TIL
    # play_id: 2629860 | game_code: 2879326
    # Week 15 | P2 | 11:32 | Jaguars vs Jets | 211(1)
    # --------------------------------------------------------------------------
    {
        'title':       'Jets - TIL (S2)',
        'play_id':     2629860,
        'game_code':   2879326,
        'qb_pos':      'N',
        'role_list':   ['LG',       'C',        'RG',       'RT',       'RTE',      'RBM',      'FBM',      'RW',       'LOR',      'QB',       'LT'       ],
        'number_list': [74,         71,         66,         70,         61,         20,         47,         89,         10,         4,          74         ],
        'name_list':   ['Simpson',  'Myers',    'Tippmann', 'Membou',   'Mitchell','Hall',     'Beck',     'Ruckert',  'Lazard',   'Cook',     'Fashanu'  ],
    },

    # --------------------------------------------------------------------------
    # Play 33: Saints TIR
    # play_id: 2635916 | game_code: 2879396
    # Week 16 | P1 | 9:43 | Saints vs Jets | 121(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Saints - TIR',
        'play_id':     2635916,
        'game_code':   2879396,
        'qb_pos':      'N',
        'role_list':   ['FBM',      'RW',       'LTE',      'ROR',      'QB',       'LT',       'LG',       'C',        'RT',       'RG',       'RBM'      ],
        'number_list': [7,          83,         87,         12,         6,          71,         77,         77,         75,         68,         30         ],
        'name_list':   ['Hill',     'Johnson',  'Moreau',   'Olave',    'Shough',   'Banks Jr.','Radunz',   'Fortner',  'Fuaga',    'Simpkins III','Estime'],
    },

    # --------------------------------------------------------------------------
    # Play 34: Titans TWL
    # play_id: 2573927 | game_code: 2879323
    # Week 5 | P4 | 11:54 | Cardinals vs Titans | 113(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Titans - TWL',
        'play_id':     2573927,
        'game_code':   2879323,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RW',       'LW',       'LOR',      'LSR',      'ROR'      ],
        'number_list': [1,          75,         77,         53,         70,         68,         2,          85,         17,         0,          5          ],
        'name_list':   ['Ward',     'Moore Jr.','Skoronski', 'Cushenberry III','Zeitler','Udoh',    'Spears',   'Okonkwo',  'Lockett',  'Ridley',   'Ayomanor' ],
    },

    # --------------------------------------------------------------------------
    # Play 35: Patriots TWR
    # play_id: 2609910 | game_code: 2879303
    # Week 12 | P2 | 3:36 | Bengals vs Patriots | 221(1)
    # --------------------------------------------------------------------------
    {
        'title':       'Patriots - TWR',
        'play_id':     2609910,
        'game_code':   2879303,
        'qb_pos':      'S',
        'role_list':   ['QB',       'LT',       'LG',       'C',        'RG',       'RT',       'LOR',      'LTE',      'LW',       'RSR',      'ROR'      ],
        'number_list': [10,         66,         77,         67,         71,         76,         32,         81,         85,         8,          37         ],
        'name_list':   ['Maye',     'Campbell', 'Brown',    'Bradbury', 'Onwenu',   'Moses',    'Henderson','Hooper',   'Henry',    'Diggs',    'Westover' ],
    },

    # --------------------------------------------------------------------------
    # Play 36: Cowboys 3TBL (S2)
    # play_id: 2572283 | game_code: 2879318
    # Week 5 | P4 | 13:06 | Jets vs Cowboys | 131(0)
    # --------------------------------------------------------------------------
    {
        'title':       'Cowboys - 3TBL (S2)',
        'play_id':     2572283,
        'game_code':   2879318,
        'qb_pos':      'N',
        'role_list':   ['RW',       'QB',       'LT',       'LG',       'C',        'RG',       'RT',       'RBM',      'LTE',      'RTE',      'LOR'      ],
        'number_list': [89,         4,          71,         75,         67,         66,         78,         33,         87,         86,         3          ],
        'name_list':   ['Spann-Ford','Prescott', 'Thomas',   'Adeniji',  'Hoffman',  'Bass',     'Steele',   'Williams', 'Ferguson', 'Schoonmaker','Pickens'],
    },

]


KNOWN_ROLE_CODES = {
    'C', 'LG', 'LT', 'RG', 'RT',
    'LTE', 'LIT', 'LW', 'LIW', 'PAL', 'PBL',
    'RTE', 'RIT', 'RW', 'RIW', 'PAR', 'PBR',
    'LOR', 'LSR', 'LIR', 'LIIR', 'LIIIR',
    'ROR', 'RSR', 'RIR', 'RIIR', 'RIIIR',
    'QB', 'RBL', 'RBR', 'RBM', 'SBL', 'SBR', 'VSF',
    'FBL', 'FBR', 'FBM',
}


def _is_number_like(value) -> bool:
    if pd.isna(value):
        return False
    try:
        int(float(value))
        return True
    except (TypeError, ValueError):
        return False


def _ensure_tester_rules(df_coords: pd.DataFrame, play: dict) -> pd.DataFrame:
    df = df_coords.copy().reset_index(drop=True)

    if 'is_uncertain' not in df.columns:
        df['is_uncertain'] = False

    for idx, row in df.iterrows():
        role = str(row.get('role', '')).strip().upper()
        number_ok = _is_number_like(row.get('player_number'))
        if role not in KNOWN_ROLE_CODES or not number_ok:
            df.at[idx, 'is_uncertain'] = True
            df.at[idx, 'x_ft'] = 0.0
            df.at[idx, 'y_ft'] = 0.0
            if not number_ok:
                df.at[idx, 'player_number'] = '?'

    if len(df) > 11:
        print(f"WARNING: mapped {len(df)} players; trimming to 11")
        df = df.iloc[:11].reset_index(drop=True)
    elif len(df) < 11:
        missing = 11 - len(df)
        print(f"WARNING: mapped {len(df)} players; padding {missing} uncertain placeholder(s)")
        filler = pd.DataFrame(
            {
                'player_number': ['?'] * missing,
                'player_name':   ['Placeholder'] * missing,
                'role':          ['UNK'] * missing,
                'x_ft':          [0.0] * missing,
                'y_ft':          [0.0] * missing,
                'is_uncertain':  [True] * missing,
            }
        )
        df = pd.concat([df, filler], ignore_index=True)

    return df


# ============================================================================
# MAIN - render all 6 plays
# ============================================================================

def main():
    output_dir = Path('outputs/figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {len(PLAYS)} plays total")

    for play in PLAYS:
        print(f"\n{'='*60}")
        print(f"Play:      {play['title']}")
        print(f"play_id:   {play['play_id']} | game_code: {play['game_code']}")
        print(f"qb_pos:    {play['qb_pos']}")

        df_coords = map_offense_to_coordinates(
            role_list=play['role_list'],
            number_list=play['number_list'],
            name_list=play['name_list'],
            qb_pos=play['qb_pos'],
        )

        df_coords = _ensure_tester_rules(df_coords, play)

        print(df_coords.sort_values(['x_ft', 'y_ft']).to_string(index=False))
        print(f"Total players placed: {len(df_coords)}")

        fig, _ = plot_offense(df_coords, title=play['title'])

        safe_title = play['title'].replace(' ', '_').replace('/', '_')
        out_path = output_dir / f"S2_{safe_title}.png"
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {out_path.resolve()}")
        plt.close(fig)

    print(f"\n{'='*60}")
    print(f"All {len(PLAYS)} plays rendered successfully.")


if __name__ == '__main__':
    main()
