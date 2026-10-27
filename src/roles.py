"""
Role definitions and utilities for offensive player positioning.

This module categorizes NFL player roles and provides utilities
for position classification and coordinate mapping.
"""

# Offensive Line positions (exact line of scrimmage, x=0)
OFFENSIVE_LINE_ROLES = {
    'C': {'x': 0, 'y': 80, 'label': 'Center'},
    'LG': {'x': 0, 'y': 75, 'label': 'Left Guard'},
    'RG': {'x': 0, 'y': 85, 'label': 'Right Guard'},
    'LT': {'x': 0, 'y': 70, 'label': 'Left Tackle'},
    'RT': {'x': 0, 'y': 90, 'label': 'Right Tackle'},
}

# Tight End categories (will be positioned based on how many TEs)
TIGHT_END_ROLES = {
    'TE': 'TE',
    'LTE': 'TE_Left',
    'RTE': 'TE_Right',
    'LW': 'TE_Left_Wing',  # Left Wing (essentially a TE on left)
    'RW': 'TE_Right_Wing',  # Right Wing (essentially a TE on right)
}

# Wide Receiver categories (will spread across field)
WIDE_RECEIVER_ROLES = {
    'LOR': 'WR_Left_Outside',
    'LIR': 'WR_Left_Inside',
    'LSR': 'WR_Left_Slot',
    'ROR': 'WR_Right_Outside',
    'RIR': 'WR_Right_Inside',
    'RSR': 'WR_Right_Slot',
}

# Running Back categories
RUNNING_BACK_ROLES = {
    'RB': 'RB',
    'RBL': 'RB_Left',
    'RBR': 'RB_Right',
    'RBM': 'RB_Middle',
    'RBC': 'RB_Center',
}

# Fullback
FULLBACK_ROLES = {
    'FB': 'FB',
    'FBL': 'FB_Left',
    'FBR': 'FB_Right',
    'FBC': 'FB_Center',
}

# Quarterback
QB_ROLES = {'QB', 'QBL', 'QBR'}

# Special/Other
OTHER_ROLES = {
    'PO': 'Play_Option',  # Unusual role coding
    'LS': 'Long_Snapper',  # Long snapper (rare in play data, more special teams)
}


def get_role_category(role_code: str) -> str:
    """
    Classify a role code into a category.
    
    Args:
        role_code: String role code from X-Info data
    
    Returns:
        Category string: 'OL', 'TE', 'WR', 'RB', 'FB', 'QB', 'OTHER'
    """
    if role_code in OFFENSIVE_LINE_ROLES:
        return 'OL'
    elif role_code in TIGHT_END_ROLES:
        return 'TE'
    elif role_code in WIDE_RECEIVER_ROLES:
        return 'WR'
    elif role_code in RUNNING_BACK_ROLES:
        return 'RB'
    elif role_code in FULLBACK_ROLES:
        return 'FB'
    elif role_code in QB_ROLES:
        return 'QB'
    else:
        return 'OTHER'


def is_offensive_role(role_code: str) -> bool:
    """Check if a role code is an offensive position."""
    return get_role_category(role_code) != 'OTHER'


def is_left_side(role_code: str) -> bool:
    """Check if a role is on the left side of the field."""
    return (
        role_code in {'LG', 'LT', 'LTE', 'LW', 'LOR', 'LIR', 'LSR', 'RBL', 'FBL'}
        or role_code in WIDE_RECEIVER_ROLES and 'Left' in WIDE_RECEIVER_ROLES[role_code]
    )


def is_right_side(role_code: str) -> bool:
    """Check if a role is on the right side of the field."""
    return (
        role_code in {'RG', 'RT', 'RTE', 'RW', 'ROR', 'RIR', 'RSR', 'RBR', 'FBR'}
        or role_code in WIDE_RECEIVER_ROLES and 'Right' in WIDE_RECEIVER_ROLES[role_code]
    )
