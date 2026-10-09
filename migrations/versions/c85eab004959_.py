"""Add user ownership to business data

Revision ID: c85eab004959
Revises: 41dc6f5d8d99
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c85eab004959"
down_revision = "41dc6f5d8d99"
branch_labels = None
depends_on = None


def upgrade():

    # ==========================================
    # BUSINESS INFORMATION
    # ==========================================

    with op.batch_alter_table(
        "business_information",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            )
        )

    # Existing business information belongs
    # to Rakesh (User ID = 1)
    op.execute(
        "UPDATE business_information SET user_id = 1 "
        "WHERE user_id IS NULL"
    )

    with op.batch_alter_table(
        "business_information",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_foreign_key(
            "fk_business_information_user",
            "users",
            ["user_id"],
            ["id"]
        )


    # ==========================================
    # FAQ
    # ==========================================

    with op.batch_alter_table(
        "faqs",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            )
        )

    # Existing FAQs belong to Rakesh
    op.execute(
        "UPDATE faqs SET user_id = 1 "
        "WHERE user_id IS NULL"
    )

    with op.batch_alter_table(
        "faqs",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_foreign_key(
            "fk_faqs_user",
            "users",
            ["user_id"],
            ["id"]
        )


    # ==========================================
    # PROPERTIES
    # ==========================================

    with op.batch_alter_table(
        "properties",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            )
        )

    # Existing properties belong to Rakesh
    op.execute(
        "UPDATE properties SET user_id = 1 "
        "WHERE user_id IS NULL"
    )

    with op.batch_alter_table(
        "properties",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_foreign_key(
            "fk_properties_user",
            "users",
            ["user_id"],
            ["id"]
        )


    # ==========================================
    # CUSTOMERS
    # ==========================================

    with op.batch_alter_table(
        "customers",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            )
        )

    # Existing customers belong to Rakesh
    op.execute(
        "UPDATE customers SET user_id = 1 "
        "WHERE user_id IS NULL"
    )

    with op.batch_alter_table(
        "customers",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_foreign_key(
            "fk_customers_user",
            "users",
            ["user_id"],
            ["id"]
        )


    # ==========================================
    # LEADS
    # ==========================================

    with op.batch_alter_table(
        "leads",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            )
        )

    # Existing leads belong to Rakesh
    op.execute(
        "UPDATE leads SET user_id = 1 "
        "WHERE user_id IS NULL"
    )

    with op.batch_alter_table(
        "leads",
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_foreign_key(
            "fk_leads_user",
            "users",
            ["user_id"],
            ["id"]
        )


def downgrade():

    # ==========================================
    # LEADS
    # ==========================================

    with op.batch_alter_table(
        "leads",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_leads_user",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")


    # ==========================================
    # CUSTOMERS
    # ==========================================

    with op.batch_alter_table(
        "customers",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_customers_user",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")


    # ==========================================
    # PROPERTIES
    # ==========================================

    with op.batch_alter_table(
        "properties",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_properties_user",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")


    # ==========================================
    # FAQ
    # ==========================================

    with op.batch_alter_table(
        "faqs",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_faqs_user",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")


    # ==========================================
    # BUSINESS INFORMATION
    # ==========================================

    with op.batch_alter_table(
        "business_information",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_business_information_user",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")