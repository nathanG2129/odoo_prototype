"""
Analyze pay type data to understand:
1. All pay types from fmPayType
2. Stall-to-pay-type mappings from DailyCollection_Electricity
3. Which stalls use which pay types for electricity and water
"""
import pandas as pd
import os
from pathlib import Path
from collections import defaultdict

def normalize_stallno(stallno):
    """Normalize stall number."""
    if pd.isna(stallno) or stallno == '':
        return None
    return str(stallno).strip()

def analyze_pay_types():
    """Analyze pay type data."""
    csv_dir = Path(__file__).parent / "master_data_csv"
    
    print("="*80)
    print("PAY TYPE ANALYSIS")
    print("="*80)
    
    # Load fmPayType
    paytype_file = csv_dir / "fmPayType.csv"
    if not paytype_file.exists():
        print(f"\n✗ File not found: {paytype_file}")
        print("Please run extract_pay_types.py first")
        return
    
    print(f"\nLoading {paytype_file}...")
    paytype_df = pd.read_csv(paytype_file, encoding='utf-8-sig')
    print(f"✓ Loaded {len(paytype_df)} pay types")
    print(f"\nPay Type Columns: {paytype_df.columns.tolist()}")
    print(f"\nPay Types:")
    print(paytype_df.to_string())
    
    # Load fmStall_Electricity (has ElectricPaymentType and WaterPaymentType columns)
    stall_elec_file = csv_dir / "fmStall_Electricity.csv"
    if not stall_elec_file.exists():
        print(f"\n✗ File not found: {stall_elec_file}")
        print("Please run extract_master_data.py first")
        return
    
    print(f"\n\nLoading {stall_elec_file}...")
    daily_df = pd.read_csv(stall_elec_file, encoding='utf-8-sig')
    print(f"✓ Loaded {len(daily_df)} stall records")
    print(f"\nfmStall_Electricity Columns: {daily_df.columns.tolist()}")
    
    # Analyze ElectricPaymentType values
    if 'ElectricPaymentType' in daily_df.columns:
        print(f"\n\nElectricPaymentType values (unique):")
        elec_pay_types = daily_df['ElectricPaymentType'].value_counts()
        print(elec_pay_types)
    
    # Analyze WaterPaymentType values
    if 'WaterPaymentType' in daily_df.columns:
        print(f"\n\nWaterPaymentType values (unique):")
        water_pay_types = daily_df['WaterPaymentType'].value_counts()
        print(water_pay_types)
    
    # Group by StallNo and analyze pay types
    print("\n" + "="*80)
    print("STALL-TO-PAY-TYPE MAPPINGS")
    print("="*80)
    
    if 'StallNo' in daily_df.columns:
        # Get unique stalls
        unique_stalls = daily_df['StallNo'].dropna().unique()
        print(f"\nTotal unique stalls in fmStall_Electricity: {len(unique_stalls)}")
        
        # Analyze pay types per stall
        stall_pay_types = defaultdict(lambda: {'electricity': set(), 'water': set()})
        
        for idx, row in daily_df.iterrows():
            stallno = normalize_stallno(row.get('StallNo'))
            if not stallno:
                continue
            
            # Get electric pay type
            elec_pay_type = str(row.get('ElectricPaymentType', '')).strip() if pd.notna(row.get('ElectricPaymentType')) else ''
            if elec_pay_type:
                stall_pay_types[stallno]['electricity'].add(elec_pay_type)
            
            # Get water pay type
            water_pay_type = str(row.get('WaterPaymentType', '')).strip() if pd.notna(row.get('WaterPaymentType')) else ''
            if water_pay_type:
                stall_pay_types[stallno]['water'].add(water_pay_type)
        
        # Print summary
        print(f"\n\nStalls with pay type assignments: {len(stall_pay_types)}")
        
        # Count stalls by pay type
        elec_pay_type_counts = defaultdict(int)
        water_pay_type_counts = defaultdict(int)
        
        for stallno, pay_types in stall_pay_types.items():
            for pt in pay_types['electricity']:
                elec_pay_type_counts[pt] += 1
            for pt in pay_types['water']:
                water_pay_type_counts[pt] += 1
        
        print(f"\n\nElectricity Pay Types (by frequency):")
        for pt, count in sorted(elec_pay_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {pt:20s}: {count:4,} stalls")
        
        print(f"\n\nWater Pay Types (by frequency):")
        for pt, count in sorted(water_pay_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {pt:20s}: {count:4,} stalls")
        
        # Show sample mappings
        print(f"\n\nSample Stall-to-Pay-Type Mappings (first 20):")
        sample_count = 0
        for stallno, pay_types in sorted(stall_pay_types.items())[:20]:
            elec_types = ', '.join(sorted(pay_types['electricity'])) if pay_types['electricity'] else 'None'
            water_types = ', '.join(sorted(pay_types['water'])) if pay_types['water'] else 'None'
            print(f"  {stallno:15s} | Elec: {elec_types:20s} | Water: {water_types:20s}")
            sample_count += 1
        
        return stall_pay_types, paytype_df, daily_df
    
    return None, paytype_df, daily_df

if __name__ == '__main__':
    analyze_pay_types()

