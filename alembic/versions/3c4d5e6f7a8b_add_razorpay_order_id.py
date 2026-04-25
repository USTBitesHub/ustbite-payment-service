"""add_razorpay_order_id_to_payments

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-04-25 00:00:01
"""
from alembic import op

revision = '3c4d5e6f7a8b'
down_revision = '2b3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS razorpay_order_id VARCHAR"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE payments DROP COLUMN IF EXISTS razorpay_order_id"
    )
