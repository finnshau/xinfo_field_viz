from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


FIELD_WIDTH = 160.0
CENTER_Y = 80.0
LOS_X = 0.0

CATALOG_PATH = r"C:\Users\Finn.Shaughnessy\OneDrive - Stats Perform\Documents\final_x_info_catalog_with_event.csv"
ROLES_XLSX_PATH = r"C:\Users\Finn.Shaughnessy\OneDrive - Stats Perform\Documents\xInfoViz\NFL Roles.xlsx"

OL_Y = {
    "LT": 70.0,
    "LG": 75.0,
    "C": 80.0,
    "RG": 85.0,
    "RT": 90.0,
}

QB_DEPTH = {
    "N": -2.0,
    "P": -12.0,
    "S": -15.0,
}

TE_WING_ROLES = {
    "TE", "LTE", "RTE", "LW", "RW", "LIW", "RIW", "LIT", "RIT", "PAL", "PAR", "PBL", "PBR"
}

WR_SUFFIX_RANK = {
    "OR": 0,
    "SR": 1,
    "IR": 2,
    "IIR": 3,
}


def _load_shared_role_data():
    role_side_map = {}
    role_broad_map = {}
    role_spec_map = {}
    catalog_role_set = set()

    try:
        roles_df = pd.read_excel(ROLES_XLSX_PATH)
        offense_mask = roles_df["Offense"].astype(str).str.upper().isin({"T", "TRUE", "1", "Y"})
        offense_roles = roles_df.loc[offense_mask].copy()

        for _, row in offense_roles.iterrows():
            abbrev = str(row.get("ABBREV", "")).strip().upper()
            if not abbrev:
                continue

            side = str(row.get("Side", "")).strip().upper()
            if side in {"L", "R", "M"}:
                role_side_map[abbrev] = side

            broad = str(row.get("Pos Broad", "")).strip().upper()
            if broad:
                role_broad_map[abbrev] = broad

            spec = str(row.get("Pos Spec", "")).strip().upper()
            if spec:
                role_spec_map[abbrev] = spec
    except Exception as exc:
        print(f"Warning: failed to load roles workbook '{ROLES_XLSX_PATH}': {exc}")

    try:
        use_cols = [f"off_{i}_role" for i in range(1, 12)]
        catalog_df = pd.read_csv(CATALOG_PATH, usecols=use_cols, dtype=str, low_memory=False)
        for col in use_cols:
            codes = catalog_df[col].dropna().astype(str).str.strip().str.upper()
            catalog_role_set.update(code for code in codes if code)
    except Exception as exc:
        print(f"Warning: failed to load catalog CSV '{CATALOG_PATH}': {exc}")

    return role_side_map, role_broad_map, role_spec_map, catalog_role_set


ROLE_SIDE_MAP, ROLE_BROAD_MAP, ROLE_SPEC_MAP, CATALOG_ROLE_SET = _load_shared_role_data()


def _normalize_qb_formation(qb_formation):
    text = str(qb_formation).strip().upper()
    if text in QB_DEPTH:
        return text
    if text:
        first = text[0]
        if first in QB_DEPTH:
            return first
    return "S"


def _infer_side(role_code):
    role = str(role_code).strip().upper()
    return ROLE_SIDE_MAP.get(role)


def _wr_rank(role_code):
    role = str(role_code).strip().upper()
    for suffix, rank in WR_SUFFIX_RANK.items():
        if role.endswith(suffix):
            return rank
    return 99


def map_offense_to_coordinates(role_list, number_list, name_list, qb_formation):
    if not (len(role_list) == len(number_list) == len(name_list)):
        raise ValueError("role_list, number_list, and name_list must have the same length")

    players = []
    for i, (role, number, name) in enumerate(zip(role_list, number_list, name_list)):
        role_code = str(role).strip().upper()
        if role_code not in CATALOG_ROLE_SET:
            print(f"Warning: role code '{role_code}' is not present in the shared catalog")

        players.append(
            {
                "idx": i,
                "role": role_code,
                "player_number": int(number),
                "player_name": str(name),
            }
        )

    qb_mode = _normalize_qb_formation(qb_formation)
    coords = []

    # 1) Offensive line on LOS.
    for p in players:
        role = p["role"]
        if role in OL_Y:
            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": role,
                    "x_ft": LOS_X,
                    "y_ft": OL_Y[role],
                    "idx": p["idx"],
                }
            )

    # 2) Tight ends / wings on LOS, stepping out from each side.
    left_te_count = 0
    right_te_count = 0
    for p in players:
        role = p["role"]
        if ROLE_BROAD_MAP.get(role) == "TE":
            side = _infer_side(role)
            if side == "L":
                y = 65.0 - (left_te_count * 5.0)
                left_te_count += 1
            elif side == "R":
                y = 95.0 + (right_te_count * 5.0)
                right_te_count += 1
            else:
                y = CENTER_Y
                print(f"Warning: could not infer TE/Wing side for role code '{role}', using placeholder y=80")

            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": role,
                    "x_ft": LOS_X,
                    "y_ft": y,
                    "idx": p["idx"],
                }
            )

    # Helper bounds from attached players (OL + TE/Wing).
    left_attached = [c["y_ft"] for c in coords if _infer_side(c["role"]) == "L" and c["x_ft"] == LOS_X]
    right_attached = [c["y_ft"] for c in coords if _infer_side(c["role"]) == "R" and c["x_ft"] == LOS_X]

    left_outermost = min(left_attached) if left_attached else 70.0
    right_outermost = max(right_attached) if right_attached else 90.0

    # 3) Wide receivers on LOS, spaced between sideline and outermost attached player.
    left_wrs = [
        p
        for p in players
        if ROLE_BROAD_MAP.get(p["role"]) == "WR" and _infer_side(p["role"]) == "L" and _wr_rank(p["role"]) < 99
    ]
    right_wrs = [
        p
        for p in players
        if ROLE_BROAD_MAP.get(p["role"]) == "WR" and _infer_side(p["role"]) == "R" and _wr_rank(p["role"]) < 99
    ]

    left_wrs.sort(key=lambda p: (_wr_rank(p["role"]), p["idx"]))
    right_wrs.sort(key=lambda p: (_wr_rank(p["role"]), p["idx"]))

    if left_wrs:
        left_remaining = left_outermost - 0.0
        left_gap = left_remaining / (len(left_wrs) + 1)
        for i, p in enumerate(left_wrs, start=1):
            y = 0.0 + (left_gap * i)
            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": p["role"],
                    "x_ft": LOS_X,
                    "y_ft": y,
                    "idx": p["idx"],
                }
            )

    if right_wrs:
        right_remaining = 160.0 - right_outermost
        right_gap = right_remaining / (len(right_wrs) + 1)
        for i, p in enumerate(right_wrs, start=1):
            y = 160.0 - (right_gap * i)
            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": p["role"],
                    "x_ft": LOS_X,
                    "y_ft": y,
                    "idx": p["idx"],
                }
            )

    # 4) Quarterback depth by formation.
    for p in players:
        role = p["role"]
        if ROLE_BROAD_MAP.get(role) == "QB":
            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": role,
                    "x_ft": QB_DEPTH[qb_mode],
                    "y_ft": CENTER_Y,
                    "idx": p["idx"],
                }
            )

    # 5) Running backs.
    rb_left_count = 0
    rb_right_count = 0

    for p in players:
        role = p["role"]
        if ROLE_BROAD_MAP.get(role) == "RB" and ROLE_SPEC_MAP.get(role) != "FB":
            side = _infer_side(role)

            if qb_mode == "N":
                x = -21.0
                if side == "L":
                    y = 75.0
                elif side == "R":
                    y = 85.0
                else:
                    y = CENTER_Y

            elif qb_mode == "P":
                x = -21.0
                if side == "L":
                    y = CENTER_Y - 5.0
                elif side == "R":
                    y = CENTER_Y + 5.0
                else:
                    y = CENTER_Y

            else:  # Shotgun
                x = -15.0
                if side == "L":
                    y = 76.0 - (4.0 * rb_left_count)
                    rb_left_count += 1
                elif side == "R":
                    y = 84.0 + (4.0 * rb_right_count)
                    rb_right_count += 1
                else:
                    print(
                        f"Warning: shotgun RB role '{role}' must be left or right per rule set; using placeholder"
                    )
                    continue

            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": role,
                    "x_ft": x,
                    "y_ft": y,
                    "idx": p["idx"],
                }
            )

    # 6) Fullbacks.
    for p in players:
        role = p["role"]
        if ROLE_SPEC_MAP.get(role) == "FB":
            side = _infer_side(role)
            if qb_mode == "N":
                x = -14.0
                if side == "L":
                    y = 75.0
                elif side == "R":
                    y = 85.0
                else:
                    y = CENTER_Y
            elif qb_mode == "P":
                if side == "L":
                    x, y = -15.0, CENTER_Y - 5.0
                elif side == "R":
                    x, y = -15.0, CENTER_Y + 5.0
                else:
                    x, y = -17.5, CENTER_Y
            else:
                x, y = -13.0, CENTER_Y

            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": role,
                    "x_ft": x,
                    "y_ft": y,
                    "idx": p["idx"],
                }
            )

    # 7) Place any still-unrecognized role at placeholder and warn.
    placed_indices = {c["idx"] for c in coords}
    for p in players:
        if p["idx"] not in placed_indices:
            print(f"Warning: unrecognized role code '{p['role']}', using placeholder at x=0,y=80")
            coords.append(
                {
                    "player_number": p["player_number"],
                    "player_name": p["player_name"],
                    "role": p["role"],
                    "x_ft": 0.0,
                    "y_ft": 80.0,
                    "idx": p["idx"],
                }
            )

    df = pd.DataFrame(coords)
    df = df.sort_values("idx").drop(columns=["idx"]).reset_index(drop=True)
    return df


def _ensure_eleven_players(df_coords):
    count = len(df_coords)

    if count > 11:
        print(f"Warning: mapped {count} players; trimming to first 11 for plotting")
        return df_coords.iloc[:11].reset_index(drop=True)

    if count < 11:
        print(f"Warning: mapped {count} players; padding to 11 with placeholders")
        missing = 11 - count
        padding = pd.DataFrame(
            {
                "player_number": [0] * missing,
                "player_name": ["Placeholder"] * missing,
                "role": ["UNK"] * missing,
                "x_ft": [0.0] * missing,
                "y_ft": [80.0] * missing,
            }
        )
        return pd.concat([df_coords, padding], ignore_index=True)

    return df_coords


def plot_offense(df_coords, title):
    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor("#215d2a")
    ax.set_facecolor("#2e8b57")

    # Line of scrimmage.
    ax.axvline(x=0, color="white", linewidth=2.5)

    # Circular dots.
    ax.scatter(
        df_coords["x_ft"],
        df_coords["y_ft"],
        s=520,
        c="#0f2747",
        edgecolors="white",
        linewidths=1.5,
        zorder=3,
    )

    # Jersey numbers inside dots.
    for _, row in df_coords.iterrows():
        ax.text(
            row["x_ft"],
            row["y_ft"],
            str(int(row["player_number"])),
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
            zorder=4,
        )

        ax.text(
            row["x_ft"] + 1.2,
            row["y_ft"],
            str(row["role"]),
            ha="left",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold",
            zorder=4,
        )

    ax.set_title(title, fontsize=14, fontweight="bold", color="white", pad=12)
    ax.set_xlim(-30, 5)
    ax.set_ylim(0, 160)
    ax.set_aspect("equal", adjustable="box")

    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")

    ax.set_xlabel("X (feet)", color="white")
    ax.set_ylabel("Y (feet)", color="white")

    return fig, ax


def _run_play(play_id, title, qb_formation, role_list, number_list, name_list):
    print("-" * 72)
    print(f"PLAY {play_id}: {title}")

    df_coords = map_offense_to_coordinates(role_list, number_list, name_list, qb_formation)
    df_coords = _ensure_eleven_players(df_coords)
    print(df_coords)
    print(f"Confirmed exactly 11 players: {len(df_coords) == 11} (count={len(df_coords)})")

    fig, _ = plot_offense(df_coords, title)
    out_dir = Path("outputs") / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"play_{play_id}.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved image: {out_path}")


def main():
    plays = [
        {
            "play_id": 2633325,
            "title": "Eagles vs Commanders | 5R",
            "qb_formation": "S",
            "role_list": ["LT", "LG", "C", "RG", "RT", "LOR", "LSR", "RIR", "RSR", "ROR", "QB"],
            "number_list": [68, 69, 51, 56, 74, 88, 6, 11, 4, 26, 1],
            "name_list": [
                "Mailata",
                "Dickerson",
                "Jurgens",
                "Steen",
                "Johnson",
                "Goedert",
                "Smith",
                "Brown",
                "Dotson",
                "Barkley",
                "Hurts",
            ],
        },
        {
            "play_id": 2572448,
            "title": "Eagles vs Broncos | T",
            "qb_formation": "S",
            "role_list": ["LT", "LG", "C", "RG", "RT", "RTE", "RIW", "LOR", "ROR", "QB", "RBM"],
            "number_list": [68, 69, 51, 56, 65, 86, 81, 11, 6, 1, 26],
            "name_list": [
                "Mailata",
                "Dickerson",
                "Jurgens",
                "Steen",
                "Johnson",
                "Granson",
                "Calcaterra",
                "Brown",
                "Smith",
                "Hurts",
                "Barkley",
            ],
        },
        {
            "play_id": 2593913,
            "title": "Patriots vs Falcons | 3TWL",
            "qb_formation": "S",
            "role_list": ["LT", "LG", "C", "RG", "RT", "LW", "PBR", "LSR", "LOR", "QB", "CU"],
            "number_list": [66, 55, 67, 71, 76, 32, 37, 8, 9, 10, 81],
            "name_list": [
                "Campbell",
                "Wilson",
                "Bradbury",
                "Onwenu",
                "Moses",
                "Henderson",
                "Westover",
                "Diggs",
                "Boutte",
                "Maye",
                "Hooper",
            ],
        },
        {
            "play_id": 2628685,
            "title": "Chargers vs Chiefs | 3L",
            "qb_formation": "S",
            "role_list": ["P", "LG", "C", "RG", "RT", "RW", "LIR", "LSR", "LOR", "ROR", "QB"],
            "number_list": [69, 77, 75, 73, 66, 44, 28, 13, 9, 15, 10],
            "name_list": [
                "Salyer",
                "Johnson",
                "Bozeman",
                "Becton",
                "Hart",
                "Matlock",
                "Vidal",
                "Allen",
                "Harris",
                "McConkey",
                "Herbert",
            ],
        },
        {
            "play_id": 2621056,
            "title": "Patriots vs Giants | N3L",
            "qb_formation": "N",
            "role_list": ["LT", "LG", "C", "RG", "RT", "LSR", "LOR", "ROR", "QB", "RBL", "RBR"],
            "number_list": [76, 77, 67, 71, 76, 85, 13, 8, 10, 32, 38],
            "name_list": [
                "Lowe",
                "Brown",
                "Bradbury",
                "Onwenu",
                "Moses",
                "Henry",
                "Hollins",
                "Williams",
                "Maye",
                "Henderson",
                "Stevenson",
            ],
        },
    ]

    for play in plays:
        _run_play(
            play["play_id"],
            play["title"],
            play["qb_formation"],
            play["role_list"],
            play["number_list"],
            play["name_list"],
        )


if __name__ == "__main__":
    main()
