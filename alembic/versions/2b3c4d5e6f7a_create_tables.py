"""create_payment_tables

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-04-25 00:00:00
"""
from alembic import op

revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # asyncpg requires ONE statement per op.execute() call

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE payment_status AS ENUM ('PENDING', 'SUCCESS', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE payment_method AS ENUM ('UPI', 'CARD', 'CASH_ON_DELIVERY');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE refund_status AS ENUM ('PENDING', 'PROCESSED', 'REJECTED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL,
            user_id UUID NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            currency VARCHAR DEFAULT 'INR',
            status payment_status DEFAULT 'PENDING',
            method payment_method NOT NULL,
            provider_reference VARCHAR,
            failure_reason VARCHAR,
            user_email VARCHAR,
            user_name VARCHAR,
            restaurant_name VARCHAR,
            delivery_floor VARCHAR,
            delivery_wing VARCHAR,
            estimated_minutes INTEGER,
            items JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_payments_order_id ON payments(order_id)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_payments_user_id ON payments(user_id)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            payment_id UUID NOT NULL REFERENCES payments(id),
            amount NUMERIC(10,2) NOT NULL,
            reason VARCHAR,
            status refund_status DEFAULT 'PENDING',
            user_email VARCHAR,
            user_name VARCHAR,
            restaurant_name VARCHAR,
            delivery_floor VARCHAR,
            delivery_wing VARCHAR,
            estimated_minutes INTEGER,
            items JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refunds CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TYPE IF EXISTS refund_status")
    op.execute("DROP TYPE IF EXISTS payment_method")
    op.execute("DROP TYPE IF EXISTS payment_status")
