"""
2025 WNBA Shot Profile Analysis
Kelsey Mitchell vs. Jackie Young

Purpose:
Compare shot selection, scoring efficiency,
and offensive tendencies during the
2025 WNBA regular season.

Data Source:
SportsDataverse / ESPN WNBA datasets

Author:
Basketball Analytics Portfolio Project
"""

# ==========================================
# 1. IMPORT LIBRARIES
# ==========================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc


# ==========================================
# 2. LOAD DATASETS
# ==========================================

shots = pd.read_csv("data/shots_2025.csv")
schedule = pd.read_csv("data/wnba_schedule_2025.csv")

print("Datasets loaded successfully!")

print("\nShot Dataset:")
print(shots.shape)

print("\nSchedule Dataset:")
print(schedule.shape)


# ==========================================
# 3. IDENTIFY PLAYERS
# ==========================================

KELSEY_ID = 3142191
JACKIE_ID = 4065870

PLAYER_IDS = [KELSEY_ID, JACKIE_ID]

print("\nPlayers selected:")
print("Kelsey Mitchell")
print("Jackie Young")

# ==========================================
# 4. FILTER REGULAR-SEASON GAMES
# ==========================================

regular_season_schedule = schedule[
    schedule["season_type"] == 2
].copy()

cup_id = 401736430

regular_season_schedule = schedule[
    (schedule["season_type"] == 2) &
    (schedule["id"] != cup_id)
].copy()

# Identify our two players' shot events
player_shots = shots[
    shots["athlete_id_1"].isin(PLAYER_IDS)
].copy()

# Match shot events to regular-season games
regular_season_shots = player_shots.merge(
    regular_season_schedule[["id"]],
    left_on="game_id",
    right_on="id",
    how="inner"
)

regular_season_shots = regular_season_shots[
    ~regular_season_shots["team_name"].isin(["Team Clark", "Team Collier"])
].copy()

print("\nRegular-Season Games by Player:")

game_counts = (
    regular_season_shots
    .groupby("athlete_name_1")["game_id"]
    .nunique()
)

print(game_counts)

# ==========================================
# 5. FILTER FIELD-GOAL ATTEMPTS
# ==========================================

field_goals = regular_season_shots[
    ~regular_season_shots["type_text"].str.contains(
        "Free Throw",
        case=False,
        na=False
    )
].copy()

print("\nField-Goal Attempts by Player:")

print(
    field_goals["athlete_name_1"].value_counts()
)

print("\nTotal Field-Goal Attempts:")
print(len(field_goals))

# ==========================================
# 6. NORMALIZE SHOT COORDINATES
# ==========================================

# Reflect shots onto one half of the court
field_goals["court_x"] = (
    field_goals["coordinate_x"].abs()
)

field_goals["court_y"] = (
    field_goals["coordinate_y"].where(
        field_goals["coordinate_x"] >= 0,
        -field_goals["coordinate_y"]
    )
)

# Verify that coordinates are available
print("\nMissing Normalized Coordinates:")

print(
    field_goals[["court_x", "court_y"]]
    .isna()
    .sum()
)

# ==========================================
# 7. CALCULATE SHOT DISTANCE
# ==========================================

RIM_X = 41.25
RIM_Y = 0

field_goals["shot_distance"] = (
    (
        (field_goals["court_x"] - RIM_X) ** 2
        + (field_goals["court_y"] - RIM_Y) ** 2
    ) ** 0.5
)

print("\nShot Distance Summary:")

print(
    field_goals["shot_distance"]
    .describe()
    .round(2)
)

# ==========================================
# 8. ESTABLISH SHOT VALUES
# ==========================================

def classify_shot_value(row):

    # Corner three-point attempts
    if (
        row["court_x"] >= 38.75
        and abs(row["court_y"]) >= 22
    ):
        return 3

    # Above-the-break three-point attempts
    elif row["shot_distance"] >= 22.25:
        return 3

    # Remaining two-point attempts
    else:
        return 2


field_goals["predicted_shot_value"] = field_goals.apply(
    classify_shot_value,
    axis=1
)

print("\nShot Values by Player:")

print(
    field_goals.groupby(
        ["athlete_name_1", "predicted_shot_value"]
    ).size()
)

# ==========================================
# 9. CLASSIFY SHOT ZONES
# ==========================================

def classify_shot_zone(row):

    # Three-point attempts
    if row["predicted_shot_value"] == 3:

        # Corner three-point attempts
        if (
            row["court_x"] >= 38.75
            and abs(row["court_y"]) >= 22
        ):
            return "Corner 3"

        # Remaining three-point attempts
        return "Above the Break 3"

    # Two-point attempts near the basket
    elif row["shot_distance"] <= 4:
        return "Rim"

    # Interior two-point attempts
    elif (
        row["court_x"] >= 25
        and abs(row["court_y"]) <= 8
    ):
        return "Paint"

    # Remaining two-point attempts
    else:
        return "Midrange"


field_goals["shot_zone"] = field_goals.apply(
    classify_shot_zone,
    axis=1
)

# Display shot-zone distribution
print("\nShot Zone Distribution:")

print(
    field_goals.groupby(
        ["athlete_name_1", "shot_zone"]
    ).size()
)

# Confirm every attempt was classified
print("\nMissing Shot Zones:")
print(field_goals["shot_zone"].isna().sum())

print("\nTotal Classified Attempts:")
print(field_goals["shot_zone"].count())

# ==========================================
# 10. CALCULATE SHOT DISTRIBUTION
# ==========================================

shot_distribution = (
    field_goals.groupby(
        ["athlete_name_1", "shot_zone"]
    )
    .size()
    .reset_index(name="attempts")
)

# Calculate total attempts for each player
shot_distribution["total_attempts"] = (
    shot_distribution.groupby("athlete_name_1")[
        "attempts"
    ].transform("sum")
)

# Calculate percentage of attempts from each zone
shot_distribution["shot_frequency_pct"] = (
    shot_distribution["attempts"]
    / shot_distribution["total_attempts"]
    * 100
)

print("\nShot Distribution by Player:")

print(
    shot_distribution[
        [
            "athlete_name_1",
            "shot_zone",
            "attempts",
            "shot_frequency_pct"
        ]
    ].round(1).to_string(index=False)
)

# ==========================================
# 11. VISUALIZE SHOT DISTRIBUTION
# ==========================================

# Establish the order of shot zones
zone_order = [
    "Rim",
    "Paint",
    "Midrange",
    "Corner 3",
    "Above the Break 3"
]

# Reshape the data for visualization
chart_data = shot_distribution.pivot(
    index="shot_zone",
    columns="athlete_name_1",
    values="shot_frequency_pct"
)

# Arrange the zones in our preferred order
chart_data = chart_data.reindex(zone_order)

# Set up bar positions
x = np.arange(len(zone_order))
bar_width = 0.35

# Create the figure
fig, ax = plt.subplots(figsize=(12, 6))

# Kelsey Mitchell bars
bars_kelsey = ax.bar(
    x - bar_width / 2,
    chart_data["Kelsey Mitchell"],
    bar_width,
    label="Kelsey Mitchell",
    color="#FDBB30"
)

# Jackie Young bars
bars_jackie = ax.bar(
    x + bar_width / 2,
    chart_data["Jackie Young"],
    bar_width,
    label="Jackie Young",
    color="#C4CED4"
)

# Chart labels
ax.set_title(
    "2025 WNBA Regular Season | Shot Distribution",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Shot Zone", fontsize=12)
ax.set_ylabel("Percentage of Field-Goal Attempts (%)", fontsize=12)

ax.set_xticks(x)
ax.set_xticklabels(zone_order)

# Display values above bars
ax.bar_label(bars_kelsey, fmt="%.1f%%", padding=3)
ax.bar_label(bars_jackie, fmt="%.1f%%", padding=3)

# Chart formatting
ax.set_ylim(0, 45)
ax.legend()
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

fig.text(
    0.5, 0.01,
    "Kelsey Mitchell: 691 FGA | Jackie Young: 549 FGA | "
    "Source: SportsDataverse / ESPN",
    ha="center",
    fontsize=9,
    color="gray"
)

plt.tight_layout()

# Save a high-resolution image for GitHub
plt.savefig(
    "visualizations/shot_distribution_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ==========================================
# 12. CALCULATE FIELD-GOAL PERCENTAGE
# ==========================================

# Identify made field goals
field_goals["made"] = (
    field_goals["scoring_play"] == True
)

# Calculate attempts, makes, and FG%
zone_efficiency = (
    field_goals.groupby(
        ["athlete_name_1", "shot_zone"]
    )
    .agg(
        attempts=("made", "count"),
        makes=("made", "sum")
    )
    .reset_index()
)

zone_efficiency["fg_pct"] = (
    zone_efficiency["makes"]
    / zone_efficiency["attempts"]
    * 100
)

print("\nField-Goal Efficiency by Zone:")

print(
    zone_efficiency.round(1).to_string(index=False)
)

# ==========================================
# 13. VISUALIZE FIELD-GOAL EFFICIENCY
# ==========================================

# Organize zones in basketball court order
zone_order = [
    "Rim",
    "Paint",
    "Midrange",
    "Corner 3",
    "Above the Break 3"
]

# Reshape data for side-by-side comparison
efficiency_chart = zone_efficiency.pivot(
    index="shot_zone",
    columns="athlete_name_1",
    values="fg_pct"
)

# Apply consistent zone ordering
efficiency_chart = efficiency_chart.reindex(zone_order)

# Create chart
fig, ax = plt.subplots(figsize=(12, 6))

efficiency_chart.plot(
    kind="bar",
    ax=ax,
    color=["#C4CDD3", "#FFB81C"],
    width=0.7
)

# Format chart
ax.set_title(
    "2025 WNBA Regular Season | Field-Goal Efficiency by Zone",
    fontsize=15,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Shot Zone")
ax.set_ylabel("Field-Goal Percentage (%)")
ax.set_ylim(0, 80)

ax.tick_params(axis="x", rotation=0)

ax.legend(title="Player")

# Display percentage labels above bars
for container in ax.containers:
    ax.bar_label(
        container,
        fmt="%.1f%%",
        padding=3,
        fontsize=10
    )

# Add data source
fig.text(
    0.5, 0.02,
    "Source: SportsDataverse / ESPN | 2025 Regular Season",
    ha="center",
    fontsize=9,
    color="gray"
)

plt.savefig(
    "visualizations/shot_efficiency_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.subplots_adjust(bottom=0.18)
plt.show()

# ==========================================
# 14. CALCULATE POINTS PER SHOT BY ZONE
# ==========================================

points_per_shot = (
    field_goals.groupby(
        ["athlete_name_1", "shot_zone"]
    )
    .agg(
        attempts=("game_id", "count"),
        total_points=("score_value", "sum")
    )
    .reset_index()
)

# Calculate scoring value per field-goal attempt
points_per_shot["points_per_shot"] = (
    points_per_shot["total_points"]
    / points_per_shot["attempts"]
)

# Round for presentation
points_per_shot["points_per_shot"] = (
    points_per_shot["points_per_shot"].round(2)
)

print("\nPoints Per Shot by Zone:")
print(points_per_shot.to_string(index=False))

# ==========================================
# 15. VISUALIZE POINTS PER SHOT BY ZONE
# ==========================================

# Define shot zone order
zone_order = [
    "Rim",
    "Paint",
    "Midrange",
    "Corner 3",
    "Above the Break 3"
]

# Prepare data for visualization
pps_pivot = points_per_shot.pivot(
    index="shot_zone",
    columns="athlete_name_1",
    values="points_per_shot"
).reindex(zone_order)

# Create the figure
fig, ax = plt.subplots(figsize=(12, 7))

x = np.arange(len(zone_order))
width = 0.35

# Create side-by-side bars
kelsey_bars = ax.bar(
    x - width / 2,
    pps_pivot["Kelsey Mitchell"],
    width,
    label="Kelsey Mitchell",
    color="#FFB81C"
)

jackie_bars = ax.bar(
    x + width / 2,
    pps_pivot["Jackie Young"],
    width,
    label="Jackie Young",
    color="#BFC7CE"
)

# Add labels and title
ax.set_title(
    "2025 WNBA Regular Season | Points Per Shot by Zone",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Shot Zone")
ax.set_ylabel("Points Per Field-Goal Attempt")

ax.set_xticks(x)
ax.set_xticklabels(zone_order)

ax.set_ylim(0, 1.8)

# Display values above bars
ax.bar_label(
    kelsey_bars,
    fmt="%.2f",
    padding=3
)

ax.bar_label(
    jackie_bars,
    fmt="%.2f",
    padding=3
)

ax.legend(title="Player")
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

# Add source attribution
fig.text(
    0.5,
    0.02,
    "Source: SportsDataverse / ESPN | 2025 Regular Season",
    ha="center",
    fontsize=9,
    color="gray"
)
plt.savefig(
    "visualizations/points_per_shot_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.subplots_adjust(bottom=0.18)
plt.show()

# ==========================================
# 16. CREATE WNBA HALF-COURT SHOT CHARTS
# ==========================================

from matplotlib.patches import Circle, Rectangle, Arc

# Convert our normalized coordinates to a
# basket-centered half-court coordinate system.
#
# Basket: (0, 0)
# Positive y: toward half court
# x: left/right across the court

field_goals["plot_x"] = field_goals["court_y"]
field_goals["plot_y"] = 41.25 - field_goals["court_x"]


def draw_wnba_court(ax):

    court_color = "#555555"

    # Court boundary
    ax.add_patch(
        Rectangle(
            (-25, -5.25),
            50,
            47,
            fill=False,
            edgecolor=court_color,
            linewidth=1.5
        )
    )

    # Paint / free throw lane
    ax.add_patch(
        Rectangle(
            (-8, -5.25),
            16,
            19,
            fill=False,
            edgecolor=court_color,
            linewidth=1.5
        )
    )

    # Basket
    ax.add_patch(
        Circle(
            (0, 0),
            radius=0.75,
            fill=False,
            edgecolor=court_color,
            linewidth=1.5
        )
    )

    # Backboard
    ax.plot(
        [-3, 3],
        [-1.25, -1.25],
        color=court_color,
        linewidth=2
    )

    # Restricted area
    ax.add_patch(
        Arc(
            (0, 0),
            8,
            8,
            theta1=0,
            theta2=180,
            color=court_color,
            linewidth=1.5
        )
    )

    # Free throw circle
    ax.add_patch(
        Arc(
            (0, 13.75),
            12,
            12,
            theta1=0,
            theta2=180,
            color=court_color,
            linewidth=1.5
        )
    )

    # Three-point arc
    three_radius = 22 + 1.75 / 12
    corner_x = 22

    arc_start = np.degrees(
        np.arccos(corner_x / three_radius)
    )

    ax.add_patch(
        Arc(
            (0, 0),
            three_radius * 2,
            three_radius * 2,
            theta1=arc_start,
            theta2=180 - arc_start,
            color=court_color,
            linewidth=1.5
        )
    )

    # Corner three-point lines
    corner_y = np.sqrt(
        three_radius**2 - corner_x**2
    )

    ax.plot(
        [-corner_x, -corner_x],
        [-5.25, corner_y],
        color=court_color,
        linewidth=1.5
    )

    ax.plot(
        [corner_x, corner_x],
        [-5.25, corner_y],
        color=court_color,
        linewidth=1.5
    )

    # Consistent plotting dimensions
    ax.set_xlim(-26, 26)
    ax.set_ylim(-6, 42)
    ax.set_aspect("equal")
    ax.axis("off")

    # ==========================================
# 17. PLOT PLAYER SHOT CHARTS
# ==========================================

players = [
    "Kelsey Mitchell",
    "Jackie Young"
]

fig, axes = plt.subplots(
    1, 2,
    figsize=(14, 8)
)

for ax, player in zip(axes, players):

    player_data = field_goals[
        field_goals["athlete_name_1"] == player
    ]

    made = player_data[
        player_data["scoring_play"] == True
    ]

    missed = player_data[
        player_data["scoring_play"] == False
    ]

    # Draw court
    draw_wnba_court(ax)

    # Plot missed shots
    ax.scatter(
        missed["plot_x"],
        missed["plot_y"],
        color="#D9534F",
        marker="x",
        s=22,
        alpha=0.55,
        label="Missed",
        zorder=3
    )

    # Plot made shots
    ax.scatter(
        made["plot_x"],
        made["plot_y"],
        color="#2E8B57",
        marker="o",
        s=20,
        alpha=0.55,
        label="Made",
        zorder=4
    )

    ax.set_title(
        f"{player}\n{len(player_data)} FGA",
        fontsize=14,
        fontweight="bold",
        pad=12
    )

    ax.legend(
        loc="upper right",
        fontsize=9
    )

fig.suptitle(
    "2025 WNBA Regular Season | Shot Location Comparison",
    fontsize=17,
    fontweight="bold"
)

fig.text(
    0.5,
    0.03,
    "Source: SportsDataverse / ESPN | 2025 Regular Season",
    ha="center",
    fontsize=9,
    color="gray"
)

plt.tight_layout(rect=[0, 0.06, 1, 0.94])

plt.savefig(
    "visualizations/shot_location_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()