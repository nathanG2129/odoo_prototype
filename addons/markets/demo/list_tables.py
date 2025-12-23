"""
List all tables in the MDB database to find the correct table name for daily collections.
"""
import pyodbc
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
try:
    from kst_statistics.config import get_connection_string, DEFAULT_DB_PATH
except ImportError:
    DEFAULT_DB_PATH = r"C:\KST_DB.mdb"
    def get_connection_string(db_path=None):
        path = db_path or DEFAULT_DB_PATH
        return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

def list_tables(conn):
    """List all tables in the database."""
    cursor = conn.cursor()
    
    # Get all table names
    tables = []
    for table_info in cursor.tables(tableType='TABLE'):
        table_name = table_info.table_name
        if not table_name.startswith('MSys'):  # Skip system tables
            tables.append(table_name)
    
    return sorted(tables)

def search_table_by_columns(conn, required_columns):
    """Search for tables that contain specific columns."""
    cursor = conn.cursor()
    matching_tables = []
    
    all_tables = list_tables(conn)
    
    for table_name in all_tables:
        try:
            # Get columns for this table
            columns = []
            for col_info in cursor.columns(table=table_name):
                columns.append(col_info.column_name)
            
            # Check if all required columns exist
            if all(col in columns for col in required_columns):
                matching_tables.append((table_name, columns))
        except Exception as e:
            # Skip if we can't read the table
            pass
    
    return matching_tables

def main():
    """Main function."""
    db_path = os.environ.get('KST_DB_PATH') or DEFAULT_DB_PATH
    
    if not os.path.exists(db_path):
        print(f"\n✗ Database file not found: {db_path}")
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
    
    conn_str = get_connection_string(db_path)
    print(f"\nConnecting to database: {db_path}")
    
    try:
        conn = pyodbc.connect(conn_str)
        print("✓ Connected successfully!")
        
        # List all tables
        print("\n" + "="*80)
        print("ALL TABLES IN DATABASE")
        print("="*80)
        tables = list_tables(conn)
        print(f"\nFound {len(tables)} tables:\n")
        for i, table in enumerate(tables, 1):
            print(f"  {i:3d}. {table}")
        
        # Search for tables with StallNo, TransType, WaterPaymentType
        print("\n" + "="*80)
        print("SEARCHING FOR TABLES WITH: StallNo, TransType, WaterPaymentType")
        print("="*80)
        required_cols = ['StallNo', 'TransType', 'WaterPaymentType']
        matching = search_table_by_columns(conn, required_cols)
        
        if matching:
            print(f"\n✓ Found {len(matching)} matching table(s):\n")
            for table_name, columns in matching:
                print(f"  Table: {table_name}")
                print(f"  Columns: {', '.join(columns)}")
                print()
        else:
            print("\n✗ No tables found with all required columns")
            print("\nSearching for tables with partial matches...")
            
            # Try with just StallNo and WaterPaymentType
            partial_cols = ['StallNo', 'WaterPaymentType']
            partial_matching = search_table_by_columns(conn, partial_cols)
            if partial_matching:
                print(f"\nFound {len(partial_matching)} table(s) with StallNo and WaterPaymentType:")
                for table_name, columns in partial_matching:
                    print(f"  {table_name}: {', '.join(columns)}")
            
            # Try with just StallNo and TransType
            partial_cols2 = ['StallNo', 'TransType']
            partial_matching2 = search_table_by_columns(conn, partial_cols2)
            if partial_matching2:
                print(f"\nFound {len(partial_matching2)} table(s) with StallNo and TransType:")
                for table_name, columns in partial_matching2:
                    print(f"  {table_name}: {', '.join(columns)}")
        
        # Also check fmStall_Electricity for these columns
        print("\n" + "="*80)
        print("CHECKING fmStall_Electricity FOR PAY TYPE COLUMNS")
        print("="*80)
        try:
            cursor = conn.cursor()
            columns = []
            for col_info in cursor.columns(table='fmStall_Electricity'):
                columns.append(col_info.column_name)
            print(f"\nfmStall_Electricity columns: {', '.join(columns)}")
            
            if 'WaterPaymentType' in columns:
                print("✓ fmStall_Electricity has WaterPaymentType column!")
            if 'ElectricPaymentType' in columns:
                print("✓ fmStall_Electricity has ElectricPaymentType column!")
        except Exception as e:
            print(f"✗ Error checking fmStall_Electricity: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

