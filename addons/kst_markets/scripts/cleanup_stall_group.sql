-- Cleanup script to remove kst.stall.group model and all related database records
-- Run this script directly in your PostgreSQL database

BEGIN;

-- Delete ir.model.fields records for kst.stall.group
DELETE FROM ir_model_fields 
WHERE model_id IN (
    SELECT id FROM ir_model WHERE model = 'kst.stall.group'
);

-- Delete ir.model.access records for kst.stall.group
DELETE FROM ir_model_access 
WHERE model_id IN (
    SELECT id FROM ir_model WHERE model = 'kst.stall.group'
);

-- Delete ir.model.data records for kst.stall.group
DELETE FROM ir_model_data 
WHERE model = 'kst.stall.group';

-- Delete ir.actions.act_window records that reference kst.stall.group
DELETE FROM ir_actions_act_window 
WHERE res_model = 'kst.stall.group';

-- Delete ir.ui.view records for kst.stall.group
DELETE FROM ir_ui_view 
WHERE model = 'kst.stall.group';

-- Delete menu items that reference stall_group
DELETE FROM ir_ui_menu 
WHERE name = 'Stall Groups' 
AND (action LIKE '%stall_group%' OR action LIKE '%action_stall_group%');

-- Clean up foreign key references in kst_stall table
-- First, set stall_group_id to NULL
UPDATE kst_stall 
SET stall_group_id = NULL 
WHERE stall_group_id IS NOT NULL;

-- Drop foreign key constraints on kst_stall.stall_group_id
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE constraint_name LIKE '%stall_group%'
        AND table_name = 'kst_stall'
    ) LOOP
        EXECUTE 'ALTER TABLE kst_stall DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
    END LOOP;
END $$;

-- Drop the column
ALTER TABLE kst_stall DROP COLUMN IF EXISTS stall_group_id;

-- Clean up foreign key references in kst_market_utility_transaction table
-- First, set stall_group_id to NULL
UPDATE kst_market_utility_transaction 
SET stall_group_id = NULL 
WHERE stall_group_id IS NOT NULL;

-- Drop foreign key constraints on kst_market_utility_transaction.stall_group_id
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE constraint_name LIKE '%stall_group%'
        AND table_name = 'kst_market_utility_transaction'
    ) LOOP
        EXECUTE 'ALTER TABLE kst_market_utility_transaction DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
    END LOOP;
END $$;

-- Drop the column
ALTER TABLE kst_market_utility_transaction DROP COLUMN IF EXISTS stall_group_id;

-- Drop the kst_stall_group table if it exists
DROP TABLE IF EXISTS kst_stall_group CASCADE;

-- Delete ir.model record for kst.stall.group (do this last)
DELETE FROM ir_model 
WHERE model = 'kst.stall.group';

COMMIT;

-- Verify cleanup
SELECT 'Cleanup completed. Remaining references:' as status;
SELECT COUNT(*) as remaining_ir_model FROM ir_model WHERE model = 'kst.stall.group';
SELECT COUNT(*) as remaining_ir_model_data FROM ir_model_data WHERE model = 'kst.stall.group';
SELECT COUNT(*) as remaining_ir_ui_view FROM ir_ui_view WHERE model = 'kst.stall.group';

