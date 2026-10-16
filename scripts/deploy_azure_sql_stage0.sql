-- Stage 0 Azure SQL schema-only pilot.
-- Run against the approved test database after reviewing the target.
-- This creates empty Data Vault tables and does not load source records.
-- Existing tables are left unchanged.

IF OBJECT_ID(N'dbo.hub_customer', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.hub_customer (
        customer_hk NVARCHAR(MAX) NOT NULL,
        customer_id NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.hub_order', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.hub_order (
        order_hk NVARCHAR(MAX) NOT NULL,
        order_id NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.link_customer_order', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.link_customer_order (
        customer_order_hk NVARCHAR(MAX) NOT NULL,
        customer_hk NVARCHAR(MAX) NOT NULL,
        order_hk NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.sat_customer_order_context', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sat_customer_order_context (
        customer_order_hk NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL,
        hashdiff NVARCHAR(MAX) NOT NULL,
        relationship_status NVARCHAR(MAX) NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.sat_customer_profile', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sat_customer_profile (
        customer_hk NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL,
        hashdiff NVARCHAR(MAX) NOT NULL,
        customer_name NVARCHAR(MAX) NULL,
        email_address NVARCHAR(MAX) NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.sat_order_details', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sat_order_details (
        order_hk NVARCHAR(MAX) NOT NULL,
        load_datetime DATETIME2(7) NOT NULL,
        record_source NVARCHAR(MAX) NOT NULL,
        hashdiff NVARCHAR(MAX) NOT NULL,
        order_date DATE NULL,
        order_total DECIMAL(38, 9) NULL
    );
END;
GO
