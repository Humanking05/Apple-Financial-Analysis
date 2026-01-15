import pandas as pd
import numpy as np
import os

def debug_data():
    base_dir = os.getcwd()
    notebooks_dir = os.path.join(base_dir, "notebooks")
    
    print(f"Loading data from: {notebooks_dir}")
    try:
        income = pd.read_csv(os.path.join(notebooks_dir, "apple_income_statement.csv"), index_col=0, parse_dates=True).sort_index()
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Income DataFrame Info:")
    print(income.info())
    print("\nHead:")
    print(income.head())
    print("\nTail:")
    print(income.tail())
    
    rev_series = income["Total Revenue"]
    print("\nTotal Revenue Series:")
    print(rev_series)
    
    start = rev_series.iloc[0]
    end = rev_series.iloc[-1]
    print(f"\nStart Value (iloc[0]): {start}, Type: {type(start)}")
    print(f"End Value (iloc[-1]): {end}, Type: {type(end)}")
    
    def calculate_cagr(series):
        if len(series) < 2: return 0.0
        start = series.iloc[0]
        end = series.iloc[-1]
        if start == 0: return 0.0
        return (end / start) ** (1 / (len(series) - 1)) - 1

    cagr = calculate_cagr(rev_series)
    print(f"\nCalculated CAGR: {cagr}")
    
    # Check Net Income too
    ni_series = income["Net Income"]
    print("\nNet Income Series:")
    print(ni_series)
    ni_cagr = calculate_cagr(ni_series)
    print(f"Net Income CAGR: {ni_cagr}")

if __name__ == "__main__":
    debug_data()
