#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup script to remove kst.stall.group model and all related database records.
Run this script using Odoo shell or directly with database connection.

Usage with Odoo shell:
    odoo shell -d your_database_name
    >>> exec(open('addons/markets/scripts/cleanup_stall_group.py').read())

Or run directly with psycopg2:
    python cleanup_stall_group.py
"""

import psycopg2
import sys
import os

# Database connection parameters - adjust as needed
DB_NAME = os.environ.get('DB_NAME', 'odoo')
DB_USER = os.environ.get('DB_USER', 'odoo')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'odoo')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

def cleanup_stall_group():
    """Clean up all database records related to kst.stall.group"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cr = conn.cursor()
        
        print("Starting cleanup of kst.stall.group model...")
        
        # Delete ir.model.fields records for kst.stall.group
        print("Deleting ir.model.fields records...")
        cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE model_id IN (
                SELECT id FROM ir_model WHERE model = 'kst.stall.group'
            )
        """)
        print(f"  Deleted {cr.rowcount} field records")
        
        # Delete ir.model.access records for kst.stall.group
        print("Deleting ir.model.access records...")
        cr.execute("""
            DELETE FROM ir_model_access 
            WHERE model_id IN (
                SELECT id FROM ir_model WHERE model = 'kst.stall.group'
            )
        """)
        print(f"  Deleted {cr.rowcount} access records")
        
        # Delete ir.model.data records for kst.stall.group
        print("Deleting ir.model.data records...")
        cr.execute("""
            DELETE FROM ir_model_data 
            WHERE model = 'kst.stall.group'
        """)
        print(f"  Deleted {cr.rowcount} data records")
        
        # Delete ir.actions.act_window records that reference kst.stall.group
        print("Deleting ir.actions.act_window records...")
        cr.execute("""
            DELETE FROM ir_actions_act_window 
            WHERE res_model = 'kst.stall.group'
        """)
        print(f"  Deleted {cr.rowcount} action records")
        
        # Delete ir.ui.view records for kst.stall.group
        print("Deleting ir.ui.view records...")
        cr.execute("""
            DELETE FROM ir_ui_view 
            WHERE model = 'kst.stall.group'
        """)
        print(f"  Deleted {cr.rowcount} view records")
        
        # Delete menu items that reference stall_group
        print("Deleting menu items...")
        cr.execute("""
            DELETE FROM ir_ui_menu 
            WHERE name = 'Stall Groups' 
            AND (action LIKE '%stall_group%' OR action LIKE '%action_stall_group%')
        """)
        print(f"  Deleted {cr.rowcount} menu records")
        
        # Clean up foreign key references in kst_stall table
        print("Cleaning up kst_stall.stall_group_id column...")
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'kst_stall' 
            AND column_name = 'stall_group_id'
        """)
        
        if cr.fetchone():
            # Set stall_group_id to NULL
            cr.execute("""
                UPDATE kst_stall 
                SET stall_group_id = NULL 
                WHERE stall_group_id IS NOT NULL
            """)
            print(f"  Updated {cr.rowcount} stall records")
            
            # Drop the foreign key constraint
            cr.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name LIKE '%stall_group%'
                AND table_name = 'kst_stall'
            """)
            constraints = cr.fetchall()
            for (constraint_name,) in constraints:
                cr.execute(f"ALTER TABLE kst_stall DROP CONSTRAINT IF EXISTS {constraint_name}")
                print(f"  Dropped constraint {constraint_name}")
            
            # Drop the column
            cr.execute("ALTER TABLE kst_stall DROP COLUMN IF EXISTS stall_group_id")
            print("  Dropped stall_group_id column")
        else:
            print("  Column already removed")
        
        # Clean up foreign key references in kst_market_utility_transaction table
        print("Cleaning up kst_market_utility_transaction.stall_group_id column...")
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'kst_market_utility_transaction' 
            AND column_name = 'stall_group_id'
        """)
        
        if cr.fetchone():
            # Set stall_group_id to NULL
            cr.execute("""
                UPDATE kst_market_utility_transaction 
                SET stall_group_id = NULL 
                WHERE stall_group_id IS NOT NULL
            """)
            print(f"  Updated {cr.rowcount} utility transaction records")
            
            # Drop the foreign key constraint
            cr.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name LIKE '%stall_group%'
                AND table_name = 'kst_market_utility_transaction'
            """)
            constraints = cr.fetchall()
            for (constraint_name,) in constraints:
                cr.execute(f"ALTER TABLE kst_market_utility_transaction DROP CONSTRAINT IF EXISTS {constraint_name}")
                print(f"  Dropped constraint {constraint_name}")
            
            # Drop the column
            cr.execute("ALTER TABLE kst_market_utility_transaction DROP COLUMN IF EXISTS stall_group_id")
            print("  Dropped stall_group_id column")
        else:
            print("  Column already removed")
        
        # Drop the kst_stall_group table if it exists
        print("Dropping kst_stall_group table...")
        cr.execute("DROP TABLE IF EXISTS kst_stall_group CASCADE")
        print("  Table dropped")
        
        # Delete ir.model record for kst.stall.group (do this last)
        print("Deleting ir.model record...")
        cr.execute("""
            DELETE FROM ir_model 
            WHERE model = 'kst.stall.group'
        """)
        print(f"  Deleted {cr.rowcount} model record")
        
        # Commit all changes
        conn.commit()
        print("\nCleanup completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\nError during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            cr.close()
            conn.close()

if __name__ == '__main__':
    cleanup_stall_group()

