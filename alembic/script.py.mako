"""
Template for alembic revision file.

The standard alembic `script.py.mako` template slightly adapted.
"""
<%!
from alembic import op
import sqlalchemy as sa
%>
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | none}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa

revision = ${up_revision!r}
down_revision = ${down_revision!r}
branch_labels = ${branch_labels!r}
depends_on = ${depends_on!r}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
