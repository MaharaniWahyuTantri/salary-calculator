import pandas as pd
import numpy as np
from scipy import stats

# ====================== KONSTANTA ======================
PERCENTILE_FACTORS = {10: 0.70, 25: 0.85, 50: 1.00, 60: 1.08, 75: 1.18, 90: 1.35, 95: 1.50}
DEFAULT_GRADE_NAMES = ['CXO', 'Sr Vice President', 'Vice President', 'Sr Director', 'Director', 
                       'Sr Manager', 'Principal', 'Manager IC', 'Sr Analyst', 'Analyst']

# ====================== FUNGSI HELPER ======================
def calculate_overlap(min_series, max_series):
    overlap = [0]
    for i in range(1, len(min_series)):
        prev_max = max_series.iloc[i-1]
        prev_min = min_series.iloc[i-1]
        curr_min = min_series.iloc[i]
        if prev_max > curr_min and (prev_max - prev_min) > 0:
            ov = (prev_max - curr_min) / (prev_max - prev_min) * 100
        else:
            ov = 0
        overlap.append(ov)
    return overlap

# ====================== FUNGSI VALIDASI ======================
def validate_scenario_1(df):
    errors = []
    for idx, row in df.iterrows():
        if row['Minimum'] >= row['Maximum']:
            errors.append(f"Grade {idx+1}: Minimum harus lebih kecil dari Maximum")
    return errors

# ====================== FUNGSI PERHITUNGAN ======================
def calculate_scenario_1(df_input):
    df = df_input.copy()
    df['Midpoint'] = (df['Minimum'] + df['Maximum']) / 2
    df['Spread %'] = ((df['Maximum'] - df['Minimum']) / df['Midpoint']) * 100
    df['Range'] = df['Maximum'] - df['Minimum']
    df['Mid Point Differential %'] = df['Midpoint'].pct_change() * 100
    df['Overlap %'] = calculate_overlap(df['Minimum'], df['Maximum'])
    return df

def calculate_scenario_2(df_input, lowest_midpoint, highest_midpoint):
    df = df_input.copy()
    n = len(df)
    df['Midpoint'] = np.linspace(lowest_midpoint, highest_midpoint, n)
    df['Minimum'] = df['Midpoint'] * (1 - df['Spread %'] / 200)
    df['Maximum'] = df['Midpoint'] * (1 + df['Spread %'] / 200)
    df['Range'] = df['Maximum'] - df['Minimum']
    df['Mid Point Differential %'] = df['Midpoint'].pct_change() * 100
    df['Overlap %'] = calculate_overlap(df['Minimum'], df['Maximum'])
    return df

def calculate_scenario_3(df_input, lowest_midpoint):
    df = df_input.copy()
    midpoints = [lowest_midpoint]
    for i in range(1, len(df)):
        next_mid = midpoints[-1] * (1 + df.iloc[i]['Midpoint Differential %'] / 100)
        midpoints.append(next_mid)
    df['Midpoint'] = midpoints
    df['Minimum'] = df['Midpoint'] * (1 - df['Spread %'] / 200)
    df['Maximum'] = df['Midpoint'] * (1 + df['Spread %'] / 200)
    df['Range'] = df['Maximum'] - df['Minimum']
    df['Overlap %'] = calculate_overlap(df['Minimum'], df['Maximum'])
    return df

def calculate_scenario_4(df_input):
    df = df_input.copy()
    df['Minimum'] = df['Midpoint'] * (1 - df['Spread %'] / 200)
    df['Maximum'] = df['Midpoint'] * (1 + df['Spread %'] / 200)
    df['Range'] = df['Maximum'] - df['Minimum']
    df['Mid Point Differential %'] = df['Midpoint'].pct_change() * 100
    df['Overlap %'] = calculate_overlap(df['Minimum'], df['Maximum'])
    return df

def calculate_scenario_5(df_input, target_percentile):
    df = df_input.copy()
    if target_percentile in PERCENTILE_FACTORS:
        adjustment_factor = PERCENTILE_FACTORS[target_percentile]
    else:
        adjustment_factor = 1 + (target_percentile - 50) / 100
    df['Midpoint'] = df['Market Rate'] * adjustment_factor
    df['Minimum'] = df['Midpoint'] * (1 - df['Spread %'] / 200)
    df['Maximum'] = df['Midpoint'] * (1 + df['Spread %'] / 200)
    df['Range'] = df['Maximum'] - df['Minimum']
    df['Mid Point Differential %'] = df['Midpoint'].pct_change() * 100
    df['Overlap %'] = calculate_overlap(df['Minimum'], df['Maximum'])
    return df