"""
Extract Lessees masterfile from Access MDB file and save to CSV.
Lessees are hardcoded in Contracts table (LesseeName and CILesseeShort columns).
This script extracts unique lessee names only (no address/contact/email).
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

def extract_lessees_from_contracts(conn, output_file):
    """
    Extract unique Lessee names from Contracts table.
    Uses LesseeName and CILesseeShort columns, extracts unique names only.
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        # Extract unique lessee names from ContractHeader table
        # Combine LesseeName and CILesseeShort using Access-compatible IIF
        # Use UNION to get both columns and deduplicate in Python
        query = """
            SELECT DISTINCT [LesseeName] AS [Lessee_Name]
            FROM [ContractHeader]
            WHERE [LesseeName] IS NOT NULL 
              AND TRIM([LesseeName]) <> ''
            
            UNION
            
            SELECT DISTINCT [CILesseeShort] AS [Lessee_Name]
            FROM [ContractHeader]
            WHERE [CILesseeShort] IS NOT NULL 
              AND TRIM([CILesseeShort]) <> ''
              AND [LesseeName] IS NULL
        """
        
        print(f"\nExtracting unique Lessee names from ContractHeader table...")
        print(f"Using columns: LesseeName, CILesseeShort")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No lessee names found in ContractHeader table.")
            print("Attempting to inspect ContractHeader table structure...")
            
            # Try to get all columns from ContractHeader table
            try:
                inspect_query = "SELECT TOP 1 * FROM [ContractHeader]"
                sample_df = pd.read_sql(inspect_query, conn)
                print(f"\nAvailable columns in ContractHeader table:")
                for col in sample_df.columns:
                    print(f"  - {col}")
                print("\nPlease check the column names and update the extraction query.")
            except Exception as e:
                print(f"Could not inspect table structure: {e}")
            
            return None
        
        # Standardize column name
        df.columns = ['lessee_name']
        
        # Clean and deduplicate
        # Remove rows with empty lessee names
        df = df[df['lessee_name'].notna() & (df['lessee_name'].str.strip() != '')].copy()
        
        # Remove duplicates based on lessee_name (case-insensitive)
        df['lessee_name_lower'] = df['lessee_name'].str.lower().str.strip()
        df = df.sort_values('lessee_name').drop_duplicates(subset=['lessee_name_lower'], keep='first')
        df = df.drop(columns=['lessee_name_lower'])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ Extracted {len(df)} unique lessee names to {output_file}")
        print(f"  Column: lessee_name")
        
        return df
        
    except Exception as e:
        print(f"✗ Error extracting lessees: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_lessees_from_lessees_table(conn, output_file):
    """
    Extract Lessees from Lessees table if it exists (preferred method).
    Only extracts lessee names.
    
    Args:
        conn: pyodbc connection
        output_file: Path to output CSV file
    """
    try:
        query = """
            SELECT DISTINCT 
                [Lessee_Name] AS [Lessee_Name]
            FROM [Lessees]
            WHERE [Lessee_Name] IS NOT NULL 
              AND TRIM([Lessee_Name]) <> ''
            ORDER BY [Lessee_Name]
        """
        
        print(f"\nExtracting Lessees from Lessees table...")
        print(f"Query: {query}")
        
        df = pd.read_sql(query, conn)
        
        if len(df) == 0:
            print("⚠ No data found in Lessees table.")
            return None
        
        # Standardize column name
        df.columns = ['lessee_name']
        
        # Remove duplicates (case-insensitive)
        df['lessee_name_lower'] = df['lessee_name'].str.lower().str.strip()
        df = df.sort_values('lessee_name').drop_duplicates(subset=['lessee_name_lower'], keep='first')
        df = df.drop(columns=['lessee_name_lower'])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df)} unique lessee names from Lessees table to {output_file}")
        return df
        
    except Exception as e:
        print(f"⚠ Lessees table not found or error: {e}")
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
        
        # Extract Lessees
        print("\n" + "="*60)
        print("EXTRACTING LESSEES MASTERFILE")
        print("="*60)
        print("\nNote: Lessees are hardcoded in ContractHeader table.")
        print("Extracting unique lessee names from LesseeName and CILesseeShort columns.")
        
        output_file = output_dir / "lessees.csv"
        
        # Try Lessees table first (if it exists)
        df = extract_lessees_from_lessees_table(conn, output_file)
        
        # If that fails, extract from Contracts table
        if df is None or len(df) == 0:
            df = extract_lessees_from_contracts(conn, output_file)
        
        if df is not None and len(df) > 0:
            print(f"\n✓ Successfully extracted {len(df)} unique lessee names")
            print(f"  Sample lessees:")
            for idx, row in df.head(10).iterrows():
                name = row['lessee_name']
                print(f"    - {name}")
        else:
            print("\n✗ Could not extract lessees from any source")
            print("Please check the Contracts table structure and column names.")
        
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

