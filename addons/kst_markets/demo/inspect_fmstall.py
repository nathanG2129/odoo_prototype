"""
Inspect fmStall table structure to get actual column names.
"""
import pyodbc
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
try:
    from kst_statistics.config import get_connection_string, DEFAULT_DB_PATH
except ImportError:
    DEFAULT_DB_PATH = r"C:\KST_DB.mdb"
    def get_connection_string(db_path=None):
        path = db_path or DEFAULT_DB_PATH
        return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

def inspect_table(conn, table_name):
    """Inspect table structure using Access system tables."""
    try:
        # Method 1: Try to get column info from MSysObjects
        cursor = conn.cursor()
        
        # Get column names by trying to select * (limited)
        print(f"\nAttempting to get column info for {table_name}...")
        try:
            cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
            columns = [column[0] for column in cursor.description]
            print(f"\nFound {len(columns)} columns:")
            for col in columns:
                print(f"  - {col}")
            return columns
        except Exception as e:
            print(f"Error with SELECT *: {e}")
        
        # Method 2: Try to query system tables (may not work in all Access versions)
        try:
            query = f"""
                SELECT Name 
                FROM MSysObjects 
                WHERE Type=1 AND Flags=0 AND Name='{table_name}'
            """
            cursor.execute(query)
            print("Table exists in MSysObjects")
        except:
            print("Cannot access MSysObjects (may require admin privileges)")
        
        return None
        
    except Exception as e:
        print(f"Error inspecting table: {e}")
        return None

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Inspect fmStall table structure')
    parser.add_argument('--db-path', type=str, help='Path to Access database file')
    args = parser.parse_args()
    
    db_path = args.db_path
    if not db_path:
        # Try common locations
        possible_paths = [
            r"C:\KST_DB.mdb",
            r"C:\Users\kst11\Desktop\TEST\up-to-nov27\KST_DB.mdb",
            r"C:\Users\kst11\Desktop\TEST\11-28-2025\Temp_Copy.mdb",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
    
    if not db_path or not os.path.exists(db_path):
        print(f"Database not found. Please provide path:")
        db_path = input("Enter path to KST_DB.mdb: ").strip().strip('"')
    
    if db_path and os.path.exists(db_path):
        print(f"Connecting to: {db_path}")
        conn_str = get_connection_string(db_path)
        try:
            conn = pyodbc.connect(conn_str)
            print("Connected successfully!")
            
            columns = inspect_table(conn, 'fmStall')
            
            if columns:
                print("\n" + "="*60)
                print("Sample query with correct column names:")
                print("="*60)
                print(f"SELECT TOP 5")
                for col in columns[:10]:  # Show first 10
                    print(f"    [{col}],")
                print(f"    ...")
                print(f"FROM [fmStall]")
                print(f"WHERE [isActive] = True")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Database file not found: {db_path}")

