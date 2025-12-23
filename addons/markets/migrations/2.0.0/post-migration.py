# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Clean up database records for deleted kst.stall.group model
    """
    # Delete ir.model.fields records for kst.stall.group
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE model_id IN (
            SELECT id FROM ir_model WHERE model = 'kst.stall.group'
        )
    """)
    
    # Delete ir.model.access records for kst.stall.group
    cr.execute("""
        DELETE FROM ir_model_access 
        WHERE model_id IN (
            SELECT id FROM ir_model WHERE model = 'kst.stall.group'
        )
    """)
    
    # Delete ir.model.data records for kst.stall.group
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'kst.stall.group'
    """)
    
    # Delete ir.actions.act_window records that reference kst.stall.group
    cr.execute("""
        DELETE FROM ir_actions_act_window 
        WHERE res_model = 'kst.stall.group'
    """)
    
    # Delete ir.ui.view records for kst.stall.group
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE model = 'kst.stall.group'
    """)
    
    # Delete ir.model record for kst.stall.group
    cr.execute("""
        DELETE FROM ir_model 
        WHERE model = 'kst.stall.group'
    """)
    
    # Delete any menu items that reference stall_group actions
    cr.execute("""
        DELETE FROM ir_ui_menu 
        WHERE name = 'Stall Groups' 
        AND action LIKE '%stall_group%'
    """)
    
    # Clean up any foreign key references in kst_stall table
    # First, check if the column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'kst_stall' 
        AND column_name = 'stall_group_id'
    """)
    
    if cr.fetchone():
        # Set stall_group_id to NULL for all records
        cr.execute("""
            UPDATE kst_stall 
            SET stall_group_id = NULL 
            WHERE stall_group_id IS NOT NULL
        """)
        
        # Drop the foreign key constraint if it exists
        cr.execute("""
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'kst_stall_stall_group_id_fkey'
                    AND table_name = 'kst_stall'
                ) THEN
                    ALTER TABLE kst_stall DROP CONSTRAINT kst_stall_stall_group_id_fkey;
                END IF;
            END $$;
        """)
        
        # Drop the column
        cr.execute("""
            ALTER TABLE kst_stall DROP COLUMN IF EXISTS stall_group_id
        """)
    
    # Clean up any foreign key references in kst_market_utility_transaction table
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'kst_market_utility_transaction' 
        AND column_name = 'stall_group_id'
    """)
    
    if cr.fetchone():
        # Set stall_group_id to NULL for all records
        cr.execute("""
            UPDATE kst_market_utility_transaction 
            SET stall_group_id = NULL 
            WHERE stall_group_id IS NOT NULL
        """)
        
        # Drop the foreign key constraint if it exists
        cr.execute("""
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'kst_market_utility_transaction_stall_group_id_fkey'
                    AND table_name = 'kst_market_utility_transaction'
                ) THEN
                    ALTER TABLE kst_market_utility_transaction DROP CONSTRAINT kst_market_utility_transaction_stall_group_id_fkey;
                END IF;
            END $$;
        """)
        
        # Drop the column
        cr.execute("""
            ALTER TABLE kst_market_utility_transaction DROP COLUMN IF EXISTS stall_group_id
        """)
    
    # Drop the kst_stall_group table if it exists
    cr.execute("""
        DROP TABLE IF EXISTS kst_stall_group CASCADE
    """)
    
    # Commit the changes
    cr.commit()

