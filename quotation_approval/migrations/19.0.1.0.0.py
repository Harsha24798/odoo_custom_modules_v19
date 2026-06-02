def migrate(cr, version):
    """
    Migration script to add approval-related fields to sale.order table.
    This handles the case where the module was partially installed before
    the fields were defined.
    """
    # Add approval_status column if it doesn't exist
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'sale_order' AND column_name = 'approval_status'
            ) THEN
                ALTER TABLE sale_order ADD COLUMN approval_status VARCHAR(32);
                COMMENT ON COLUMN sale_order.approval_status IS 'Approval Status (pending/approved/rejected)';
            END IF;
        END $$;
    """)

    # Add approved_by_user_id column if it doesn't exist
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'sale_order' AND column_name = 'approved_by_user_id'
            ) THEN
                ALTER TABLE sale_order ADD COLUMN approved_by_user_id INTEGER;
            END IF;
        END $$;
    """)

    # Add approval_date column if it doesn't exist
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'sale_order' AND column_name = 'approval_date'
            ) THEN
                ALTER TABLE sale_order ADD COLUMN approval_date TIMESTAMP;
            END IF;
        END $$;
    """)

    # Set default value for existing records
    cr.execute("""
        UPDATE sale_order 
        SET approval_status = 'pending'
        WHERE approval_status IS NULL;
    """)

