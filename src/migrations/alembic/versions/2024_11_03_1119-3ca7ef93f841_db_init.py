"""DB Init

Revision ID: 3ca7ef93f841
Revises: 
Create Date: 2024-11-03 11:19:36.243482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ca7ef93f841'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""CREATE TABLE IF NOT EXISTS stg.api_couriers(
        id 				SERIAL CONSTRAINT pk_api_couriers PRIMARY KEY,
        object_value 	JSON NOT NULL,
        update_ts 		TIMESTAMP NOT NULL
    )""")   
    op.execute("""CREATE TABLE IF NOT EXISTS stg.api_deliveries(
        id 				SERIAL CONSTRAINT pk_api_deliveries PRIMARY KEY,
        object_value 	JSON NOT NULL,
        update_ts 		TIMESTAMP NOT NULL
    )""")   
    op.execute("""CREATE TABLE dds.dm_couriers(
        id 				SERIAL CONSTRAINT pk_dm_couriers PRIMARY KEY,
        courier_id 		VARCHAR NOT NULL,
        courier_name 	VARCHAR NOT NULL
    )""")   
    op.execute("""CREATE TABLE dds.fct_deliveries (
        id 				SERIAL CONSTRAINT pk_fct_deliveries PRIMARY KEY,
        order_id		INT NOT NULL,
        delivery_id 	VARCHAR NOT NULL,
        address 		VARCHAR NOT NULL,
        delivery_ts 	TIMESTAMP NOT NULL,
        rate 			SMALLINT NOT NULL CONSTRAINT check_fct_deliveries_rate CHECK(rate BETWEEN 0 AND 5),
        "sum" 			NUMERIC(14, 2) NOT NULL DEFAULT 0 CONSTRAINT check_fct_deliveries_sum CHECK("sum" >= 0),
        tip_sum 		NUMERIC(14, 2) NOT NULL DEFAULT 0 CONSTRAINT check_fct_deliveries_tip_sum CHECK(tip_sum >= 0),
        
        CONSTRAINT fk_fct_deliveries_order_id FOREIGN KEY(order_id) REFERENCES dds.dm_orders 
    )""")   
    op.execute("""ALTER TABLE dds.dm_orders ADD COLUMN courier_id int;
    ADD CONSTRAINT dm_orders_couriers_fk FOREIGN KEY (courier_id) REFERENCES dds.dm_couriers(id);""")   
    op.execute("""CREATE TABLE dds.dm_couriers(
        id 				SERIAL CONSTRAINT pk_dm_couriers PRIMARY KEY,
        courier_id 		VARCHAR NOT NULL,
        courier_name 	VARCHAR NOT NULL
    )""")   
    op.execute("""CREATE TABLE cdm.dm_courier_ledger (
		id 						SERIAL CONSTRAINT pk_dm_courier_ledger PRIMARY KEY,
		courier_id 				VARCHAR NOT NULL,
		courier_name 			VARCHAR(124) NOT NULL,
		settlement_year 		SMALLINT NOT NULL,
		settlement_month 		SMALLINT NOT NULL CONSTRAINT check_dm_courier_ledger_settlement_month CHECK(settlement_month BETWEEN 1 AND 12),
		orders_count 			INT4 DEFAULT 0 NOT NULL,
		orders_total_sum 		NUMERIC(14, 2) DEFAULT 0 NOT NULL,
		rate_avg 				NUMERIC(14, 2) DEFAULT 0 NOT NULL,
		order_processing_fee 	NUMERIC(14, 2) DEFAULT 0 NOT NULL,
		courier_order_sum 		NUMERIC(14, 2) DEFAULT 0 NOT NULL,
		courier_tips_sum 		NUMERIC(14, 2) DEFAULT 0 NOT NULL,
		courier_reward_sum 		NUMERIC(14, 2) DEFAULT 0 NOT NULL
    )""")   


def downgrade() -> None:
    op.execute("""DROP TABLE IF EXISTS stg.api_couriers""")
    op.execute("""DROP TABLE IF EXISTS stg.api_deliveries""")
    op.execute("""DROP TABLE IF EXISTS dds.dm_couriers""")
    op.execute("""DROP TABLE IF EXISTS dds.fct_deliveries""")
    op.execute("""ALTER TABLE dds.dm_orders DROP COLUMN courier_id""")
    op.execute("""DROP TABLE IF EXISTS dds.dm_couriers""")
    op.execute("""DROP TABLE IF EXISTS cdm.dm_courier_ledger""")
