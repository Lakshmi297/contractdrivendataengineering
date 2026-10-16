-- Read-only validation for the Stage 0 Azure SQL schema-only pilot.
-- Run in database test_db_crelax after deployment.
-- Raises an error if an expected table or column is missing or differs.

SET NOCOUNT ON;

DECLARE @ExpectedColumns TABLE (
    table_name SYSNAME NOT NULL,
    column_name SYSNAME NOT NULL,
    type_name SYSNAME NOT NULL,
    max_length SMALLINT NOT NULL,
    precision_value TINYINT NOT NULL,
    scale_value TINYINT NOT NULL,
    is_nullable BIT NOT NULL,
    PRIMARY KEY (table_name, column_name)
);

INSERT INTO @ExpectedColumns
    (table_name, column_name, type_name, max_length, precision_value, scale_value, is_nullable)
VALUES
    (N'hub_customer', N'customer_hk', N'nvarchar', -1, 0, 0, 0),
    (N'hub_customer', N'customer_id', N'nvarchar', -1, 0, 0, 0),
    (N'hub_customer', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'hub_customer', N'record_source', N'nvarchar', -1, 0, 0, 0),

    (N'hub_order', N'order_hk', N'nvarchar', -1, 0, 0, 0),
    (N'hub_order', N'order_id', N'nvarchar', -1, 0, 0, 0),
    (N'hub_order', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'hub_order', N'record_source', N'nvarchar', -1, 0, 0, 0),

    (N'link_customer_order', N'customer_order_hk', N'nvarchar', -1, 0, 0, 0),
    (N'link_customer_order', N'customer_hk', N'nvarchar', -1, 0, 0, 0),
    (N'link_customer_order', N'order_hk', N'nvarchar', -1, 0, 0, 0),
    (N'link_customer_order', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'link_customer_order', N'record_source', N'nvarchar', -1, 0, 0, 0),

    (N'sat_customer_order_context', N'customer_order_hk', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_order_context', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'sat_customer_order_context', N'record_source', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_order_context', N'hashdiff', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_order_context', N'relationship_status', N'nvarchar', -1, 0, 0, 1),

    (N'sat_customer_profile', N'customer_hk', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_profile', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'sat_customer_profile', N'record_source', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_profile', N'hashdiff', N'nvarchar', -1, 0, 0, 0),
    (N'sat_customer_profile', N'customer_name', N'nvarchar', -1, 0, 0, 1),
    (N'sat_customer_profile', N'email_address', N'nvarchar', -1, 0, 0, 1),

    (N'sat_order_details', N'order_hk', N'nvarchar', -1, 0, 0, 0),
    (N'sat_order_details', N'load_datetime', N'datetime2', 8, 27, 7, 0),
    (N'sat_order_details', N'record_source', N'nvarchar', -1, 0, 0, 0),
    (N'sat_order_details', N'hashdiff', N'nvarchar', -1, 0, 0, 0),
    (N'sat_order_details', N'order_date', N'date', 3, 10, 0, 1),
    (N'sat_order_details', N'order_total', N'decimal', 17, 38, 9, 1);

DECLARE @ExpectedTables TABLE (table_name SYSNAME PRIMARY KEY);
INSERT INTO @ExpectedTables (table_name)
SELECT DISTINCT table_name FROM @ExpectedColumns;

DECLARE @MissingTables INT;
SELECT @MissingTables = COUNT(*)
FROM @ExpectedTables e
LEFT JOIN sys.tables t ON t.name = e.table_name
LEFT JOIN sys.schemas s ON s.schema_id = t.schema_id AND s.name = N'dbo'
WHERE t.object_id IS NULL OR s.schema_id IS NULL;

DECLARE @MissingOrMismatchedColumns INT;
SELECT @MissingOrMismatchedColumns = COUNT(*)
FROM @ExpectedColumns e
JOIN sys.tables t ON t.name = e.table_name
JOIN sys.schemas s ON s.schema_id = t.schema_id AND s.name = N'dbo'
LEFT JOIN sys.columns c ON c.object_id = t.object_id AND c.name = e.column_name
LEFT JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE c.column_id IS NULL
   OR ty.name <> e.type_name
   OR c.max_length <> e.max_length
   OR c.precision <> e.precision_value
   OR c.scale <> e.scale_value
   OR c.is_nullable <> e.is_nullable;

DECLARE @UnexpectedColumns INT;
SELECT @UnexpectedColumns = COUNT(*)
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id AND s.name = N'dbo'
JOIN @ExpectedTables et ON et.table_name = t.name
JOIN sys.columns c ON c.object_id = t.object_id
LEFT JOIN @ExpectedColumns e
    ON e.table_name = t.name AND e.column_name = c.name
WHERE e.column_name IS NULL;

IF @MissingTables <> 0
    THROW 51000, 'Azure SQL validation failed: one or more expected dbo tables are missing.', 1;
IF @MissingOrMismatchedColumns <> 0
    THROW 51001, 'Azure SQL validation failed: one or more expected columns differ from the contract.', 1;
IF @UnexpectedColumns <> 0
    THROW 51002, 'Azure SQL validation failed: unexpected columns exist in an expected table.', 1;

SELECT N'target_database' AS check_name,
       CASE WHEN DB_NAME() = N'test_db_crelax' THEN N'PASS' ELSE N'FAIL' END AS result,
       N'test_db_crelax' AS expected,
       DB_NAME() AS actual
UNION ALL
SELECT N'expected_tables', N'PASS', N'6', CONVERT(NVARCHAR(20), COUNT(*))
FROM @ExpectedTables
UNION ALL
SELECT N'expected_columns', N'PASS', N'30', CONVERT(NVARCHAR(20), COUNT(*))
FROM @ExpectedColumns
UNION ALL
SELECT N'missing_or_mismatched_columns', N'PASS', N'0', CONVERT(NVARCHAR(20), @MissingOrMismatchedColumns)
UNION ALL
SELECT N'unexpected_columns', N'PASS', N'0', CONVERT(NVARCHAR(20), @UnexpectedColumns);

SELECT s.name AS schema_name,
       t.name AS table_name,
       c.column_id,
       c.name AS column_name,
       ty.name AS data_type,
       c.max_length,
       c.precision,
       c.scale,
       c.is_nullable
FROM @ExpectedTables et
JOIN sys.tables t ON t.name = et.table_name
JOIN sys.schemas s ON s.schema_id = t.schema_id AND s.name = N'dbo'
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
ORDER BY t.name, c.column_id;
