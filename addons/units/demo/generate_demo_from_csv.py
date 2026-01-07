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


def generate_locations_xml(df_locations):
    """Generate XML records for locations."""
    xml_lines = []
    
    if df_locations is None or len(df_locations) == 0:
        return xml_lines
    
    xml_lines.append('    <!-- Locations (from extracted CSV) -->')
    
    for idx, row in df_locations.iterrows():
        # Handle NaN/null values properly
        location_code_raw = row.get("location_code")
        if pd.isna(location_code_raw):
            continue
        
        location_code = str(location_code_raw).strip()
        if not location_code or location_code.lower() == 'nan':
            continue
        
        # Use location_code as XML ID (numeric, e.g., "01", "02")
        # Pad with leading zero if needed to ensure 2-digit format
        # Prefix with "loc" to avoid conflict with category IDs
        try:
            location_code_int = int(float(location_code))
            location_code_padded = f"{location_code_int:02d}"
            location_xml_id = f"loc{location_code_padded}"  # e.g., "loc01", "loc02"
        except (ValueError, TypeError):
            # If not numeric, skip
            continue
        
        description_raw = row.get("description")
        description = str(description_raw).strip() if pd.notna(description_raw) else ""
        if description.lower() == 'nan':
            description = ""
        
        company_name_raw = row.get("company_name")
        company_name = str(company_name_raw).strip() if pd.notna(company_name_raw) else ""
        if company_name.lower() == 'nan':
            company_name = ""
        
        company_code_raw = row.get("company_code")
        company_code = str(company_code_raw).strip() if pd.notna(company_code_raw) else ""
        if company_code.lower() == 'nan':
            company_code = ""
        
        company_address_raw = row.get("company_address")
        company_address = str(company_address_raw).strip() if pd.notna(company_address_raw) else ""
        if company_address.lower() == 'nan':
            company_address = ""
        
        xml_lines.append(f'    <record id="{location_xml_id}" model="kst.location">')
        xml_lines.append(f'        <field name="code">{escape_xml(location_code_padded)}</field>')
        
        if description:
            xml_lines.append(f'        <field name="description">{escape_xml(description)}</field>')
        if company_name:
            xml_lines.append(f'        <field name="company_name">{escape_xml(company_name)}</field>')
        if company_code:
            xml_lines.append(f'        <field name="company_code">{escape_xml(company_code)}</field>')
        if company_address:
            xml_lines.append(f'        <field name="company_address">{escape_xml(company_address)}</field>')
        
        xml_lines.append('    </record>')
        xml_lines.append('')
    
    return xml_lines


def generate_units_xml(df_units):
    """Generate XML records for units."""
    xml_lines = []
    if df_units is None or len(df_units) == 0:
        return xml_lines

    xml_lines.append('    <!-- Units (from extracted CSV) -->')

    existing_ids = set()

    for idx, row in df_units.iterrows():
        # Handle NaN/null values properly - check before converting to string
        lessor_code_raw = row.get("lessor_code")
        if pd.isna(lessor_code_raw):
            continue  # Skip rows with missing lessor_code
        lessor_code = str(lessor_code_raw).strip()
        if not lessor_code or lessor_code.lower() == 'nan':
            continue  # Skip empty or "nan" string values
        
        unit_code_raw = row.get("unit_code")
        unit_code = str(unit_code_raw).strip() if pd.notna(unit_code_raw) else ""
        if unit_code.lower() == 'nan':
            unit_code = ""
        
        unit_specified_raw = row.get("unit_specified")
        unit_specified = str(unit_specified_raw).strip() if pd.notna(unit_specified_raw) else ""
        if unit_specified.lower() == 'nan':
            unit_specified = ""
        
        address_raw = row.get("address")
        address = str(address_raw).strip() if pd.notna(address_raw) else ""
        if address.lower() == 'nan':
            address = ""
        
        description_raw = row.get("description")
        description = str(description_raw).strip() if pd.notna(description_raw) else ""
        if description.lower() == 'nan':
            description = ""
        
        size = row.get("size", 0) if pd.notna(row.get("size", 0)) else 0
        
        soa_bank_raw = row.get("soa_bank_account_number")
        soa_bank = str(soa_bank_raw).strip() if pd.notna(soa_bank_raw) else ""
        if soa_bank.lower() == 'nan':
            soa_bank = ""

        # Lessor is required in the Odoo model; skip if missing
        if not lessor_code:
            continue

        # Get category_code for category reference
        category_code_raw = row.get("category_code")
        category_code = None
        if pd.notna(category_code_raw):
            try:
                # Handle both string and numeric values (pandas may read "04" as float 4.0)
                # Convert to float first (handles both "4" and 4.0), then to int to remove decimal
                category_code_float = float(category_code_raw)
                category_code_int = int(category_code_float)
                # Convert to zero-padded 2-digit string (e.g., 4 -> "04", 10 -> "10")
                category_code = f"{category_code_int:02d}"
            except (ValueError, TypeError):
                # If conversion fails, skip category reference
                category_code = None
        
        # Get location_code for location reference
        location_code_raw = row.get("location_code")
        location_code = None
        if pd.notna(location_code_raw):
            try:
                # Handle both string and numeric values (pandas may read "10" as float 10.0)
                # Convert to float first, then to int to remove decimal
                location_code_float = float(location_code_raw)
                location_code_int = int(location_code_float)
                # Convert to zero-padded 2-digit string (e.g., 10 -> "10", 5 -> "05")
                location_code = f"{location_code_int:02d}"
            except (ValueError, TypeError):
                # If conversion fails, skip location reference
                location_code = None

        # Determine a usable unit identifier
        base_id_source = unit_code or unit_specified
        if not base_id_source:
            base_id_source = f"unit_{idx}"

        xml_id = f"unit_{sanitize_xml_id(base_id_source)}"
        if xml_id in existing_ids:
            xml_id = f"{xml_id}_{idx}"
        existing_ids.add(xml_id)

        xml_lines.append(f'    <record id="{xml_id}" model="kst.unit">')

        # Lessor reference (required)
        lessor_xml_id = f"lessor_{sanitize_xml_id(lessor_code)}"
        xml_lines.append(f'        <field name="lessor_id" ref="{lessor_xml_id}"/>')

        # Category reference (optional, if category_code exists)
        if category_code:
            # Use numeric ID directly (e.g., "01", "02") matching the CSV format
            xml_lines.append(f'        <field name="category_id" ref="{category_code}"/>')
        
        # Location reference (optional, if location_code exists)
        if location_code:
            # Use prefixed ID (e.g., "loc01", "loc02") to avoid conflict with category IDs
            location_xml_id = f"loc{location_code}"
            xml_lines.append(f'        <field name="location_id" ref="{location_xml_id}"/>')

        if unit_specified:
            xml_lines.append(f'        <field name="unit_specified">{escape_xml(unit_specified)}</field>')
        elif unit_code:
            xml_lines.append(f'        <field name="unit_specified">{escape_xml(unit_code)}</field>')

        if address:
            xml_lines.append(f'        <field name="address">{escape_xml(address)}</field>')
        if description:
            xml_lines.append(f'        <field name="description">{escape_xml(description)}</field>')
        try:
            size_val = float(size)
            if size_val:
                xml_lines.append(f'        <field name="size">{size_val:.2f}</field>')
        except Exception:
            pass
        if soa_bank:
            xml_lines.append(f'        <field name="soa_bank_account_number">{escape_xml(soa_bank)}</field>')

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
    locations_csv = csv_dir / "locations.csv"
    units_csv = csv_dir / "units.csv"
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

    try:
        df_locations = pd.read_csv(locations_csv, encoding='utf-8-sig') if locations_csv.exists() else None
        if df_locations is not None:
            print(f"✓ Loaded {len(df_locations)} locations from {locations_csv.name}")
    except Exception as e:
        print(f"⚠ Error loading locations CSV: {e}")
        df_locations = None
    
    try:
        df_units = pd.read_csv(units_csv, encoding='utf-8-sig')
        print(f"✓ Loaded {len(df_units)} units from {units_csv.name}")
    except Exception as e:
        print(f"✗ Error loading units CSV: {e}")
        df_units = None
    
    if df_lessors is None and df_lessees is None and df_locations is None and df_units is None:
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
    
    # Add locations (before units so units can reference them)
    if df_locations is not None and len(df_locations) > 0:
        locations_xml = generate_locations_xml(df_locations)
        xml_lines.extend(locations_xml)
        print(f"✓ Generated {len(df_locations)} location records")

    # Add units (must come after locations and categories for references to work)
    if df_units is not None and len(df_units) > 0:
        units_xml = generate_units_xml(df_units)
        xml_lines.extend(units_xml)
        print(f"✓ Generated {len(units_xml)//3} unit records")  # rough count based on record/blank lines
    
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
    if df_locations is not None:
        print(f"  Locations: {len(df_locations)} records")
    if df_units is not None:
        print(f"  Units: {len(df_units)} records")
    if df_locations is not None:
        print(f"  Locations: {len(df_locations)} records")
    if df_units is not None:
        print(f"  Units: {len(df_units)} records")
    if df_units is not None:
        print(f"  Units: {len(df_units)} records")
    
    print(f"\nNext steps:")
    print(f"  1. Review the generated XML: {output_xml}")
    print(f"  2. Add it to __manifest__.py 'demo' section if not already included")
    print(f"  3. Or merge it into existing units_demo.xml if preferred")


if __name__ == '__main__':
    main()

