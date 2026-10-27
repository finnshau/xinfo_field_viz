from pathlib import Path

import matplotlib.pyplot as plt
import offense_plot

from offense_plot import map_offense_to_coordinates, plot_offense


PLAYS = [
	{
		'play_id': 2633325,
		'filename': 'Eagles_Commanders_manual',
		'title': 'Eagles vs Commanders | 5R',
		'qb_pos': 'S',
		'role_list': ['LT', 'LG', 'C', 'RG', 'RT', 'LOR', 'LSR', 'RIR', 'RSR', 'ROR', 'QB'],
		'number_list': [68, 69, 51, 56, 74, 88, 6, 11, 4, 26, 1],
		'name_list': ['Mailata', 'Dickerson', 'Jurgens', 'Steen', 'Johnson',
					  'Goedert', 'Smith', 'Brown', 'Dotson', 'Barkley', 'Hurts'],
	},
	{
		'play_id': 2572448,
		'filename': 'Eagles_Broncos_manual',
		'title': 'Eagles vs Broncos | T',
		'qb_pos': 'S',
		'role_list': ['LT', 'LG', 'C', 'RG', 'RT', 'RTE', 'RIW', 'LOR', 'ROR', 'QB', 'RBM'],
		'number_list': [68, 69, 51, 56, 65, 86, 81, 11, 6, 1, 26],
		'name_list': ['Mailata', 'Dickerson', 'Jurgens', 'Steen', 'Johnson',
					  'Granson', 'Calcaterra', 'Brown', 'Smith', 'Hurts', 'Barkley'],
	},
	{
		'play_id': 2593913,
		'filename': 'Patriots_Falcons_manual',
		'title': 'Patriots vs Falcons | 3TWL',
		'qb_pos': 'S',
		'role_list': ['LT', 'LG', 'C', 'RG', 'RT', 'LW', 'PBR', 'LSR', 'LOR', 'QB', 'CU'],
		'number_list': [66, 55, 67, 71, 76, 32, 37, 8, 9, 10, 81],
		'name_list': ['Campbell', 'Wilson', 'Bradbury', 'Onwenu', 'Moses',
					  'Henderson', 'Westover', 'Diggs', 'Boutte', 'Maye', 'Hooper'],
	},
	{
		'play_id': 2628685,
		'filename': 'Chargers_Chiefs_manual',
		'title': 'Chargers vs Chiefs | 3L',
		'qb_pos': 'S',
		'role_list': ['P', 'LG', 'C', 'RG', 'RT', 'RW', 'LIR', 'LSR', 'LOR', 'ROR', 'QB'],
		'number_list': [69, 77, 75, 73, 66, 44, 28, 13, 9, 15, 10],
		'name_list': ['Salyer', 'Johnson', 'Bozeman', 'Becton', 'Hart',
					  'Matlock', 'Vidal', 'Allen', 'Harris', 'McConkey', 'Herbert'],
	},
	{
		'play_id': 2621056,
		'filename': 'Patriots_Giants_manual',
		'title': 'Patriots vs Giants | N3L',
		'qb_pos': 'N',
		'role_list': ['LT', 'LG', 'C', 'RG', 'RT', 'LSR', 'LOR', 'ROR', 'QB', 'RBL', 'RBR'],
		'number_list': [76, 77, 67, 71, 76, 85, 13, 8, 10, 32, 38],
		'name_list': ['Lowe', 'Brown', 'Bradbury', 'Onwenu', 'Moses',
					  'Henry', 'Hollins', 'Williams', 'Maye', 'Henderson', 'Stevenson'],
	},
]


def normalize_roles(role_list):
	return ['LT' if role == 'P' else role for role in role_list]


def align_offense_mapper_to_requested_rules():
	offense_plot.FIELD_WIDTH = 160
	offense_plot.CENTER_Y = 80
	offense_plot.LOS_X = 0
	offense_plot.OL_POSITIONS = {'C': 80, 'LG': 85, 'LT': 90, 'RG': 75, 'RT': 70}
	offense_plot.TE_START_LEFT_Y = 95
	offense_plot.TE_START_RIGHT_Y = 65
	offense_plot.TE_SPACING = 5


def wr_rank(role):
	role_u = str(role).upper()
	if role_u.endswith('OR'):
		return 0
	if role_u.endswith('SR'):
		return 1
	if role_u.endswith('IIR'):
		return 3
	if role_u.endswith('IR'):
		return 2
	return 99


def is_wr_role(role):
	role_u = str(role).upper()
	return role_u.endswith('OR') or role_u.endswith('SR') or role_u.endswith('IR')


def is_attached_role(role):
	role_u = str(role).upper()
	if role_u in offense_plot.OL_POSITIONS:
		return True
	if role_u in offense_plot.TE_ROLES:
		return True
	if role_u in {'LW', 'RW', 'LIW', 'RIW', 'PAL', 'PAR', 'PBL', 'PBR'}:
		return True
	return False


def infer_qb_relative_side(role):
	role_u = str(role).upper()
	if role_u in {'QB', 'C', 'RBM', 'FBM', 'CU'}:
		return 'M'
	if role_u.startswith('L'):
		return 'L'
	if role_u.startswith('R'):
		return 'R'
	if role_u in {'LW', 'LIW', 'PAL', 'PBL', 'FBL', 'SBL'}:
		return 'L'
	if role_u in {'RW', 'RIW', 'PAR', 'PBR', 'FBR', 'SBR'}:
		return 'R'
	if role_u.endswith('L'):
		return 'L'
	if role_u.endswith('R'):
		return 'R'
	return 'M'


def enforce_lr_relative_to_qb(df_coords):
	adjusted = df_coords.copy()
	qb_rows = adjusted[adjusted['role'] == 'QB']
	qb_y = float(qb_rows.iloc[0]['y_ft']) if not qb_rows.empty else float(offense_plot.CENTER_Y)

	for idx, row in adjusted.iterrows():
		role = str(row['role']).upper()
		y = float(row['y_ft'])
		side = infer_qb_relative_side(role)

		if side == 'L' and y <= qb_y:
			new_y = min(offense_plot.FIELD_WIDTH, (2 * qb_y) - y)
			adjusted.at[idx, 'y_ft'] = max(new_y, qb_y + 0.01)
		elif side == 'R' and y >= qb_y:
			new_y = max(0.0, (2 * qb_y) - y)
			adjusted.at[idx, 'y_ft'] = min(new_y, qb_y - 0.01)

	return adjusted


def enforce_wr_outside_in_order(df_coords):
	adjusted = df_coords.copy()
	qb_rows = adjusted[adjusted['role'] == 'QB']
	qb_y = float(qb_rows.iloc[0]['y_ft']) if not qb_rows.empty else float(offense_plot.CENTER_Y)

	left_wr_idx = []
	right_wr_idx = []
	left_attached_ys = []
	right_attached_ys = []

	for idx, row in adjusted.iterrows():
		role_u = str(row['role']).upper()
		y = float(row['y_ft'])

		if is_attached_role(role_u):
			side = infer_qb_relative_side(role_u)
			if side == 'L' and y > qb_y:
				left_attached_ys.append(y)
			elif side == 'R' and y < qb_y:
				right_attached_ys.append(y)

		if is_wr_role(role_u):
			side = infer_qb_relative_side(role_u)
			if side == 'L':
				left_wr_idx.append(idx)
			elif side == 'R':
				right_wr_idx.append(idx)

	if left_wr_idx:
		left_outer_attached = max(left_attached_ys) if left_attached_ys else qb_y
		left_remaining = offense_plot.FIELD_WIDTH - left_outer_attached
		left_gap = left_remaining / (len(left_wr_idx) + 1)
		left_order = sorted(left_wr_idx, key=lambda i: wr_rank(adjusted.at[i, 'role']))
		for i, row_idx in enumerate(left_order, start=1):
			adjusted.at[row_idx, 'y_ft'] = min(
				offense_plot.FIELD_WIDTH,
				offense_plot.FIELD_WIDTH - (left_gap * i),
			)

	if right_wr_idx:
		right_outer_attached = min(right_attached_ys) if right_attached_ys else qb_y
		right_gap = right_outer_attached / (len(right_wr_idx) + 1)
		right_order = sorted(right_wr_idx, key=lambda i: wr_rank(adjusted.at[i, 'role']))
		for i, row_idx in enumerate(right_order, start=1):
			adjusted.at[row_idx, 'y_ft'] = max(0.0, right_gap * i)

	return adjusted


def apply_special_role_adjustments(df_coords, play):
	adjusted = df_coords.copy()

	if play['play_id'] == 2572448:
		rbm_mask = adjusted['role'] == 'RBM'
		adjusted.loc[rbm_mask, 'x_ft'] = -15
		adjusted.loc[rbm_mask, 'y_ft'] = 80

	return adjusted


def separate_overlapping_players(df_coords):
	separated = df_coords.copy()
	duplicate_groups = separated.groupby(['x_ft', 'y_ft']).indices

	for _, indices in duplicate_groups.items():
		if len(indices) <= 1:
			continue

		sorted_indices = sorted(
			indices,
			key=lambda i: 0 if str(separated.loc[i, 'role']) == 'QB' else 1,
		)

		for offset_i, row_idx in enumerate(sorted_indices[1:], start=1):
			lateral_shift = 1.5 * offset_i
			side_sign = -1 if offset_i % 2 else 1

			separated.at[row_idx, 'x_ft'] = float(separated.at[row_idx, 'x_ft']) - (2.0 * offset_i)
			separated.at[row_idx, 'y_ft'] = float(separated.at[row_idx, 'y_ft']) + (side_sign * lateral_shift)
			separated.at[row_idx, 'y_ft'] = min(max(separated.at[row_idx, 'y_ft'], 0.0), offense_plot.FIELD_WIDTH)

			if separated.at[row_idx, 'x_ft'] < -23.0:
				separated.at[row_idx, 'x_ft'] = -23.0

	return separated


def validate_unique_coordinates(df_coords, play_id):
	unique_spots = df_coords[['x_ft', 'y_ft']].drop_duplicates()
	if len(unique_spots) != len(df_coords):
		raise ValueError(f"Play {play_id} still has overlapping coordinates after separation")


def validate_lr_semantics(df_coords, play_id):
	qb_rows = df_coords[df_coords['role'] == 'QB']
	if qb_rows.empty:
		return

	qb_y = float(qb_rows.iloc[0]['y_ft'])
	for _, row in df_coords.iterrows():
		role = str(row['role']).upper()
		y = float(row['y_ft'])
		side = infer_qb_relative_side(role)

		if side == 'M':
			continue
		if side == 'L' and y <= qb_y:
			raise ValueError(f"Play {play_id}: role {role} is not above/left of QB")
		if side == 'R' and y >= qb_y:
			raise ValueError(f"Play {play_id}: role {role} is not below/right of QB")


def main():
	output_dir = Path('outputs/figures')
	output_dir.mkdir(parents=True, exist_ok=True)
	align_offense_mapper_to_requested_rules()

	summary = []
	for play in PLAYS:
		mapped_roles = normalize_roles(play['role_list'])
		df_coords = map_offense_to_coordinates(
			mapped_roles,
			play['number_list'],
			play['name_list'],
			qb_pos=play['qb_pos'],
		)
		df_coords = enforce_lr_relative_to_qb(df_coords)
		df_coords = apply_special_role_adjustments(df_coords, play)
		df_coords = enforce_wr_outside_in_order(df_coords)
		df_coords = separate_overlapping_players(df_coords)
		validate_unique_coordinates(df_coords, play['play_id'])
		validate_lr_semantics(df_coords, play['play_id'])

		print(f"\n{'=' * 72}")
		print(f"PLAY {play['play_id']}: {play['title']}")
		print(f"{'=' * 72}")
		print(df_coords.to_string(index=False))

		player_count = len(df_coords)
		print(f"\nConfirmed player count: {player_count}")
		if player_count != 11:
			raise ValueError(f"Play {play['play_id']} produced {player_count} players instead of 11")

		fig, _ = plot_offense(df_coords, title=play['title'])
		output_path = output_dir / f"{play['filename']}.png"
		fig.savefig(output_path, dpi=150)
		plt.close(fig)
		print(f"Saved figure to: {output_path.resolve()}")

		summary.append((play['play_id'], player_count, output_path.name))

	print(f"\n{'=' * 72}")
	print('SUMMARY')
	print(f"{'=' * 72}")
	for play_id, player_count, filename in summary:
		print(f"Play {play_id}: {player_count} players plotted -> {filename}")


if __name__ == '__main__':
	main()
