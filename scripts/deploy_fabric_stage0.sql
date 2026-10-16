-- Stage 0 Fabric Lakehouse schema-only pilot.
-- In workspace Lakshmi297, open a notebook, attach the intended Lakehouse,
-- and run each statement in a Spark SQL cell (for example, a cell starting
-- with %%sql). Do not run this in the read-only SQL analytics endpoint.
-- Check for existing tables first: IF NOT EXISTS leaves them unchanged.
-- This creates empty Delta tables; it does not load customer/order records.

CREATE TABLE IF NOT EXISTS hub_customer (
    customer_hk STRING NOT NULL,
    customer_id STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS hub_order (
    order_hk STRING NOT NULL,
    order_id STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS link_customer_order (
    customer_order_hk STRING NOT NULL,
    customer_hk STRING NOT NULL,
    order_hk STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS sat_customer_order_context (
    customer_order_hk STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL,
    hashdiff STRING NOT NULL,
    relationship_status STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS sat_customer_profile (
    customer_hk STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL,
    hashdiff STRING NOT NULL,
    customer_name STRING,
    email_address STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS sat_order_details (
    order_hk STRING NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source STRING NOT NULL,
    hashdiff STRING NOT NULL,
    order_date DATE,
    order_total DECIMAL(38, 9)
) USING DELTA;

SHOW TABLES;
DESCRIBE TABLE hub_customer;
DESCRIBE TABLE hub_order;
DESCRIBE TABLE link_customer_order;
DESCRIBE TABLE sat_customer_order_context;
DESCRIBE TABLE sat_customer_profile;
DESCRIBE TABLE sat_order_details;
