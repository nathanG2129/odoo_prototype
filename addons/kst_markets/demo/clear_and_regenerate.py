"""
Clear existing demo data and regenerate from real Access database stalls.
"""
import os
import sys

# Get the demo directory
demo_dir = os.path.dirname(__file__)

# Clear existing demo data
demo_file = os.path.join(demo_dir, 'kst_markets_demo.xml')
if os.path.exists(demo_file):
    os.remove(demo_file)
    print(f"Cleared existing demo data: {demo_file}")

# Run the extraction script
print("\n" + "=" * 60)
print("Extracting real stalls from Access database...")
print("=" * 60)

# Import and run the extraction
from extract_real_stalls import extract_stall_data, generate_demo_from_real_data

# Try to get database path from environment or use default
db_path = os.environ.get('KST_DB_PATH')
if not db_path:
    # Try common locations
    possible_paths = [
        r"C:\KST_DB.mdb",
        r"C:\Users\kst11\Desktop\TEST\up-to-nov27\KST_DB.mdb",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

if not db_path:
    print("\nDatabase path not found. Please provide it:")
    db_path = input("Enter path to KST_DB.mdb: ").strip().strip('"')

if db_path and os.path.exists(db_path):
    extracted = extract_stall_data(db_path)
    if extracted:
        os.chdir(demo_dir)
        generate_demo_from_real_data(extracted)
        print("\n✓ Demo data regenerated from real stalls!")
    else:
        print("\n✗ Failed to extract data.")
else:
    print(f"\n✗ Database file not found: {db_path}")
    print("Please set KST_DB_PATH environment variable or provide the path.")

