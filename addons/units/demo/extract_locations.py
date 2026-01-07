"""
Extract Locations masterfile from Access MDB file and save to CSV.
Locations are stored in the fmLocation table.
"""
import pyodbc
import pandas as pd
import os
import sys
from pathlib import Path

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

def extract_locations_from_table(conn, output_file):
    """
    Extract Locations from the fmLocation table.
    Table structure: LocCode, Location, CompanyName, CompanyShortCode, CompanyAddress
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        # Extract from fmLocation table
        query = """
            SELECT DISTINCT 
                [LocCode] AS [Location_Code],
                [Location] AS [Location_Description],
                [CompanyName] AS [Company_Name],
                [CompanyShortCode] AS [Company_Code],
                [CompanyAddress] AS [Company_Address]
            FROM [fmLocation]
            WHERE [LocCode] IS NOT NULL
            ORDER BY [LocCode]
        """
        
        print(f"\nExtracting Locations from fmLocation table...")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No data found in fmLocation table.")
            return None
        
        # Standardize column names (map to Odoo model fields)
        df.columns = ['location_code', 'description', 'company_name', 'company_code', 'company_address']
        
        # Fill missing values with empty strings
        df = df.fillna('')
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df)} locations to {output_file}")
        return df
        
    except Exception as e:
        print(f"✗ Error extracting locations: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main extraction function."""
    # Get database path
    db_path = os.environ.get('KST_DB_PATH') or DEFAULT_DB_PATH
    
    if not os.path.exists(db_path):
        print(f"\n✗ Database file not found: {db_path}")
        print("Please set KST_DB_PATH environment variable or update DEFAULT_DB_PATH")
        print("\nTrying common locations...")
        
        possible_paths = [
            r"C:\KST_DB.mdb",
            r"C:\Users\kst11\Desktop\TEST\up-to-nov27\KST_DB.mdb",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                print(f"✓ Found database at: {db_path}")
                break
        else:
            print("\nPlease provide the database path:")
            db_path = input("Enter path to KST_DB.mdb: ").strip().strip('"')
            if not os.path.exists(db_path):
                print(f"✗ File still not found: {db_path}")
                return
    
    # Connect to database
    conn_str = get_connection_string(db_path)
    print(f"\nConnecting to database: {db_path}")
    
    try:
        conn = pyodbc.connect(conn_str)
        print("✓ Connected successfully!")
        
        # Create output directory
        output_dir = Path(__file__).parent / "master_data_csv"
        output_dir.mkdir(exist_ok=True)
        print(f"\nOutput directory: {output_dir}")
        
        # Extract Locations
        print("\n" + "="*60)
        print("EXTRACTING LOCATIONS MASTERFILE")
        print("="*60)
        print("Source: fmLocation table")
        
        output_file = output_dir / "locations.csv"
        
        df = extract_locations_from_table(conn, output_file)
        
        if df is not None and len(df) > 0:
            print(f"\n✓ Successfully extracted {len(df)} locations")
            print(f"  Sample locations:")
            for idx, row in df.head(5).iterrows():
                code = row['location_code']
                desc = row['description'] or row['company_name'] or 'N/A'
                print(f"    - [{code}] {desc}")
        else:
            print("\n✗ Could not extract locations")
        
        # Close connection
        conn.close()
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"\nCSV file saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

