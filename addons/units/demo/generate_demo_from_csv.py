"""
Convert extracted CSV masterfiles (lessors.csv, lessees.csv) to Odoo XML demo data.
This script reads the CSV files and generates XML records compatible with Odoo.
"""
import pandas as pd
import re
from pathlib import Path


def escape_xml(text):
    """Escape XML special characters."""
    if pd.isna(text) or text is None:
        return ''
    text = str(text)
    # Replace XML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text


def sanitize_xml_id(text):
    """
    Convert text to a valid XML ID.
    XML IDs must start with a letter and contain only letters, digits, underscores, and hyphens.
    Dots are replaced with underscores as Odoo XML parser doesn't accept them.
    """
    if pd.isna(text) or text is None:
        return 'unknown'
    
    # Convert to string and lowercase
    text = str(text).lower().strip()
    
    # Replace spaces and special chars (including dots) with underscores
    # Odoo XML IDs should not contain dots, so we replace them with underscores
    text = re.sub(r'[^a-z0-9_-]', '_', text)
    
    # Remove consecutive underscores
    text = re.sub(r'_+', '_', text)
    
    # Remove leading/trailing underscores
    text = text.strip('_')
    
    # Ensure it starts with a letter or underscore
    if text and not text[0].isalpha() and text[0] != '_':
        text = 'id_' + text
    
    # Limit length
    if len(text) > 50:
        text = text[:50]
    
    # If empty after sanitization, use default
    if not text:
        text = 'unknown'
    
    return text


def generate_lessors_xml(df_lessors):
    """Generate XML records for lessors."""
    xml_lines = []
    
    if df_lessors is None or len(df_lessors) == 0:
        return xml_lines
    
    xml_lines.append('    <!-- Lessors (from extracted CSV) -->')
    
    for idx, row in df_lessors.iterrows():
        lessor_code = str(row['lessor_code']).strip() if 'lessor_code' in row else ''
        lessor_name = str(row['lessor_name']).strip() if 'lessor_name' in row else ''
        
        if not lessor_code and not lessor_name:
            continue
        
        # Create XML ID from code or name
        if lessor_code:
            xml_id = f"lessor_{sanitize_xml_id(lessor_code)}"
        else:
            xml_id = f"lessor_{sanitize_xml_id(lessor_name)}"
        
        # Ensure unique ID by appending index if needed
        if xml_id in [line for line in xml_lines if f'id="{xml_id}"' in line]:
            xml_id = f"{xml_id}_{idx}"
        
        xml_lines.append(f'    <record id="{xml_id}" model="kst.lessor">')
        
        if lessor_code:
            xml_lines.append(f'        <field name="code">{escape_xml(lessor_code)}</field>')
        if lessor_name:
            xml_lines.append(f'        <field name="name">{escape_xml(lessor_name)}</field>')
        
        xml_lines.append('    </record>')
        xml_lines.append('')
    
    return xml_lines


def generate_lessees_xml(df_lessees):
    """Generate XML records for lessees."""
    xml_lines = []
    
    if df_lessees is None or len(df_lessees) == 0:
        return xml_lines
    
    xml_lines.append('    <!-- Lessees (from extracted CSV) -->')
    
    for idx, row in df_lessees.iterrows():
        lessee_name = str(row['lessee_name']).strip() if 'lessee_name' in row else ''
        
        if not lessee_name:
            continue
        
        # Create XML ID from name
        sanitized = sanitize_xml_id(lessee_name)
        xml_id = f"lessee_{sanitized}"
        
        # Ensure unique ID by appending index if needed
        if xml_id in [line for line in xml_lines if f'id="{xml_id}"' in line]:
            xml_id = f"{xml_id}_{idx}"
        
        xml_lines.append(f'    <record id="{xml_id}" model="kst.lessee">')
        xml_lines.append(f'        <field name="name">{escape_xml(lessee_name)}</field>')
        
        # Optional fields (if present in CSV)
        if 'lessee_address' in row and pd.notna(row['lessee_address']):
            address = str(row['lessee_address']).strip()
            if address:
                xml_lines.append(f'        <field name="address">{escape_xml(address)}</field>')
        
        if 'lessee_contact' in row and pd.notna(row['lessee_contact']):
            contact = str(row['lessee_contact']).strip()
            if contact:
                xml_lines.append(f'        <field name="contact">{escape_xml(contact)}</field>')
        
        if 'lessee_email' in row and pd.notna(row['lessee_email']):
            email = str(row['lessee_email']).strip()
            if email:
                xml_lines.append(f'        <field name="email">{escape_xml(email)}</field>')
        
        xml_lines.append('    </record>')
        xml_lines.append('')
    
    return xml_lines


def main():
    """Main function to convert CSV to XML."""
    print("="*80)
    print("CONVERTING CSV MASTERFILES TO ODOO XML DEMO DATA")
    print("="*80)
    
    # Get paths
    demo_dir = Path(__file__).parent
    csv_dir = demo_dir / "master_data_csv"
    
    lessors_csv = csv_dir / "lessors.csv"
    lessees_csv = csv_dir / "lessees.csv"
    output_xml = demo_dir / "masterfiles_demo.xml"
    
    # Check if CSV files exist
    if not lessors_csv.exists():
        print(f"\n✗ Lessors CSV not found: {lessors_csv}")
        return
    
    if not lessees_csv.exists():
        print(f"\n✗ Lessees CSV not found: {lessees_csv}")
        return
    
    # Load CSV files
    print(f"\nLoading CSV files...")
    try:
        df_lessors = pd.read_csv(lessors_csv, encoding='utf-8-sig')
        print(f"✓ Loaded {len(df_lessors)} lessors from {lessors_csv.name}")
    except Exception as e:
        print(f"✗ Error loading lessors CSV: {e}")
        df_lessors = None
    
    try:
        df_lessees = pd.read_csv(lessees_csv, encoding='utf-8-sig')
        print(f"✓ Loaded {len(df_lessees)} lessees from {lessees_csv.name}")
    except Exception as e:
        print(f"✗ Error loading lessees CSV: {e}")
        df_lessees = None
    
    if df_lessors is None and df_lessees is None:
        print("\n✗ No data to convert")
        return
    
    # Generate XML
    print(f"\nGenerating XML demo data...")
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <!-- Masterfiles Demo Data -->',
        '    <!-- Generated from extracted CSV files -->',
        '    <!-- Lessors and Lessees extracted from legacy database -->',
        '',
    ]
    
    # Add lessors
    if df_lessors is not None and len(df_lessors) > 0:
        lessors_xml = generate_lessors_xml(df_lessors)
        xml_lines.extend(lessors_xml)
        print(f"✓ Generated {len(df_lessors)} lessor records")
    
    # Add lessees
    if df_lessees is not None and len(df_lessees) > 0:
        lessees_xml = generate_lessees_xml(df_lessees)
        xml_lines.extend(lessees_xml)
        print(f"✓ Generated {len(df_lessees)} lessee records")
    
    # Close XML
    xml_lines.append('</odoo>')
    
    # Write to file
    xml_content = '\n'.join(xml_lines)
    with open(output_xml, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"\n✓ Generated XML file: {output_xml}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    if df_lessors is not None:
        print(f"  Lessors: {len(df_lessors)} records")
    if df_lessees is not None:
        print(f"  Lessees: {len(df_lessees)} records")
    
    print(f"\nNext steps:")
    print(f"  1. Review the generated XML: {output_xml}")
    print(f"  2. Add it to __manifest__.py 'demo' section if not already included")
    print(f"  3. Or merge it into existing units_demo.xml if preferred")


if __name__ == '__main__':
    main()

