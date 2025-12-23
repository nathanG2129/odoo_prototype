"""
Analyze the extracted master data CSV files to understand structure and data quality.
"""
import pandas as pd
import os
from pathlib import Path

def analyze_csv(file_path, table_name):
    """Analyze a CSV file and provide insights."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {table_name}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return None
    
    # Read CSV
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return None
    
    print(f"\n✓ File loaded successfully")
    print(f"  Total rows: {len(df):,}")
    print(f"  Total columns: {len(df.columns)}")
    
    # Column analysis
    print(f"\n{'─'*80}")
    print("COLUMN ANALYSIS")
    print(f"{'─'*80}")
    print(f"\nColumn Names ({len(df.columns)} total):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # Data types
    print(f"\n{'─'*80}")
    print("DATA TYPES")
    print(f"{'─'*80}")
    dtype_summary = df.dtypes.value_counts()
    for dtype, count in dtype_summary.items():
        print(f"  {dtype}: {count} columns")
    
    # Missing values analysis
    print(f"\n{'─'*80}")
    print("MISSING VALUES ANALYSIS")
    print(f"{'─'*80}")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing Count': missing.values,
        'Missing %': missing_pct.values
    })
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    
    if len(missing_df) > 0:
        print(f"\nColumns with missing values ({len(missing_df)} total):")
        for _, row in missing_df.iterrows():
            print(f"  {row['Column']:30s} : {row['Missing Count']:5,} ({row['Missing %']:5.1f}%)")
    else:
        print("\n✓ No missing values found")
    
    # Unique values analysis
    print(f"\n{'─'*80}")
    print("UNIQUE VALUES ANALYSIS")
    print(f"{'─'*80}")
    for col in df.columns:
        unique_count = df[col].nunique()
        total_count = len(df)
        if unique_count < 20 and unique_count > 0:  # Show if relatively few unique values
            print(f"\n  {col} ({unique_count} unique values):")
            value_counts = df[col].value_counts().head(10)
            for val, count in value_counts.items():
                pct = (count / total_count * 100)
                print(f"    '{val}': {count:,} ({pct:.1f}%)")
        elif unique_count == total_count:
            print(f"  {col}: {unique_count:,} unique (likely ID/key field)")
        else:
            print(f"  {col}: {unique_count:,} unique values")
    
    # Sample data
    print(f"\n{'─'*80}")
    print("SAMPLE DATA (First 3 rows)")
    print(f"{'─'*80}")
    print(df.head(3).to_string())
    
    return df

def compare_tables(df_stall, df_electricity):
    """Compare the two tables to understand relationships."""
    print(f"\n{'='*80}")
    print("RELATIONSHIP ANALYSIS")
    print(f"{'='*80}")
    
    # Check if StallNo is the key
    if 'StallNo' in df_stall.columns and 'StallNo' in df_electricity.columns:
        stall_stallnos = set(df_stall['StallNo'].dropna().unique())
        elec_stallnos = set(df_electricity['StallNo'].dropna().unique())
        
        print(f"\nStallNo Analysis:")
        print(f"  Unique StallNo in fmStall: {len(stall_stallnos):,}")
        print(f"  Unique StallNo in fmStall_Electricity: {len(elec_stallnos):,}")
        print(f"  Common StallNo: {len(stall_stallnos & elec_stallnos):,}")
        print(f"  Only in fmStall: {len(stall_stallnos - elec_stallnos):,}")
        print(f"  Only in fmStall_Electricity: {len(elec_stallnos - stall_stallnos):,}")
        
        # Show some examples
        only_in_stall = list(stall_stallnos - elec_stallnos)[:10]
        only_in_elec = list(elec_stallnos - stall_stallnos)[:10]
        
        if only_in_stall:
            print(f"\n  Sample StallNo only in fmStall (first 10):")
            for sn in only_in_stall:
                print(f"    - {sn}")
        
        if only_in_elec:
            print(f"\n  Sample StallNo only in fmStall_Electricity (first 10):")
            for sn in only_in_elec:
                print(f"    - {sn}")
    
    # Check for common columns
    common_cols = set(df_stall.columns) & set(df_electricity.columns)
    print(f"\nCommon columns between tables ({len(common_cols)}):")
    for col in sorted(common_cols):
        print(f"  - {col}")
    
    # Check for market distribution
    if 'Martket' in df_stall.columns:
        print(f"\n{'─'*80}")
        print("MARKET DISTRIBUTION (fmStall)")
        print(f"{'─'*80}")
        market_counts = df_stall['Martket'].value_counts()
        for market, count in market_counts.items():
            pct = (count / len(df_stall) * 100)
            print(f"  {market:20s}: {count:4,} ({pct:5.1f}%)")
    
    if 'Martket' in df_electricity.columns:
        print(f"\n{'─'*80}")
        print("MARKET DISTRIBUTION (fmStall_Electricity)")
        print(f"{'─'*80}")
        market_counts = df_electricity['Martket'].value_counts()
        for market, count in market_counts.items():
            pct = (count / len(df_electricity) * 100)
            print(f"  {market:20s}: {count:4,} ({pct:5.1f}%)")

def main():
    """Main analysis function."""
    # Get CSV directory
    csv_dir = Path(__file__).parent / "master_data_csv"
    
    print("="*80)
    print("MASTER DATA ANALYSIS")
    print("="*80)
    print(f"\nCSV Directory: {csv_dir}")
    
    # Analyze fmStall
    stall_file = csv_dir / "fmStall.csv"
    df_stall = analyze_csv(stall_file, "fmStall")
    
    # Analyze fmStall_Electricity
    elec_file = csv_dir / "fmStall_Electricity.csv"
    df_electricity = analyze_csv(elec_file, "fmStall_Electricity")
    
    # Compare tables
    if df_stall is not None and df_electricity is not None:
        compare_tables(df_stall, df_electricity)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()

