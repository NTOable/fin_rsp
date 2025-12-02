"""
Inventory Management System - Flask API
Connects to PostgreSQL database for CRUD operations
Converted to use psycopg (psycopg3) for Python 3.13 compatibility.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row
from psycopg import errors
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database Configuration
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        # Note: psycopg.connect returns a connection object
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except psycopg.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize the database table if it doesn't exist"""
    conn = get_db_connection()
    if conn:
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("""
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
                
                CREATE INDEX IF NOT EXISTS idx_item_sku ON Item(sku);
                CREATE INDEX IF NOT EXISTS idx_item_category ON Item(category);
                CREATE INDEX IF NOT EXISTS idx_item_status ON Item(status);
            """)
            conn.commit()
            print("Database initialized successfully!")
        except psycopg.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            if cur:
                cur.close()
            conn.close()

def serialize_item(item):
    """Convert database row to JSON-serializable dict"""
    if item is None:
        return None
    
    # item will already be a dict when using dict_row
    result = dict(item)
    # Convert Decimal to float for JSON serialization
    if 'unit_price' in result and result['unit_price'] is not None:
        result['unit_price'] = float(result['unit_price'])
    if 'total_revenue' in result and result['total_revenue'] is not None:
        result['total_revenue'] = float(result['total_revenue'])
    # Convert datetime to string
    if 'updated_at' in result and result['updated_at'] is not None:
        # Keep date-only format as before
        result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d')
    return result

# ==================== API ROUTES ====================

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all inventory items"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("SELECT * FROM Item ORDER BY updated_at DESC")
        items = cur.fetchall()
        return jsonify([serialize_item(item) for item in items])
    except psycopg.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a single item by ID"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("SELECT * FROM Item WHERE id = %s", (item_id,))
        item = cur.fetchone()
        if item:
            return jsonify(serialize_item(item))
        return jsonify({'error': 'Item not found'}), 404
    except psycopg.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/items', methods=['POST'])
def add_item():
    """Add a new inventory item"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['sku', 'name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        # Calculate total_revenue (stock * unit_price)
        stock = data.get('stock', 0)
        unit_price = data.get('unit_price', 0)
        total_revenue = float(stock) * float(unit_price)
        
        # Use provided status or auto-calculate based on stock level
        status = data.get('status')
        if not status or status not in ['In Stock', 'Low Stock', 'Out of Stock']:
            LOW_THRESHOLD = 10
            if stock <= 0:
                status = 'Out of Stock'
            elif stock <= LOW_THRESHOLD:
                status = 'Low Stock'
            else:
                status = 'In Stock'
        
        cur.execute("""
            INSERT INTO Item (sku, name, category, supplier, stock, unit_price, total_revenue, status, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING *
        """, (
            data['sku'],
            data['name'],
            data.get('category', ''),
            data.get('supplier', ''),
            stock,
            unit_price,
            total_revenue,
            status
        ))
        
        new_item = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'message': 'Item added successfully',
            'item': serialize_item(new_item)
        }), 201
        
    except errors.UniqueViolation as e:
        # Unique constraint (SKU) violation
        conn.rollback()
        return jsonify({'error': 'SKU already exists'}), 409
    except psycopg.DatabaseError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing inventory item"""
    data = request.get_json()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        # Check if item exists
        cur.execute("SELECT * FROM Item WHERE id = %s", (item_id,))
        existing_item = cur.fetchone()
        if not existing_item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Calculate total_revenue (stock * unit_price)
        stock = data.get('stock', existing_item['stock'])
        unit_price = data.get('unit_price', existing_item['unit_price'])
        total_revenue = float(stock) * float(unit_price)
        
        # Use provided status or auto-calculate based on stock level
        status = data.get('status')
        if not status or status not in ['In Stock', 'Low Stock', 'Out of Stock']:
            LOW_THRESHOLD = 10
            if stock <= 0:
                status = 'Out of Stock'
            elif stock <= LOW_THRESHOLD:
                status = 'Low Stock'
            else:
                status = 'In Stock'
        
        cur.execute("""
            UPDATE Item SET
                sku = %s,
                name = %s,
                category = %s,
                supplier = %s,
                stock = %s,
                unit_price = %s,
                total_revenue = %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
        """, (
            data.get('sku', existing_item['sku']),
            data.get('name', existing_item['name']),
            data.get('category', existing_item['category']),
            data.get('supplier', existing_item['supplier']),
            stock,
            unit_price,
            total_revenue,
            status,
            item_id
        ))
        
        updated_item = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'message': 'Item updated successfully',
            'item': serialize_item(updated_item)
        })
        
    except errors.UniqueViolation as e:
        conn.rollback()
        return jsonify({'error': 'SKU already exists'}), 409
    except psycopg.DatabaseError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an inventory item"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        # Check if item exists
        cur.execute("SELECT * FROM Item WHERE id = %s", (item_id,))
        item = cur.fetchone()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        cur.execute("DELETE FROM Item WHERE id = %s", (item_id,))
        conn.commit()
        
        return jsonify({
            'message': 'Item deleted successfully',
            'item': serialize_item(item)
        })
        
    except psycopg.DatabaseError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/items/bulk', methods=['POST'])
def add_bulk_items():
    """Add multiple items at once"""
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({'error': 'Expected a list of items'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        added_items = []
        errors = []
        
        for item_data in data:
            try:
                stock = item_data.get('stock', 0)
                unit_price = item_data.get('unit_price', 0)
                total_revenue = float(stock) * float(unit_price)
                
                LOW_THRESHOLD = 10
                if stock <= 0:
                    status = 'Out of Stock'
                elif stock <= LOW_THRESHOLD:
                    status = 'Low Stock'
                else:
                    status = 'In Stock'
                
                cur.execute("""
                    INSERT INTO Item (sku, name, category, supplier, stock, unit_price, total_revenue, status, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING *
                """, (
                    item_data['sku'],
                    item_data['name'],
                    item_data.get('category', ''),
                    item_data.get('supplier', ''),
                    stock,
                    unit_price,
                    total_revenue,
                    status
                ))
                added_items.append(serialize_item(cur.fetchone()))
            except Exception as e:
                errors.append({'sku': item_data.get('sku', 'unknown'), 'error': str(e)})
        
        conn.commit()
        
        return jsonify({
            'message': f'Added {len(added_items)} items',
            'added': added_items,
            'errors': errors
        }), 201
        
    except psycopg.DatabaseError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get inventory statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = None
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        # Total items
        cur.execute("SELECT COUNT(*) as total FROM Item")
        total_items = cur.fetchone()['total']
        
        # Total stock value
        cur.execute("SELECT COALESCE(SUM(total_revenue), 0) as value FROM Item")
        total_value = float(cur.fetchone()['value'])
        
        # Items by status
        cur.execute("""
            SELECT status, COUNT(*) as count 
            FROM Item 
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cur.fetchall()}
        
        # Items by category
        cur.execute("""
            SELECT category, COUNT(*) as count, SUM(stock) as total_stock
            FROM Item 
            GROUP BY category
        """)
        categories = [dict(row) for row in cur.fetchall()]
        
        # Unique suppliers
        cur.execute("SELECT COUNT(DISTINCT supplier) as count FROM Item")
        suppliers_count = cur.fetchone()['count']
        
        return jsonify({
            'total_items': total_items,
            'total_value': total_value,
            'status_counts': status_counts,
            'categories': categories,
            'suppliers_count': suppliers_count
        })
        
    except psycopg.DatabaseError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        conn.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check API and database health"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    return jsonify({
        'status': 'unhealthy',
        'database': 'disconnected',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'Inventory Management System API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/items': 'Get all items',
            'GET /api/items/<id>': 'Get single item',
            'POST /api/items': 'Add new item',
            'PUT /api/items/<id>': 'Update item',
            'DELETE /api/items/<id>': 'Delete item',
            'POST /api/items/bulk': 'Add multiple items',
            'GET /api/stats': 'Get inventory statistics',
            'GET /api/health': 'Health check'
        }
    })

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Starting Flask server on http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
