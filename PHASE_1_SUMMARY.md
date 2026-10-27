# Phase 1 Summary: Offensive Mapping Complete ✓

## What Was Built

A Python-based system to map NFL X-Info football data into 2D pre-snap player coordinates.

### Files Created

```
xinfo_field_viz/
├── src/
│   ├── mapper.py              # Main offensive mapping & visualization logic
│   └── roles.py               # Role categorization utilities
├── data/
│   ├── raw/                   # Input CSV location
│   └── processed/             # Output coordinates CSV
│       └── sample_offense_coordinates.csv
├── outputs/
│   └── figures/               # Output PNG visualizations
│       └── sample_offense.png
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
└── PHASE_1_SUMMARY.md        # This file
```

## Coordinate System

- **Field dimensions**: 160 feet wide (sideline to sideline)
- **Line of scrimmage**: x = 0
- **Offense positioning**: x ≤ 0 (behind the line)
- **Sidelines**: y = 0 (left) to y = 160 (right)
- **Center of field**: y = 80

## Positioning Logic Implemented

### Offensive Line (OL)
- Fixed at x = 0 (line of scrimmage)
- Center (C): y = 80
- Guards: LG at y = 75, RG at y = 85
- Tackles: LT at y = 70, RT at y = 90

### Tight Ends (TE)
- Positioned attached to the tackles
- Left TEs: Start at (-5, 65), then (-10, 60), (-15, 55), etc.
- Right TEs: Start at (-5, 95), then (-10, 100), (-15, 105), etc.

### Wide Receivers (WR)
- Positioned 3 yards back (x = -3)
- Spread across available field width
- Left side: From y = 0 to outermost-left TE
- Right side: From outermost-right TE to y = 160

### Quarterback (QB)
- Position varies by formation:
  - Normal/Under Center: x = -2, y = 80
  - Pistol: x = -12, y = 80
  - Shotgun: x = -15, y = 80

### Running Backs & Fullbacks (RB/FB)
- Positioned 5 yards back (x = -5)
- Offset by direction:
  - RBL/FBL: Left side offset (y = 72)
  - RBR/FBR: Right side offset (y = 88)
  - RBM/FBM: Center/middle (y = 80)

## Sample Output Analysis

**First play from dataset:**
- Game: Philadelphia Eagles vs Dallas Cowboys
- Offensive team: Dallas Cowboys
- Formation: 3L (3-receiver left)
- 11 offensive players successfully mapped

**Generated visualization** shows:
- Compact offensive line at line of scrimmage
- Tight end (Luke Schoonmaker) attached to left tackle
- Wide receivers spread across the field
- Running back (Hunter Luepke) in backfield on left side
- QB (Dak Prescott) 2 yards deep, centered

## Code Architecture

### OffensiveMapper Class
Core mapping logic with methods:
- `add_offensive_line()` - Place OL at exact positions
- `add_tight_ends()` - Attach TEs to tackles with spacing
- `add_wide_receivers()` - Spread WRs across field width
- `add_running_backs()` - Position backfield players
- `add_quarterback()` - Place QB based on formation
- `map_play()` - Orchestrate the mapping for one play

### Utility Functions
- `plot_offensive_formation()` - Matplotlib visualization
- Role categorization via `roles.py`

## Modular Design

✓ **Easily extendable** - Defense mapping can be added in Phase 2 without modifying offense code
✓ **Reusable components** - Role definitions separated into `roles.py`
✓ **Clean data format** - Output as CSV for easy integration with other tools

## Next Steps (Phase 2+)

- [ ] Add defensive player positioning
- [ ] Handle defensive gap techniques (0T, 1T, 3T, 5T, 7T, 9T positions)
- [ ] Add QB formation detection from CSV data
- [ ] Create multiple plays visualization
- [ ] Add play animation support
- [ ] Export to interactive visualization format

## Example Usage

```python
from src.mapper import OffensiveMapper
import pandas as pd

df = pd.read_csv('data/raw/final_x_info_catalog_with_event.csv')
mapper = OffensiveMapper()

# Map any play
coords = mapper.map_play(df.iloc[5])
print(coords)

# Plot and save
fig, ax = plot_offensive_formation(coords, title="My Formation")
fig.savefig('outputs/figures/my_play.png')
```

## Dependencies

```
pandas>=1.3.0
matplotlib>=3.4.0
numpy>=1.20.0
```

Install with: `pip install -r requirements.txt`

## Notes

- The coordinate system is designed for easy football visualization (negative x = deeper in backfield)
- Player positions are "rough pre-snap" based on role - actual positioning from player tracking data can refine these later
- Handles varying numbers of TEs and WRs automatically
- Gracefully handles missing data in the CSV
