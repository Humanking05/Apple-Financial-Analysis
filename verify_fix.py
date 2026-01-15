import pandas as pd
import numpy as np
import os

def check_fix():
    print("Verifying fix for CAGR calculation...")
    
    # Mock data with NaN at start
    data = {"Total Revenue": [np.nan, 100, 110, 121]}
    idx = pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"])
    series = pd.Series(data["Total Revenue"], index=idx)
    
    print(f"Test Series:\n{series}")
    
    # Applied Fix Logic
    series_dropped = series.dropna()
    start = series_dropped.iloc[0]
    end = series_dropped.iloc[-1]
    periods = len(series_dropped) - 1
    
    cagr = (end / start) ** (1 / periods) - 1
    
    print(f"\nStart: {start}, End: {end}, Periods: {periods}")
    print(f"Calculated CAGR: {cagr:.4f}")
    
    if np.isnan(cagr):
        print("❌ Fix Failed: Result is still NaN")
    else:
        print("✅ Fix Verified: Result is a valid number")
        assert abs(cagr - 0.1) < 0.0001 # Should be 10%

if __name__ == "__main__":
    check_fix()
