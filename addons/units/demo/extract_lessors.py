"""
Extract Lessors masterfile from Access MDB file and save to CSV.
Lessors are typically stored in a dedicated Lessors table with Lessor_Code and Lessor_Name.
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

def extract_lessors_from_table(conn, output_file):
    """
    Extract Lessors from the fmLessor table.
    Table structure: LessorCode, Lessor (name), SMCTitle
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        # Extract from fmLessor table (actual table name in Access)
        query = """
            SELECT DISTINCT 
                [LessorCode] AS [Lessor_Code],
                [Lessor] AS [Lessor_Name],
                [SMCTitle]
            FROM [fmLessor]
            WHERE [LessorCode] IS NOT NULL 
              AND [Lessor] IS NOT NULL
            ORDER BY [LessorCode]
        """
        
        print(f"\nExtracting Lessors from fmLessor table...")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No data found in fmLessor table. Trying alternative sources...")
            return None
        
        # Standardize column names (map to Odoo model fields)
        # Note: SMCTitle is kept for reference but not used in Odoo model
        df.columns = ['lessor_code', 'lessor_name', 'smc_title']
        
        # Keep only fields needed for Odoo model (code and name)
        df_output = df[['lessor_code', 'lessor_name']].copy()
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_output.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df_output)} lessors to {output_file}")
        print(f"  Note: SMCTitle field is available but not imported to Odoo model")
        return df_output
        
    except Exception as e:
        print(f"⚠ Error extracting from Lessors table: {e}")
        return None

def extract_lessors_from_units(conn, output_file):
    """
    Extract unique Lessors from Units table (fallback if Lessors table doesn't exist).
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        # Extract unique lessors from Units table
        query = """
            SELECT DISTINCT 
                u.[Lessor_ID],
                u.[Lessor_Code],
                u.[Lessor_Name]
            FROM [Units] u
            WHERE u.[Lessor_Code] IS NOT NULL 
              AND u.[Lessor_Name] IS NOT NULL
            ORDER BY u.[Lessor_Code]
        """
        
        print(f"\nExtracting Lessors from Units table...")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No lessor data found in Units table.")
            return None
        
        # Standardize column names
        df.columns = ['lessor_id', 'lessor_code', 'lessor_name']
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df)} unique lessors from Units to {output_file}")
        return df
        
    except Exception as e:
        print(f"⚠ Error extracting from Units table: {e}")
        return None

def extract_lessors_from_contracts(conn, output_file):
    """
    Extract unique Lessors from Contracts table (fallback).
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        # Extract unique lessors from Contracts table
        query = """
            SELECT DISTINCT 
                c.[Lessor_ID],
                c.[Lessor_Code],
                c.[Lessor_Name]
            FROM [Contracts] c
            WHERE c.[Lessor_Code] IS NOT NULL 
              AND c.[Lessor_Name] IS NOT NULL
            ORDER BY c.[Lessor_Code]
        """
        
        print(f"\nExtracting Lessors from Contracts table...")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No lessor data found in Contracts table.")
            return None
        
        # Standardize column names
        df.columns = ['lessor_id', 'lessor_code', 'lessor_name']
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df)} unique lessors from Contracts to {output_file}")
        return df
        
    except Exception as e:
        print(f"⚠ Error extracting from Contracts table: {e}")
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
        
        # Extract Lessors - try multiple sources
        print("\n" + "="*60)
        print("EXTRACTING LESSORS MASTERFILE")
        print("="*60)
        print("Source: fmLessor table (LessorCode, Lessor, SMCTitle)")
        
        output_file = output_dir / "lessors.csv"
        
        # Try fmLessor table first (primary source)
        df = extract_lessors_from_table(conn, output_file)
        
        # If that fails, try Units table (fallback)
        if df is None or len(df) == 0:
            print("\n⚠ fmLessor table extraction failed, trying Units table...")
            df = extract_lessors_from_units(conn, output_file)
        
        # If that fails, try Contracts table (fallback)
        if df is None or len(df) == 0:
            print("\n⚠ Units table extraction failed, trying Contracts table...")
            df = extract_lessors_from_contracts(conn, output_file)
        
        if df is not None and len(df) > 0:
            print(f"\n✓ Successfully extracted {len(df)} lessors")
            print(f"  Sample lessors:")
            for idx, row in df.head(5).iterrows():
                print(f"    - [{row['lessor_code']}] {row['lessor_name']}")
        else:
            print("\n✗ Could not extract lessors from any source")
        
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

