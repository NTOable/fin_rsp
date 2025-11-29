-- Create Item table for inventory management
-- PostgreSQL Database Script

CREATE TABLE IF NOT EXISTS Item (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    supplier VARCHAR(255),
    stock INTEGER DEFAULT 0,
    unit_price DECIMAL(10, 2) DEFAULT 0.00,
    total_revenue DECIMAL(12, 2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'Active',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on SKU for faster lookups
CREATE INDEX IF NOT EXISTS idx_item_sku ON Item(sku);

-- Create an index on category for filtering
CREATE INDEX IF NOT EXISTS idx_item_category ON Item(category);

-- Create an index on status for filtering
CREATE INDEX IF NOT EXISTS idx_item_status ON Item(status);

-- Optional: Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_item_modtime
    BEFORE UPDATE ON Item
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Sample insert statement (commented out)
-- INSERT INTO Item (sku, name, category, supplier, stock, unit_price, total_revenue, status)
-- VALUES ('SKU-001', 'Sample Product', 'Electronics', 'Supplier A', 100, 29.99, 2999.00, 'Active');

