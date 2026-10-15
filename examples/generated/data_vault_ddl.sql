-- Generated from a validated contract. Do not edit by hand.

-- Data Vault 2.0 DDL target: demo-data-dev.dv_stage0

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.hub_customer` (
  `customer_hk` STRING NOT NULL,
  `customer_id` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.sat_customer_profile` (
  `customer_hk` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL,
  `hashdiff` STRING NOT NULL,
  `customer_name` STRING,
  `email_address` STRING
);

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.hub_order` (
  `order_hk` STRING NOT NULL,
  `order_id` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.sat_order_details` (
  `order_hk` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL,
  `hashdiff` STRING NOT NULL,
  `order_date` DATE,
  `order_total` NUMERIC
);

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.link_customer_order` (
  `customer_order_hk` STRING NOT NULL,
  `customer_hk` STRING NOT NULL,
  `order_hk` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `demo-data-dev.dv_stage0.sat_customer_order_context` (
  `customer_order_hk` STRING NOT NULL,
  `load_datetime` TIMESTAMP NOT NULL,
  `record_source` STRING NOT NULL,
  `hashdiff` STRING NOT NULL,
  `relationship_status` STRING
);
