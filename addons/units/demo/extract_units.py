"""
Extract Units masterfile from Access MDB file (fmUnits) and save to CSV.
Maps legacy columns to the Odoo Units model fields as much as possible.
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


def extract_units(conn, output_file):
    """
    Extract Units from fmUnits table and map to CSV fields aligned with Odoo model.

    Legacy columns (fmUnits):
      KCode, UnitCode, Unit, UnitAddress, LocationCode, CatCode, DateBuild, RentalAmount,
      RealEstateType, Size, Improvement, LessorCode, UnitType, Size2, ProjectName,
      SavingAcct, TypeOfUse, SOABankAcctNo

    Mapped CSV columns:
      lessor_code          -> LessorCode
      category_code        -> CatCode
      location_code        -> LocationCode
      kcode_code           -> KCode
      unit_code            -> UnitCode
      unit_specified       -> Unit (fallback to UnitCode)
      address              -> UnitAddress
      description          -> TypeOfUse (fallback to Improvement)
      size                 -> Size2 (fallback to Size)
      soa_bank_account_number -> SOABankAcctNo
      real_estate_type     -> RealEstateType
      unit_type            -> UnitType
      rental_amount        -> RentalAmount
      project_name         -> ProjectName
      improvement          -> Improvement
      type_of_use          -> TypeOfUse
    """
    query = """
        SELECT
            [KCode],
            [UnitCode],
            [Unit],
            [UnitAddress],
            [LocationCode],
            [CatCode],
            [RentalAmount],
            [RealEstateType],
            [Size],
            [Improvement],
            [LessorCode],
            [UnitType],
            [Size2],
            [ProjectName],
            [SavingAcct],
            [TypeOfUse],
            [SOABankAcctNo]
        FROM [fmUnits]
        WHERE [UnitCode] IS NOT NULL
    """

    print("\nExtracting Units from fmUnits...")
    print(f"Query:\n{query}")

    df = pd.read_sql(query, conn)
    if len(df) == 0:
        print("⚠ No rows returned from fmUnits.")
        return None

    # Build mapped dataframe
    def coalesce(a, b):
        return a if pd.notna(a) and str(a).strip() != '' else b

    mapped = pd.DataFrame()
    mapped["lessor_code"] = df["LessorCode"].fillna("").str.strip()
    mapped["category_code"] = df["CatCode"].fillna("").str.strip()
    mapped["location_code"] = df["LocationCode"].fillna("").str.strip()
    mapped["kcode_code"] = df["KCode"].fillna("").str.strip()
    mapped["unit_code"] = df["UnitCode"].fillna("").str.strip()

    unit_col = df["Unit"].fillna("").str.strip()
    mapped["unit_specified"] = unit_col
    mapped.loc[mapped["unit_specified"] == "", "unit_specified"] = mapped.loc[mapped["unit_specified"] == "", "unit_code"]

    mapped["address"] = df["UnitAddress"].fillna("").str.strip()

    mapped["type_of_use"] = df["TypeOfUse"].fillna("").str.strip()
    mapped["improvement"] = df["Improvement"].fillna("").str.strip()
    mapped["description"] = mapped["type_of_use"]
    mapped.loc[mapped["description"] == "", "description"] = mapped.loc[mapped["description"] == "", "improvement"]

    size2 = pd.to_numeric(df["Size2"], errors="coerce")
    size1 = pd.to_numeric(df["Size"], errors="coerce")
    mapped["size"] = size2
    mapped.loc[mapped["size"].isna(), "size"] = size1
    mapped["size"] = mapped["size"].fillna(0)

    mapped["soa_bank_account_number"] = df["SOABankAcctNo"].fillna("").str.strip()
    mapped["real_estate_type"] = df["RealEstateType"].fillna("").str.strip()
    mapped["unit_type"] = df["UnitType"].fillna("").str.strip()
    mapped["rental_amount"] = pd.to_numeric(df["RentalAmount"], errors="coerce").fillna(0)
    mapped["project_name"] = df["ProjectName"].fillna("").str.strip()
    mapped["saving_account"] = df["SavingAcct"].fillna("").str.strip()

    # Order columns for clarity
    ordered_cols = [
        "lessor_code",
        "category_code",
        "location_code",
        "kcode_code",
        "unit_code",
        "unit_specified",
        "address",
        "description",
        "size",
        "soa_bank_account_number",
        "rental_amount",
        "real_estate_type",
        "unit_type",
        "project_name",
        "type_of_use",
        "improvement",
        "saving_account",
    ]
    mapped = mapped[ordered_cols]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapped.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"✓ Extracted {len(mapped)} units to {output_file}")
    return mapped


def main():
    """Main extraction function."""
    db_path = os.environ.get("KST_DB_PATH") or DEFAULT_DB_PATH

    if not os.path.exists(db_path):
        print(f"\n✗ Database file not found: {db_path}")
        print("Please set KST_DB_PATH environment variable or update DEFAULT_DB_PATH")
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

        output_dir = Path(__file__).parent / "master_data_csv"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "units.csv"

        print("\n" + "=" * 60)
        print("EXTRACTING UNITS MASTERFILE")
        print("=" * 60)

        df_units = extract_units(conn, output_file)
        if df_units is not None and len(df_units) > 0:
            print(f"\nSample rows:")
            print(df_units.head(5).to_string(index=False))
        else:
            print("\n✗ No units extracted.")

        conn.close()
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE")
        print("=" * 60)
        print(f"\nCSV file saved to: {output_file}")

    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


