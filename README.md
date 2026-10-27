# X-Info Football Field Visualization

Map X-Info data to pre-snap player coordinates on a football field.

## Phase 1: Offensive Mapping

Maps 11 offensive players to 2D coordinates before the snap.

### Coordinate System

- **Field width**: 160 feet (sideline to sideline)
- **Line of scrimmage**: x = 0
- **Center of field**: y = 80 (middle of 0-160 range)
- **Offense positioning**: x ≤ 0 (behind or at line of scrimmage)

### Offensive Player Positioning Rules

**Offensive Line:**
- Center (C): (0, 80)
- Left Guard (LG): (0, 75)
- Left Tackle (LT): (0, 70)
- Right Guard (RG): (0, 85)
- Right Tackle (RT): (0, 90)

**Tight Ends** (attached to tackles, spaced 5 feet apart):
- Left TE positions: (−5, 65), (−10, 60), (−15, 55), etc.
- Right TE positions: (−5, 95), (−10, 100), (−15, 105), etc.

**Wide Receivers** (spread between sideline and outermost TE):
- Left side WRs: Spaced from y=0 to outermost-left TE position
- Right side WRs: Spaced from outermost-right TE position to y=160

**Quarterback (QB):**
- Normal / Under Center: (−2, 80)
- Pistol: (−12, 80)
- Shotgun: (−15, 80)

**Running Backs (RB) & Fullbacks (FB):**
- Positioned 3-5 yards behind QB based on role designation
- RBL/RBR = 4-6 yards deep, offset left/right
- RBM/RBC = directly behind QB
- RBR = offset right
- RBL = offset left

### Data Structure

Input CSV columns:
- `off_1_number` through `off_11_number`: Player jersey numbers
- `off_1_player_first_name` through `off_11_player_first_name`: First names
- `off_1_player_last_name` through `off_11_player_last_name`: Last names
- `off_1_role` through `off_11_role`: Position/role codes
- `offensive_formation`: Formation type (e.g., "3L", "4", "Nickel")

Output format:
```
player_number,player_name,role,x_ft,y_ft
```

### Role Code Reference

Common offensive roles:
- **QB** - Quarterback
- **C** - Center
- **LG** - Left Guard
- **RG** - Right Guard
- **LT** - Left Tackle
- **RT** - Right Tackle
- **TE/LTE/RTE** - Tight end variants
- **LOR/LSR/LIR** - Left Outside Receiver / Left Slot Receiver / Left Inside Receiver
- **ROR/RSR/RIR** - Right Outside Receiver / Right Slot Receiver / Right Inside Receiver
- **RBL/RBR/RBM** - Running Back Left / Right / Middle
- **FB/FBL/FBR** - Fullback variants
- **LW/RW** - Left/Right Wing
- **PO** - Plays Option role (atypical)

### Project Structure

```
xinfo_field_viz/
├── data/
│   ├── raw/                    # Original CSV data
│   └── processed/              # Processed coordinates
├── outputs/
│   └── figures/                # Visualization PNG files
├── src/
│   ├── mapper.py              # Main mapping logic
│   └── roles.py               # Role definitions and utilities
├── README.md                  # This file
└── requirements.txt           # Python dependencies
```

## Usage

```python
python src/mapper.py
```

## Next Phases

- Phase 2: Defensive mapping (defense-side coordinates)
- Phase 3: Animation of plays over time
- Phase 4: Interactive visualization
