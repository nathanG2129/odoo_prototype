"""
Extract and standardize all unique stalls from fmStall.csv and fmStall_Electricity.csv
into Odoo kst.stall model format.
"""
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

def normalize_stallno(stallno):
    """Normalize stall number (remove extra spaces, handle empty)."""
    if pd.isna(stallno) or stallno == '':
        return None
    return str(stallno).strip()

def normalize_market(market):
    """Normalize market code and map to Odoo market IDs."""
    if pd.isna(market) or market == '':
        return 'bbh'  # Default to BBH
    market_code = str(market).strip().upper()
    # Map to existing Odoo market IDs (from markets_demo.xml)
    market_map = {
        'BBH': 'bbh',      # Bagong Barrio Hypermarket
        'KTC': 'ktc',      # Kalayaan Talipapa Corporation
        'STM': 'smt',      # Sample Market Text (STM in CSV = SMT in Odoo)
        'MALATE': 'bbh',   # Default MALATE to BBH (no MALATE market in Odoo yet)
    }
    return market_map.get(market_code, 'bbh')  # Default to BBH

def normalize_collection_type(collection_type):
    """Map CollectionType to rent_collection_type."""
    if pd.isna(collection_type) or collection_type == '':
        return 'monthly'  # default
    collection_type = str(collection_type).strip().upper()
    type_map = {
        'D': 'daily',
        'W': 'weekly',
        'M': 'monthly',
    }
    return type_map.get(collection_type, 'monthly')

def safe_float(value, default=0.0):
    """Safely convert to float."""
    if pd.isna(value) or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value, default=False):
    """Safely convert to boolean."""
    if pd.isna(value) or value == '':
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    value_str = str(value).strip().upper()
    return value_str in ['TRUE', '1', 'YES', 'T', '-1']

def safe_date(value):
    """Safely convert to date string."""
    if pd.isna(value) or value == '':
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, str):
        # Try to parse common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(value.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
    return None

def escape_xml(text):
    """Escape XML special characters."""
    if pd.isna(text) or text == '':
        return ''
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

def get_pay_type_ref(pay_type_code):
    """Map MDB pay type code to Odoo external ID."""
    if not pay_type_code or pay_type_code == '':
        return None
    pay_type_code = str(pay_type_code).strip().upper()
    # Map to Odoo external IDs (from generate_pay_types.py)
    pay_type_map = {
        'FR': 'pay_type_fr',
        'K1MH': 'pay_type_k1mh',
        'LG': 'pay_type_lg',
        'MO': 'pay_type_mo',
        'NW': 'pay_type_nw',
        'PT': 'pay_type_pt',
        'SM': 'pay_type_sm',
        'TL': 'pay_type_tl',
        'UGPM': 'pay_type_ugpm',
        'UGPW': 'pay_type_ugpw',
    }
    return pay_type_map.get(pay_type_code)

def load_and_combine_stalls():
    """Load stalls from both CSV files and combine unique stalls."""
    csv_dir = Path(__file__).parent / "master_data_csv"
    
    # Load fmStall.csv
    stall_file = csv_dir / "fmStall.csv"
    print(f"Loading {stall_file}...")
    df_stall = pd.read_csv(stall_file, encoding='utf-8-sig')
    print(f"  Loaded {len(df_stall)} rows from fmStall.csv")
    
    # Load fmStall_Electricity.csv
    elec_file = csv_dir / "fmStall_Electricity.csv"
    print(f"Loading {elec_file}...")
    df_elec = pd.read_csv(elec_file, encoding='utf-8-sig')
    print(f"  Loaded {len(df_elec)} rows from fmStall_Electricity.csv")
    
    # Combine both dataframes, prioritizing fmStall data
    # Use StallNo as the key
    stalls_dict = {}
    
    # First, process fmStall (primary source)
    print("\nProcessing fmStall.csv...")
    for idx, row in df_stall.iterrows():
        stallno = normalize_stallno(row.get('StallNo'))
        if not stallno:
            continue
        
        if stallno not in stalls_dict:
            stalls_dict[stallno] = {
                'StallNo': stallno,
                'TenantName': row.get('TenantName', ''),
                'Rate': safe_float(row.get('Rate')),
                'isActive': safe_bool(row.get('isActive'), True),
                'DateStart': safe_date(row.get('DateStart')),
                'DateEnd': safe_date(row.get('DateEnd')),
                'isOR': safe_bool(row.get('isOR')),
                'Martket': normalize_market(row.get('Martket')),  # Returns lowercase market ID
                'CollectionType': normalize_collection_type(row.get('CollectionType')),
                'Frequency': safe_float(row.get('Frequency'), 0.0),
                'WaterDailyRate': safe_float(row.get('WaterDailyRate')),
                'ElectricityDailyRate': safe_float(row.get('ElectricityDailyRate')),
                'MeterNumber': None,  # Will be filled from electricity table
                'ElecSubMeterNo': None,  # Will be filled from electricity table
                'ElectricPaymentType': None,  # Will be filled from electricity table
                'WaterPaymentType': None,  # Will be filled from electricity table
                'source': 'fmStall'
            }
    
    # Then, process fmStall_Electricity (supplement with utility info and add missing stalls)
    print("Processing fmStall_Electricity.csv...")
    added_from_elec = 0
    updated_from_elec = 0
    
    for idx, row in df_elec.iterrows():
        stallno = normalize_stallno(row.get('StallNo'))
        if not stallno:
            continue
        
        if stallno not in stalls_dict:
            # New stall not in fmStall
            stalls_dict[stallno] = {
                'StallNo': stallno,
                'TenantName': row.get('TenantName', ''),
                'Rate': safe_float(row.get('Rate')),
                'isActive': safe_bool(row.get('isActive'), True),
                'DateStart': safe_date(row.get('DateStart')),
                'DateEnd': safe_date(row.get('DateEnd')),
                'isOR': safe_bool(row.get('isOR')),
                'Martket': normalize_market(row.get('Martket')),  # Returns lowercase market ID
                'CollectionType': normalize_collection_type(row.get('CollectionType')),
                'Frequency': safe_float(row.get('Frequency'), 0.0),
                'WaterDailyRate': safe_float(row.get('WaterRatePerCubic')),  # Note: different field name
                'ElectricityDailyRate': safe_float(row.get('ElectricityDailyRate')),
                'MeterNumber': str(row.get('MeterNumber', '')).strip() if pd.notna(row.get('MeterNumber')) else None,
                'ElecSubMeterNo': str(row.get('ElecSubMeterNo', '')).strip() if pd.notna(row.get('ElecSubMeterNo')) else None,
                'ElectricPaymentType': str(row.get('ElectricPaymentType', '')).strip() if pd.notna(row.get('ElectricPaymentType')) else None,
                'WaterPaymentType': str(row.get('WaterPaymentType', '')).strip() if pd.notna(row.get('WaterPaymentType')) else None,
                'source': 'fmStall_Electricity'
            }
            added_from_elec += 1
        else:
            # Update existing stall with utility info if missing
            if not stalls_dict[stallno]['MeterNumber'] and pd.notna(row.get('MeterNumber')):
                stalls_dict[stallno]['MeterNumber'] = str(row.get('MeterNumber')).strip()
                updated_from_elec += 1
            if not stalls_dict[stallno]['ElecSubMeterNo'] and pd.notna(row.get('ElecSubMeterNo')):
                stalls_dict[stallno]['ElecSubMeterNo'] = str(row.get('ElecSubMeterNo')).strip()
                updated_from_elec += 1
            # Update pay types from electricity table
            if not stalls_dict[stallno]['ElectricPaymentType'] and pd.notna(row.get('ElectricPaymentType')):
                stalls_dict[stallno]['ElectricPaymentType'] = str(row.get('ElectricPaymentType')).strip()
            if not stalls_dict[stallno]['WaterPaymentType'] and pd.notna(row.get('WaterPaymentType')):
                stalls_dict[stallno]['WaterPaymentType'] = str(row.get('WaterPaymentType')).strip()
    
    print(f"\n✓ Combined stalls:")
    print(f"  Total unique stalls: {len(stalls_dict)}")
    print(f"  From fmStall: {len(stalls_dict) - added_from_elec}")
    print(f"  Added from fmStall_Electricity: {added_from_elec}")
    print(f"  Updated with utility info: {updated_from_elec}")
    
    return stalls_dict

def generate_odoo_xml(stalls_dict):
    """Generate Odoo XML demo data for stalls."""
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="1">',
        '    <!-- Standardized Stall Master Data -->',
        '    <!-- Generated from fmStall.csv and fmStall_Electricity.csv -->',
        ''
    ]
    
    # Group stalls by market for better organization
    markets = {}
    for stallno, stall_data in stalls_dict.items():
        market = stall_data.get('Martket') or 'UNKNOWN'
        if market not in markets:
            markets[market] = []
        markets[market].append((stallno, stall_data))
    
    # Generate XML records
    record_id_counter = 1
    
    for market in sorted(markets.keys()):
        market_name = market.upper() if market != 'UNKNOWN' else 'UNKNOWN'
        xml_lines.append(f'        <!-- {market_name} Market Stalls -->')
        
        for stallno, stall_data in sorted(markets[market], key=lambda x: x[0]):
            # Create a safe XML ID
            safe_id = f"stall_{market.lower()}_{record_id_counter:04d}"
            record_id_counter += 1
            
            # Build record
            xml_lines.append(f'        <record id="{safe_id}" model="kst.stall">')
            
            # Market (required) - use normalized market
            market_ref = stall_data.get('Martket') or 'bbh'
            xml_lines.append(f'            <field name="market_id" ref="market_{market_ref}"/>')
            
            # Code (required) - escape XML
            escaped_stallno = escape_xml(stallno)
            xml_lines.append(f'            <field name="code">{escaped_stallno}</field>')
            
            # Tenant (if available) - skip for now, will be handled separately
            # tenant_name = stall_data.get('TenantName', '').strip()
            # if tenant_name and tenant_name.upper() not in ['VACANT', '']:
            #     tenant_id = f"tenant_{tenant_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')[:50]}"
            #     xml_lines.append(f'            <field name="tenant_id" ref="{tenant_id}"/>')
            
            # Rental rate
            if stall_data.get('Rate', 0) > 0:
                xml_lines.append(f'            <field name="rental_rate">{stall_data["Rate"]:.2f}</field>')
            
            # Collection type
            xml_lines.append(f'            <field name="rent_collection_type">{stall_data.get("CollectionType", "monthly")}</field>')
            
            # Utility rates
            if stall_data.get('ElectricityDailyRate', 0) > 0:
                xml_lines.append(f'            <field name="default_electricity_rate">{stall_data["ElectricityDailyRate"]:.2f}</field>')
            
            if stall_data.get('WaterDailyRate', 0) > 0:
                xml_lines.append(f'            <field name="default_water_rate">{stall_data["WaterDailyRate"]:.2f}</field>')
            
            # Status flags
            is_active_val = str(stall_data.get('isActive', True)).lower()
            need_or_val = str(stall_data.get('isOR', False)).lower()
            xml_lines.append(f'            <field name="is_active" eval="{is_active_val}"/>')
            xml_lines.append(f'            <field name="need_or" eval="{need_or_val}"/>')
            
            # Utility account info - escape XML
            if stall_data.get('MeterNumber'):
                escaped_meter = escape_xml(stall_data["MeterNumber"])
                xml_lines.append(f'            <field name="meralco_account_number">{escaped_meter}</field>')
            
            if stall_data.get('ElecSubMeterNo'):
                escaped_submeter = escape_xml(stall_data["ElecSubMeterNo"])
                xml_lines.append(f'            <field name="electricity_sub_meter_number">{escaped_submeter}</field>')
            
            # Pay type assignments
            elec_pay_type_ref = get_pay_type_ref(stall_data.get('ElectricPaymentType'))
            if elec_pay_type_ref:
                xml_lines.append(f'            <field name="electric_pay_type_id" ref="{elec_pay_type_ref}"/>')
            
            water_pay_type_ref = get_pay_type_ref(stall_data.get('WaterPaymentType'))
            if water_pay_type_ref:
                xml_lines.append(f'            <field name="water_pay_type_id" ref="{water_pay_type_ref}"/>')
            
            xml_lines.append('        </record>')
            xml_lines.append('')
    
    xml_lines.append('    </data>')
    xml_lines.append('</odoo>')
    
    return '\n'.join(xml_lines)

def main():
    """Main function."""
    print("="*80)
    print("STALL STANDARDIZATION")
    print("="*80)
    
    # Load and combine stalls
    stalls_dict = load_and_combine_stalls()
    
    # Generate XML
    print("\n" + "="*80)
    print("GENERATING ODOO XML")
    print("="*80)
    
    xml_content = generate_odoo_xml(stalls_dict)
    
    # Save to file (in demo directory, not master_data_csv)
    output_file = Path(__file__).parent / "standardized_stalls.xml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"\n✓ Generated XML file: {output_file}")
    print(f"  Total stalls: {len(stalls_dict)}")
    
    # Print summary by market
    print("\n" + "="*80)
    print("SUMMARY BY MARKET")
    print("="*80)
    market_counts = {}
    for stall_data in stalls_dict.values():
        market = stall_data.get('Martket') or 'UNKNOWN'
        market_counts[market] = market_counts.get(market, 0) + 1
    
    for market, count in sorted(market_counts.items()):
        print(f"  {market:20s}: {count:4,} stalls")

if __name__ == '__main__':
    main()

