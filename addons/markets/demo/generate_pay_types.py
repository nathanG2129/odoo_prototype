"""
Generate Odoo pay types from fmPayType.csv.
Maps MDB pay types to Odoo kst.market.pay.type format.
"""
import pandas as pd
from pathlib import Path

def map_subgroup(subgroup):
    """Map MDB sub-group to Odoo sub_group."""
    if pd.isna(subgroup) or subgroup == '':
        return 'monthly'
    subgroup = str(subgroup).strip().upper()
    map_dict = {
        'D': 'daily',
        'W': 'weekly',
        'M': 'monthly',
    }
    return map_dict.get(subgroup, 'monthly')

def determine_pay_type_use(code, paytype_name):
    """Determine if pay type is for electricity, water, or both."""
    code = str(code).strip().upper()
    name = str(paytype_name).upper()
    
    # Water-specific codes
    if code in ['NW', 'TL'] or 'NAWASA' in name or 'TOILET' in name:
        return 'water'
    
    # Electricity-specific codes
    if code in ['LG', 'K1MH', 'UGPM', 'UGPW']:
        return 'electricity'
    
    # Can be both
    if code in ['SM', 'MO', 'PT', 'FR']:
        return 'both'
    
    return 'both'  # Default

def generate_pay_types_xml():
    """Generate Odoo XML for pay types."""
    csv_dir = Path(__file__).parent / "master_data_csv"
    paytype_file = csv_dir / "fmPayType.csv"
    
    if not paytype_file.exists():
        print(f"✗ File not found: {paytype_file}")
        return None
    
    df = pd.read_csv(paytype_file, encoding='utf-8-sig')
    print(f"✓ Loaded {len(df)} pay types from {paytype_file}")
    
    xml_lines = [
        '    <!-- Pay Types from fmPayType.csv -->',
        ''
    ]
    
    for idx, row in df.iterrows():
        code = str(row['code']).strip()
        paytype_name = str(row['paytype']).strip()
        subgroup = map_subgroup(row.get('sub-group'))
        pay_type_use = determine_pay_type_use(code, paytype_name)
        
        # Create safe XML ID
        safe_id = f"pay_type_{code.lower()}"
        
        # Generate record
        xml_lines.append(f'    <record id="{safe_id}" model="kst.market.pay.type">')
        xml_lines.append(f'        <field name="code">{code}</field>')
        xml_lines.append(f'        <field name="name">{paytype_name}</field>')
        xml_lines.append(f'        <field name="pay_type_use">{pay_type_use}</field>')
        xml_lines.append(f'        <field name="sub_group">{subgroup}</field>')
        xml_lines.append('    </record>')
        xml_lines.append('')
    
    return '\n'.join(xml_lines)

def get_pay_type_mapping():
    """Get mapping from MDB pay type code to Odoo external ID."""
    return {
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

if __name__ == '__main__':
    print("="*80)
    print("GENERATING PAY TYPES XML")
    print("="*80)
    
    xml_content = generate_pay_types_xml()
    
    if xml_content:
        print("\nGenerated XML:")
        print(xml_content)
        
        # Save to file
        output_file = Path(__file__).parent / "master_data_csv" / "pay_types.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<odoo>\n')
            f.write('    <data noupdate="1">\n')
            f.write(xml_content)
            f.write('    </data>\n')
            f.write('</odoo>\n')
        
        print(f"\n✓ Saved to {output_file}")

