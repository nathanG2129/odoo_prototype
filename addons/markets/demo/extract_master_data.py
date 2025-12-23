"""
Extract master data from Access MDB file and save to CSV.
Focuses on collecting raw data from fmStall and fmStall_Electricity tables.
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

def extract_table_to_csv(conn, table_name, output_file, where_clause=None):
    """
    Extract all data from a table and save to CSV.
    
    Args:
        conn: pyodbc connection
        table_name: Name of the table to extract
        output_file: Path to output CSV file
        where_clause: Optional WHERE clause (without the WHERE keyword)
    """
    try:
        # Build query
        query = f"SELECT * FROM [{table_name}]"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        print(f"\nExtracting from {table_name}...")
        print(f"Query: {query}")
        
        # Read data
        df = pd.read_sql(query, conn)
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✓ Extracted {len(df)} rows to {output_file}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")
        
        return df
        
    except Exception as e:
        print(f"✗ Error extracting {table_name}: {e}")
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
        
        # Extract fmStall table
        print("\n" + "="*60)
        print("EXTRACTING fmStall TABLE")
        print("="*60)
        extract_table_to_csv(
            conn,
            "fmStall",
            output_dir / "fmStall.csv"
        )
        
        # Extract fmStall_Electricity table
        print("\n" + "="*60)
        print("EXTRACTING fmStall_Electricity TABLE")
        print("="*60)
        extract_table_to_csv(
            conn,
            "fmStall_Electricity",
            output_dir / "fmStall_Electricity.csv"
        )
        
        # Close connection
        conn.close()
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"\nAll CSV files saved to: {output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

