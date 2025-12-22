"""
Extract real stall data from Access database and generate demo data.
"""
import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import random
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
try:
    from kst_statistics.config import get_connection_string, DEFAULT_DB_PATH
except ImportError:
    # Fallback if import fails
    DEFAULT_DB_PATH = r"C:\KST_DB.mdb"
    def get_connection_string(db_path=None):
        path = db_path or DEFAULT_DB_PATH
        return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

def extract_stall_data(db_path=None):
    """Extract real stall data from Access database."""
    conn_str = get_connection_string(db_path)
    
    try:
        conn = pyodbc.connect(conn_str)
        print("Connected to Access database successfully!")
        
        # Extract stalls
        print("\nExtracting stalls from fmStall...")
        query_stalls = """
            SELECT TOP 30 
                [StallNo], 
                [TenantName],
                [Rate],
                [CollectionType],
                [Frequency],
                [Martket] AS [Market],
                [isActive],
                [isOR] AS [needOR],
                [DateStart],
                [DateEnd],
                [ElectricityDailyRate],
                [WaterDailyRate]
            FROM [fmStall]
            WHERE [isActive] = -1
            ORDER BY [StallNo]
        """
        
        df_stalls = pd.read_sql(query_stalls, conn)
        print(f"Found {len(df_stalls)} active stalls")
        
        # Extract markets (from stall data or separate table)
        print("\nExtracting markets...")
        # Markets might be in a separate table or derived from StallNo prefix
        # For now, we'll extract unique markets from the data
        markets = df_stalls['Market'].dropna().unique() if 'Market' in df_stalls.columns else []
        
        # Extract tenants
        print("\nExtracting tenants...")
        tenants = df_stalls['TenantName'].dropna().unique() if 'TenantName' in df_stalls.columns else []
        
        # Extract electricity/utility data (try to get from related tables)
        print("\nExtracting utility data from fmStall_Electricity...")
        try:
            query_utility = """
                SELECT TOP 100
                    [StallNo],
                    [MeralcoAccountNumber],
                    [ElectricitySubMeterNumber],
                    [ElectricPaymentType],
                    [WaterPaymentType]
                FROM [fmStall_Electricity]
                WHERE [isActive] = -1
            """
            df_utility = pd.read_sql(query_utility, conn)
            print(f"Found {len(df_utility)} utility records")
        except Exception as e:
            print(f"Could not extract utility data: {e}")
            df_utility = pd.DataFrame()
        
        conn.close()
        
        return {
            'stalls': df_stalls,
            'markets': markets,
            'tenants': tenants,
            'utility_data': df_utility if 'df_utility' in locals() else pd.DataFrame()
        }
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"\nTrying database path: {db_path or DEFAULT_DB_PATH}")
        return None

def generate_demo_from_real_data(extracted_data, output_file='kst_markets_demo.xml'):
    """Generate Odoo demo data XML from real Access database data."""
    
    if not extracted_data:
        print("No data extracted. Cannot generate demo data.")
        return
    
    df_stalls = extracted_data['stalls']
    markets = extracted_data['markets']
    tenants = extracted_data['tenants']
    df_utility = extracted_data.get('utility_data', pd.DataFrame())
    
    # Merge utility data with stalls if available
    if not df_utility.empty and 'StallNo' in df_utility.columns:
        df_stalls = df_stalls.merge(
            df_utility[['StallNo', 'MeralcoAccountNumber', 'ElectricitySubMeterNumber']].drop_duplicates(subset=['StallNo']),
            on='StallNo',
            how='left'
        )
    
    print(f"\nGenerating demo data from {len(df_stalls)} real stalls...")
    
    # Map collection types
    collection_type_map = {
        'DAILY': 'daily',
        'WEEKLY': 'weekly',
        'MONTHLY': 'monthly',
        'Daily': 'daily',
        'Weekly': 'weekly',
        'Monthly': 'monthly',
    }
    
    # Generate dates
    TODAY = datetime.now()
    monthly_dates = []
    for i in range(7):
        date = TODAY.replace(day=1) - timedelta(days=32 * i)
        date = date.replace(day=1)
        monthly_dates.append(date)
    monthly_dates = sorted(monthly_dates)
    
    daily_dates = []
    current = TODAY.replace(day=1) - timedelta(days=32 * 6)
    current = current.replace(day=1)
    while current <= TODAY:
        if current.weekday() < 5:
            daily_dates.append(current)
        current += timedelta(days=1)
    daily_dates = sorted(daily_dates)
    
    weekly_dates = []
    current = TODAY.replace(day=1) - timedelta(days=32 * 6)
    current = current.replace(day=1)
    while current.weekday() != 0:
        current += timedelta(days=1)
    while current <= TODAY:
        weekly_dates.append(current)
        current += timedelta(days=7)
    weekly_dates = sorted(weekly_dates)
    
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        '',
        '        <!-- Market Pay Types -->',
    ]
    
    # Pay Types (create standard ones)
    pay_types = [
        ('K1-MH', 'K1 Monthly', 'electricity', 'monthly'),
        ('UGS Weekly', 'UGS Weekly', 'electricity', 'weekly'),
        ('LG Daily', 'LG Daily', 'electricity', 'daily'),
        ('NAWASA', 'NAWASA Monthly', 'water', 'monthly'),
        ('Water Weekly', 'Water Weekly', 'water', 'weekly'),
    ]
    
    pay_type_refs = {}
    for code, name, use, subgroup in pay_types:
        ref_id = f"pay_type_{code.lower().replace(' ', '_').replace('-', '_')}"
        pay_type_refs[code] = ref_id
        xml_lines.append(f'        <record id="{ref_id}" model="kst.market.pay.type">')
        xml_lines.append(f'            <field name="code">{code}</field>')
        xml_lines.append(f'            <field name="name">{name}</field>')
        xml_lines.append(f'            <field name="pay_type_use">{use}</field>')
        xml_lines.append(f'            <field name="sub_group">{subgroup}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Markets (from real data or create defaults)
    xml_lines.append('        <!-- Markets -->')
    market_refs = {}
    if len(markets) > 0:
        for i, market_code in enumerate(markets[:3]):  # Limit to 3 markets
            ref_id = f"market_{str(market_code).lower().replace(' ', '_')}"
            market_refs[market_code] = ref_id
            xml_lines.append(f'        <record id="{ref_id}" model="kst.market">')
            xml_lines.append(f'            <field name="code">{market_code}</field>')
            xml_lines.append(f'            <field name="name">{market_code} Market</field>')
            xml_lines.append(f'            <field name="address">Market Address</field>')
            xml_lines.append(f'        </record>')
            xml_lines.append('')
    else:
        # Default markets if none found
        for code in ['BBH', 'KTC', 'SIL']:
            ref_id = f"market_{code.lower()}"
            market_refs[code] = ref_id
            xml_lines.append(f'        <record id="{ref_id}" model="kst.market">')
            xml_lines.append(f'            <field name="code">{code}</field>')
            xml_lines.append(f'            <field name="name">{code} Market</field>')
            xml_lines.append(f'            <field name="address">Market Address</field>')
            xml_lines.append(f'        </record>')
            xml_lines.append('')
    
    # Tenants (from real data)
    xml_lines.append('        <!-- Tenants -->')
    tenant_refs = {}
    unique_tenants = list(set(tenants))[:20]  # Limit to 20 unique tenants
    tenant_counter = 1
    for tenant_name in unique_tenants:
        if pd.isna(tenant_name) or tenant_name == '' or tenant_name.strip() == '':
            continue
        ref_id = f"tenant_{tenant_counter}"
        tenant_refs[tenant_name] = ref_id
        start_date = TODAY - timedelta(days=random.randint(90, 730))
        xml_lines.append(f'        <record id="{ref_id}" model="kst.tenant">')
        xml_lines.append(f'            <field name="name">{tenant_name}</field>')
        xml_lines.append(f'            <field name="date_started">{start_date.strftime("%Y-%m-%d")}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
        tenant_counter += 1
    
    # Add any additional tenants found in stalls but not in the initial list
    additional_tenants = []
    
    # Stall Groups (create standard ones)
    xml_lines.append('        <!-- Stall Groups -->')
    stall_group_refs = {}
    stall_groups = [
        ('LG', 'pay_type_lg_daily', 'pay_type_water_weekly'),
        ('UGP', 'pay_type_ugs_weekly', 'pay_type_nawasa'),
        ('K1-MH', 'pay_type_k1_mh', 'pay_type_nawasa'),
    ]
    for code, elec_ref, water_ref in stall_groups:
        ref_id = f"stall_group_{code.lower().replace('-', '_')}"
        stall_group_refs[code] = ref_id
        xml_lines.append(f'        <record id="{ref_id}" model="kst.stall.group">')
        xml_lines.append(f'            <field name="code">{code}</field>')
        xml_lines.append(f'            <field name="electric_pay_type_id" ref="{elec_ref}"/>')
        xml_lines.append(f'            <field name="water_pay_type_id" ref="{water_ref}"/>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Stalls (from real data)
    xml_lines.append('        <!-- Stalls (from real data) -->')
    stall_refs = []
    stall_info_dict = {}  # Track stall info: {ref_id: {'freq': 'monthly', 'rate': 5000, 'cobp': 0}}
    accumulated_cobp_by_stall = {}  # Track COBP per stall
    additional_tenants = []  # Track tenants found in stalls but not in initial list
    
    for idx, row in df_stalls.iterrows():
        stall_no = str(row.get('StallNo', f'STALL_{idx}')).strip()
        tenant_name = str(row.get('TenantName', '')).strip() if pd.notna(row.get('TenantName')) else f'Tenant_{idx}'
        rate = float(row.get('Rate', 0)) if pd.notna(row.get('Rate')) else random.randint(3000, 8000)
        collection_type = str(row.get('CollectionType', 'MONTHLY')).strip().upper() if pd.notna(row.get('CollectionType')) else 'MONTHLY'
        market = str(row.get('Market', 'BBH')).strip() if pd.notna(row.get('Market')) else 'BBH'
        is_active = bool(row.get('isActive', True)) if pd.notna(row.get('isActive')) else True
        need_or = bool(row.get('needOR', False)) if pd.notna(row.get('needOR')) else False
        meralco = str(row.get('MeralcoAccountNumber', '')).strip() if pd.notna(row.get('MeralcoAccountNumber')) else ''
        sub_meter = str(row.get('ElectricitySubMeterNumber', '')).strip() if pd.notna(row.get('ElectricitySubMeterNumber')) else f'SM-{idx+1:03d}'
        elec_rate = float(row.get('ElectricityDailyRate', 0)) if pd.notna(row.get('ElectricityDailyRate')) else round(random.uniform(12.0, 22.0), 2)
        
        # Map collection type
        rent_freq = collection_type_map.get(collection_type, 'monthly')
        
        # Get market reference
        if market in market_refs:
            market_ref = market_refs[market]
        else:
            # Use first available market
            market_ref = list(market_refs.values())[0] if market_refs else 'market_bbh'
        
        # Get tenant reference
        if tenant_name in tenant_refs:
            tenant_ref = tenant_refs[tenant_name]
        else:
            # Create a new tenant reference and add to list for later insertion
            tenant_ref = f"tenant_{len(tenant_refs) + 1}"
            tenant_refs[tenant_name] = tenant_ref
            additional_tenants.append((tenant_ref, tenant_name))
        
        # Calculate rental rate based on frequency
        monthly_rent = rate
        if rent_freq == 'daily':
            rental_rate = round(monthly_rent / 22, 2)
        elif rent_freq == 'weekly':
            rental_rate = round(monthly_rent / 4, 2)
        else:
            rental_rate = monthly_rent
        
        # Assign stall group (70% have groups)
        has_group = random.random() < 0.7
        if has_group:
            group_code = random.choice(stall_groups)[0]
            group_ref = stall_group_refs[group_code]
        else:
            group_ref = None
        
        # Assign pay types
        elec_pay_type = pay_type_refs[random.choice(['LG Daily', 'UGS Weekly', 'K1-MH'])]
        water_pay_type = pay_type_refs[random.choice(['NAWASA', 'Water Weekly'])]
        
        # Create stall reference
        stall_code_clean = stall_no.replace(' ', '_').replace('-', '_').replace('/', '_').replace('\\', '_')
        ref_id = f"stall_{market_ref.replace('market_', '')}_{stall_code_clean}"
        stall_refs.append(ref_id)
        accumulated_cobp_by_stall[ref_id] = 0.0
        stall_info_dict[ref_id] = {'freq': rent_freq, 'rate': rental_rate}
        
        xml_lines.append(f'        <record id="{ref_id}" model="kst.stall">')
        xml_lines.append(f'            <field name="market_id" ref="{market_ref}"/>')
        xml_lines.append(f'            <field name="code">{stall_no}</field>')
        xml_lines.append(f'            <field name="tenant_id" ref="{tenant_ref}"/>')
        if group_ref:
            xml_lines.append(f'            <field name="stall_group_id" ref="{group_ref}"/>')
        xml_lines.append(f'            <field name="rental_rate">{rental_rate:.2f}</field>')
        xml_lines.append(f'            <field name="electricity_rate">{elec_rate:.2f}</field>')
        xml_lines.append(f'            <field name="electric_pay_type_id" ref="{elec_pay_type}"/>')
        xml_lines.append(f'            <field name="water_pay_type_id" ref="{water_pay_type}"/>')
        xml_lines.append(f'            <field name="rent_collection_type">{rent_freq}</field>')
        xml_lines.append(f'            <field name="is_active">{str(is_active).lower()}</field>')
        xml_lines.append(f'            <field name="need_or">{str(need_or).lower()}</field>')
        if meralco:
            xml_lines.append(f'            <field name="meralco_account_number">{meralco}</field>')
        xml_lines.append(f'            <field name="electricity_sub_meter_number">{sub_meter}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Add additional tenants that were found in stalls
    if additional_tenants:
        # Insert after the last tenant record
        tenant_section_end = None
        for i, line in enumerate(xml_lines):
            if '<!-- Stall Groups -->' in line:
                tenant_section_end = i
                break
        
        if tenant_section_end:
            insert_pos = tenant_section_end
            for tenant_ref, tenant_name in additional_tenants:
                start_date = TODAY - timedelta(days=random.randint(90, 730))
                xml_lines.insert(insert_pos, f'        <record id="{tenant_ref}" model="kst.tenant">')
                xml_lines.insert(insert_pos + 1, f'            <field name="name">{tenant_name}</field>')
                xml_lines.insert(insert_pos + 2, f'            <field name="date_started">{start_date.strftime("%Y-%m-%d")}</field>')
                xml_lines.insert(insert_pos + 3, f'        </record>')
                xml_lines.insert(insert_pos + 4, '')
                insert_pos += 5
    
    # Generate transactions for each stall
    xml_lines.append('        <!-- Market Rent Transactions -->')
    trans_counter = 1
    
    for stall_ref in stall_refs:
        # Get stall info from our tracking dict
        if stall_ref in stall_info_dict:
            rent_freq = stall_info_dict[stall_ref]['freq']
            base_rate = stall_info_dict[stall_ref]['rate']
        else:
            # Default if not found
            rent_freq = 'monthly'
            base_rate = 5000.0
        
        accumulated_cobp = accumulated_cobp_by_stall[stall_ref]
        
        # Select dates based on frequency
        if rent_freq == 'daily':
            transaction_dates = [d for d in daily_dates if d <= TODAY]
        elif rent_freq == 'weekly':
            transaction_dates = [d for d in weekly_dates if d <= TODAY]
        else:
            transaction_dates = [d for d in monthly_dates if d <= TODAY]
        
        # Limit to reasonable number of transactions
        transaction_dates = transaction_dates[:50]  # Max 50 transactions per stall
        
        for trans_date in transaction_dates:
            rand = random.random()
            rent_due = round(base_rate, 2)
            cobp_due = round(accumulated_cobp, 2)
            
            if rand < 0.80:
                status = 'paid'
                amount_paid = rent_due
                cobp_due = 0.0
                if accumulated_cobp > 0 and random.random() < 0.3:
                    cobp_paid = round(random.uniform(0, min(accumulated_cobp, rent_due * 0.5)), 2)
                    accumulated_cobp = max(0, accumulated_cobp - cobp_paid)
                else:
                    cobp_paid = 0.0
                receipt = f'RCP-2024-{str(trans_counter).zfill(4)}'
            elif rand < 0.90:
                status = 'partial'
                amount_paid = round(rent_due * random.uniform(0.3, 0.7), 2)
                unpaid_rent = round(rent_due - amount_paid, 2)
                accumulated_cobp += unpaid_rent
                cobp_due = round(accumulated_cobp, 2)
                cobp_paid = 0.0
                receipt = f'RCP-2024-{str(trans_counter).zfill(4)}'
            elif rand < 0.95:
                status = 'pending'
                amount_paid = 0.0
                accumulated_cobp += rent_due
                cobp_due = round(accumulated_cobp, 2)
                cobp_paid = 0.0
                receipt = ''
            else:
                status = 'cancelled'
                amount_paid = 0.0
                cobp_due = round(accumulated_cobp, 2)
                cobp_paid = 0.0
                receipt = ''
            
            accumulated_cobp_by_stall[stall_ref] = accumulated_cobp
            
            trans_id = f"rent_trans_{stall_ref}_{trans_counter}"
            xml_lines.append(f'        <record id="{trans_id}" model="kst.market.rent.transaction">')
            xml_lines.append(f'            <field name="stall_id" ref="{stall_ref}"/>')
            xml_lines.append(f'            <field name="transaction_date">{trans_date.strftime("%Y-%m-%d")}</field>')
            xml_lines.append(f'            <field name="payment_status">{status}</field>')
            xml_lines.append(f'            <field name="amount_paid">{amount_paid:.2f}</field>')
            xml_lines.append(f'            <field name="cobp_due">{cobp_due:.2f}</field>')
            xml_lines.append(f'            <field name="cobp_paid">{cobp_paid:.2f}</field>')
            if receipt:
                xml_lines.append(f'            <field name="receipt_number">{receipt}</field>')
            xml_lines.append(f'        </record>')
            xml_lines.append('')
            trans_counter += 1
    
    xml_lines.append('    </data>')
    xml_lines.append('</odoo>')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
    
    print(f"\nDemo data generated successfully: {output_file}")
    print(f"Generated {len(df_stalls)} stalls with transaction history")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Extract real stalls and generate demo data')
    parser.add_argument('--db-path', type=str, help='Path to Access database file')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Extracting Real Stall Data from Access Database")
    print("=" * 60)
    
    extracted = extract_stall_data(args.db_path)
    
    if extracted:
        # Change to demo directory
        os.chdir(os.path.dirname(__file__))
        generate_demo_from_real_data(extracted)
        print("\nDone! Demo data generated from real stalls.")
    else:
        print("\nFailed to extract data. Please check database path.")
        print(f"Default path: {DEFAULT_DB_PATH}")

