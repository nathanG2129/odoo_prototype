"""
Script to generate comprehensive demo data for KST Markets module.
Generates 30 active stalls with 7 months of transaction history.
Updated for v2.0.0: No stall groups, uses utility accounts, new field names.
"""
from datetime import datetime, timedelta
import random

# Configuration
NUM_STALLS = 30
MONTHS_HISTORY = 7
TODAY = datetime.now()

# Market codes
MARKETS = [
    ('BBH', 'Bacolod Public Market', 'Bacolod City, Negros Occidental'),
    ('KTC', 'Kabankalan Town Center', 'Kabankalan City, Negros Occidental'),
    ('STM', 'Silay City Market', 'Silay City, Negros Occidental'),
]

# Pay Types
PAY_TYPES = [
    ('K1-MH', 'K1 Monthly', 'electricity', 'monthly'),
    ('UGS Weekly', 'UGS Weekly', 'electricity', 'weekly'),
    ('LG Daily', 'LG Daily', 'electricity', 'daily'),
    ('NAWASA', 'NAWASA Monthly', 'water', 'monthly'),
    ('Water Weekly', 'Water Weekly', 'water', 'weekly'),
]

# Utility Accounts (from kst_base - these should exist)
UTILITY_ACCOUNTS = [
    ('kst_base.utility_account_meralco_001', 'electricity'),
    ('kst_base.utility_account_meralco_002', 'electricity'),
    ('kst_base.utility_account_water_001', 'water'),
    ('kst_base.utility_account_water_002', 'water'),
]

# Generate tenant names
TENANT_NAMES = [
    'Juan Dela Cruz', 'Maria Santos', 'Pedro Reyes', 'Ana Garcia',
    'Roberto Tan', 'Carmen Villanueva', 'Jose Mendoza', 'Lourdes Fernandez',
    'Antonio Cruz', 'Rosa Martinez', 'Carlos Ramos', 'Elena Torres',
    'Fernando Lopez', 'Isabel Gutierrez', 'Miguel Rodriguez', 'Patricia Diaz',
    'Ricardo Morales', 'Sofia Herrera', 'Victor Jimenez', 'Teresa Navarro',
]

def generate_stall_code(market_code, index):
    """Generate stall codes like A-1, A-2, B-1, etc."""
    section = chr(65 + (index // 10))  # A, B, C, etc.
    number = (index % 10) + 1
    return f"{section}-{number}"

def generate_date_string(dt):
    """Convert datetime to YYYY-MM-DD string"""
    return dt.strftime('%Y-%m-%d')

def generate_monthly_dates(start_date, months):
    """Generate list of dates, one per month"""
    dates = []
    for i in range(months):
        # First day of each month
        date = start_date.replace(day=1) - timedelta(days=32 * i)
        date = date.replace(day=1)
        dates.append(date)
    return sorted(dates)

def generate_daily_dates(start_date, months):
    """Generate list of dates for daily billing (weekdays only, ~22 days per month)"""
    dates = []
    current = start_date.replace(day=1) - timedelta(days=32 * (months - 1))
    current = current.replace(day=1)
    end_date = start_date
    
    while current <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:  # Monday to Friday
            dates.append(current)
        current += timedelta(days=1)
    
    return sorted(dates)

def generate_weekly_dates(start_date, months):
    """Generate list of dates for weekly billing (~4 per month)"""
    dates = []
    current = start_date.replace(day=1) - timedelta(days=32 * (months - 1))
    current = current.replace(day=1)
    end_date = start_date
    
    # Start on a Monday
    while current.weekday() != 0:  # 0 = Monday
        current += timedelta(days=1)
    
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=7)  # Next week
    
    return sorted(dates)

def generate_xml():
    """Generate the complete XML demo data"""
    
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        '',
        '        <!-- Market Pay Types -->',
    ]
    
    # Pay Types
    pay_type_refs = {}
    for i, (code, name, use, subgroup) in enumerate(PAY_TYPES):
        ref_id = f"pay_type_{code.lower().replace(' ', '_').replace('-', '_')}"
        pay_type_refs[code] = ref_id
        xml_lines.append(f'        <record id="{ref_id}" model="kst.market.pay.type">')
        xml_lines.append(f'            <field name="code">{code}</field>')
        xml_lines.append(f'            <field name="name">{name}</field>')
        xml_lines.append(f'            <field name="pay_type_use">{use}</field>')
        xml_lines.append(f'            <field name="sub_group">{subgroup}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Markets
    xml_lines.append('        <!-- Markets -->')
    market_refs = {}
    for i, (code, name, address) in enumerate(MARKETS):
        ref_id = f"market_{code.lower()}"
        market_refs[code] = ref_id
        xml_lines.append(f'        <record id="{ref_id}" model="kst.market">')
        xml_lines.append(f'            <field name="code">{code}</field>')
        xml_lines.append(f'            <field name="name">{name}</field>')
        xml_lines.append(f'            <field name="address">{address}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Tenants
    xml_lines.append('        <!-- Tenants -->')
    tenant_refs = {}
    for i, name in enumerate(TENANT_NAMES):
        ref_id = f"tenant_{i+1}"
        tenant_refs[i] = ref_id
        start_date = TODAY - timedelta(days=random.randint(90, 730))
        xml_lines.append(f'        <record id="{ref_id}" model="kst.tenant">')
        xml_lines.append(f'            <field name="name">{name}</field>')
        xml_lines.append(f'            <field name="date_started">{generate_date_string(start_date)}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    # Utility Bills (sample bills for demo)
    xml_lines.append('        <!-- Utility Bills -->')
    utility_bill_refs = []
    monthly_dates = generate_monthly_dates(TODAY, MONTHS_HISTORY)
    electricity_accounts = []  # Track which accounts have bills
    for i, (account_ref, utility_type) in enumerate(UTILITY_ACCOUNTS):
        if utility_type == 'electricity':
            electricity_accounts.append(account_ref)
            # Generate one bill per month for electricity accounts
            for j, bill_date in enumerate(monthly_dates[:3]):  # Last 3 months
                bill_id = f"utility_bill_{account_ref.split('.')[-1]}_{j+1}"
                period_from = bill_date - timedelta(days=30)
                period_to = bill_date
                # Store: (bill_id, account_ref, bill_date, utility_type, period_from, period_to)
                utility_bill_refs.append((bill_id, account_ref, bill_date, utility_type, period_from, period_to))
                xml_lines.append(f'        <record id="{bill_id}" model="kst.utility.bill">')
                xml_lines.append(f'            <field name="utility_account_id" ref="{account_ref}"/>')
                xml_lines.append(f'            <field name="bill_date">{generate_date_string(bill_date)}</field>')
                xml_lines.append(f'            <field name="due_date">{generate_date_string(bill_date + timedelta(days=20))}</field>')
                xml_lines.append(f'            <field name="period_covered_from">{generate_date_string(period_from)}</field>')
                xml_lines.append(f'            <field name="period_covered_to">{generate_date_string(period_to)}</field>')
                xml_lines.append(f'            <field name="total_consumption">{random.randint(10000, 20000)}.00</field>')
                xml_lines.append(f'            <field name="total_bill_amount">{random.randint(120000, 240000)}.00</field>')
                xml_lines.append(f'        </record>')
                xml_lines.append('')
    
    # Stalls
    xml_lines.append('        <!-- Stalls -->')
    stall_refs = []
    
    # Distribute stalls across utility accounts that have bills
    # Target: 4-7 stalls per account (most common), with some outliers at 10-11
    # Create a distribution plan for stalls per account
    account_stall_distribution = {}
    if electricity_accounts:
        if len(electricity_accounts) == 2:
            # Distribute: Account 1 gets 5 stalls, Account 2 gets 6 stalls (typical)
            # Or Account 1 gets 10 stalls (outlier), Account 2 gets 5 stalls
            if random.random() < 0.2:  # 20% chance of outlier
                account_stall_distribution[electricity_accounts[0]] = 10  # Outlier
                account_stall_distribution[electricity_accounts[1]] = 5
            else:
                account_stall_distribution[electricity_accounts[0]] = random.randint(4, 7)
                account_stall_distribution[electricity_accounts[1]] = random.randint(4, 7)
        else:
            # For other cases, distribute evenly with 4-7 stalls per account
            stalls_per_account = random.randint(4, 7)
            for account in electricity_accounts:
                account_stall_distribution[account] = stalls_per_account
    
    # Track how many stalls assigned to each account
    account_stall_count = {account: 0 for account in electricity_accounts}
    
    for i in range(NUM_STALLS):
        market_code = MARKETS[i % len(MARKETS)][0]
        market_ref = market_refs[market_code]
        stall_code = generate_stall_code(market_code, i)
        ref_id = f"stall_{market_code.lower()}_{stall_code.lower().replace('-', '_')}"
        stall_refs.append(ref_id)
        
        tenant_idx = i % len(TENANT_NAMES)
        tenant_ref = tenant_refs[tenant_idx]
        
        # Assign utility account based on distribution plan
        utility_account_ref = None
        if electricity_accounts and account_stall_distribution:
            # Find an account that hasn't reached its target yet
            for account in electricity_accounts:
                if account_stall_count[account] < account_stall_distribution.get(account, 0):
                    utility_account_ref = account
                    account_stall_count[account] += 1
                    break
        
        # Determine rent collection frequency (30% daily, 30% weekly, 40% monthly)
        rent_freq_rand = random.random()
        if rent_freq_rand < 0.3:
            rent_collection_type = 'daily'
        elif rent_freq_rand < 0.6:
            rent_collection_type = 'weekly'
        else:
            rent_collection_type = 'monthly'
        
        # Determine pay types (random selection)
        elec_choice = random.choice(['LG Daily', 'UGS Weekly', 'K1-MH'])
        elec_pay_type = pay_type_refs[elec_choice]
        if elec_choice == 'LG Daily':
            elec_freq = 'daily'
        elif elec_choice == 'UGS Weekly':
            elec_freq = 'weekly'
        else:
            elec_freq = 'monthly'
        
        water_choice = random.choice(['NAWASA', 'Water Weekly'])
        water_pay_type = pay_type_refs[water_choice]
        if water_choice == 'NAWASA':
            water_freq = 'monthly'
        else:
            water_freq = 'weekly'
        
        # Calculate rental rate based on frequency
        monthly_rent = random.randint(3000, 8000)
        if rent_collection_type == 'daily':
            rental_rate = round(monthly_rent / 22, 2)  # ~22 working days per month
        elif rent_collection_type == 'weekly':
            rental_rate = round(monthly_rent / 4, 2)  # ~4 weeks per month
        else:  # monthly
            rental_rate = monthly_rent
        
        default_electricity_rate = round(random.uniform(12.0, 22.0), 2)
        default_water_rate = round(random.uniform(8.0, 15.0), 2)
        
        xml_lines.append(f'        <record id="{ref_id}" model="kst.stall">')
        xml_lines.append(f'            <field name="market_id" ref="{market_ref}"/>')
        xml_lines.append(f'            <field name="code">{stall_code}</field>')
        xml_lines.append(f'            <field name="tenant_id" ref="{tenant_ref}"/>')
        if utility_account_ref:
            xml_lines.append(f'            <field name="utility_account_id" ref="{utility_account_ref}"/>')
        xml_lines.append(f'            <field name="rental_rate">{rental_rate:.2f}</field>')
        xml_lines.append(f'            <field name="default_electricity_rate">{default_electricity_rate:.2f}</field>')
        xml_lines.append(f'            <field name="default_water_rate">{default_water_rate:.2f}</field>')
        xml_lines.append(f'            <field name="electric_pay_type_id" ref="{elec_pay_type}"/>')
        xml_lines.append(f'            <field name="water_pay_type_id" ref="{water_pay_type}"/>')
        xml_lines.append(f'            <field name="rent_collection_type">{rent_collection_type}</field>')
        xml_lines.append(f'            <field name="is_active">True</field>')
        xml_lines.append(f'            <field name="need_or">{str(random.choice([True, False])).lower()}</field>')
        xml_lines.append(f'            <field name="meralco_account_number">{random.randint(1000000000, 9999999999)}</field>')
        xml_lines.append(f'            <field name="electricity_sub_meter_number">SM-{str(i+1).zfill(3)}</field>')
        xml_lines.append(f'        </record>')
        xml_lines.append('')
    
    xml_lines.append('    </data>')
    xml_lines.append('</odoo>')
    
    return '\n'.join(xml_lines)

if __name__ == '__main__':
    xml_content = generate_xml()
    output_file = 'kst_markets_demo.xml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"Demo data generated successfully: {output_file}")
    print(f"Generated {NUM_STALLS} stalls (masterfiles only, no transaction data)")
