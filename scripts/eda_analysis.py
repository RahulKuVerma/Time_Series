"""
scripts/eda_analysis.py
-----------------------
Generates publication-quality Exploratory Data Analysis (EDA) visualizations
and statistical summaries for the Energy Consumption Forecasting project.
Outputs saved to `reports/figures/`.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def generate_eda_visualizations(
    csv_path: str = "data/processed/dataset_augmented_5000.csv",
    output_dir: str = "reports/figures"
):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)
    df['parsed_dt'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['parsed_dt'].dt.hour
    df['day_name'] = df['parsed_dt'].dt.day_name()

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    palette = {'DataCenter': '#2563EB', 'Office_A': '#10B981', 'Office_B': '#F59E0B', 'Warehouse': '#8B5CF6', 'Canteen': '#EC4899'}

    # 1. Time Series of Energy Consumption Over Time
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    for b_id, color in palette.items():
        sub = df[df['building_id'] == b_id].sort_values('parsed_dt').iloc[:200] # First 200 hours for clarity
        ax.plot(sub['parsed_dt'], sub['consumption_kWh'], label=b_id, color=color, linewidth=1.8, alpha=0.85)

    ax.set_title("Figure 1: Energy Consumption Over Time (Hourly Cadence per Building)", fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel("Timestamp (Local Time)", fontsize=11, labelpad=8)
    ax.set_ylabel("Consumption (kWh)", fontsize=11, labelpad=8)
    ax.legend(title="Building Category", frameon=True, loc='upper right')
    fig.autofmt_xdate()
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "fig1_consumption_over_time.png")
    fig.savefig(fig1_path)
    plt.close(fig)
    print(f"Saved: {fig1_path}")

    # 2. Consumption Distribution & Outlier View per Building (Boxplot & Violin)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    # Boxplot
    buildings = list(palette.keys())
    data_by_building = [df[df['building_id'] == b]['consumption_kWh'].values for b in buildings]
    bplot = ax1.boxplot(data_by_building, tick_labels=buildings, patch_artist=True, medianprops=dict(color='black', linewidth=1.5))
    for patch, color in zip(bplot['boxes'], palette.values()):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax1.set_title("Consumption Distribution & Outliers by Building", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Consumption (kWh)", fontsize=10)
    ax1.tick_params(axis='x', rotation=25)

    # Histogram/Density
    for b_id, color in palette.items():
        sub = df[df['building_id'] == b_id]['consumption_kWh']
        ax2.hist(sub, bins=25, alpha=0.5, label=b_id, color=color, density=True)
    ax2.set_title("Probability Density Distribution", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Consumption (kWh)", fontsize=10)
    ax2.set_ylabel("Density", fontsize=10)
    ax2.legend(title="Building", frameon=True)

    fig.suptitle("Figure 2: Energy Consumption Statistical Spread & Anomaly Boundaries", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "fig2_consumption_distribution.png")
    fig.savefig(fig2_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {fig2_path}")

    # 3. Diurnal (Hour of Day) & Day Type Profiles
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    hourly_mean = df.groupby(['hour', 'building_id'])['consumption_kWh'].mean().unstack()
    for col in hourly_mean.columns:
        ax1.plot(hourly_mean.index, hourly_mean[col], marker='o', markersize=4, label=col, color=palette.get(col, '#333'), linewidth=2)
    ax1.set_title("Average Diurnal Profile (24-Hour Cycle)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Hour of Day (0 - 23)", fontsize=10)
    ax1.set_ylabel("Mean Consumption (kWh)", fontsize=10)
    ax1.set_xticks(range(0, 24, 2))
    ax1.legend(title="Building")

    day_type_mean = df.groupby(['day_type', 'building_id'])['consumption_kWh'].mean().unstack()
    day_type_mean.plot(kind='bar', ax=ax2, colormap='viridis', alpha=0.85, edgecolor='black')
    ax2.set_title("Mean Consumption by Day Type (Weekday vs Weekend vs Holiday)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Operating Schedule Type", fontsize=10)
    ax2.set_ylabel("Mean Consumption (kWh)", fontsize=10)
    ax2.tick_params(axis='x', rotation=0)

    fig.suptitle("Figure 3: Temporal Operating Schedules and Diurnal Load Dynamics", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "fig3_diurnal_and_weekly_patterns.png")
    fig.savefig(fig3_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {fig3_path}")

    # 4. Correlation with Weather Features (Temperature & Humidity)
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    numeric_cols = ['consumption_kWh', 'temperature_C', 'humidity_pct', 'hour']
    corr = df[numeric_cols].corr()

    cax = ax.matshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)

    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=35, ha='left', fontsize=10)
    ax.set_yticklabels(numeric_cols, fontsize=10)

    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            val = corr.iloc[i, j]
            ax.text(j, i, f"{val:.2f}", ha='center', va='center', color='black' if abs(val) < 0.6 else 'white', fontweight='bold')

    ax.set_title("Figure 4: Pearson Correlation Matrix (Exogenous Weather & Load Dynamics)", fontsize=12, fontweight='bold', pad=25)
    plt.tight_layout()
    fig4_path = os.path.join(output_dir, "fig4_weather_correlation_matrix.png")
    fig.savefig(fig4_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {fig4_path}")

if __name__ == "__main__":
    generate_eda_visualizations()
