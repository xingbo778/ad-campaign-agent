"""
Product data loading from database or CSV.

Supports:
- PostgreSQL via SQLAlchemy
- CSV file fallback
"""

import os
import csv
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.common.schemas import Product
from app.common.db import get_db_session, is_db_available

# Import ProductORM only if SQLAlchemy is available
try:
    from app.common.db import ProductORM
    PRODUCTORM_AVAILABLE = True
except (ImportError, AttributeError):
    PRODUCTORM_AVAILABLE = False
    ProductORM = None
from app.common.middleware import get_logger

logger = get_logger(__name__)

# In-memory product cache (for CSV mode)
_product_cache: List[Product] = []
_csv_loaded = False


def load_products_from_db(category: Optional[str] = None) -> List[Product]:
    """
    Load products from PostgreSQL database.
    
    Args:
        category: Optional category filter
        
    Returns:
        List of Product objects
    """
    if not is_db_available() or not PRODUCTORM_AVAILABLE:
        return []
    
    products = []
    try:
        with get_db_session() as db:
            if db is None:
                return []
            
            query = db.query(ProductORM)
            if category:
                query = query.filter(ProductORM.category.ilike(f"%{category}%"))
            
            product_orms = query.all()
            
            for p_orm in product_orms:
                product = Product(
                    product_id=p_orm.product_id,
                    title=p_orm.title,
                    description=p_orm.description,
                    price=p_orm.price,
                    category=p_orm.category,
                    image_url=p_orm.image_url,
                    metadata=p_orm.metadata or {}
                )
                products.append(product)
            
            logger.info(f"Loaded {len(products)} products from database" + 
                       (f" (category: {category})" if category else ""))
            
    except Exception as e:
        logger.error(f"Error loading products from database: {e}")
        return []
    
    return products


def load_products_from_csv(csv_path: Optional[str] = None) -> List[Product]:
    """
    Load products from CSV file.
    
    Expected CSV columns:
    - product_id, title, description, price, category, image_url, metadata_json
    
    Args:
        csv_path: Path to CSV file. If None, looks for products.csv in service directory.
        
    Returns:
        List of Product objects
    """
    global _product_cache, _csv_loaded
    
    if _csv_loaded:
        return _product_cache.copy()
    
    if csv_path is None:
        # Default CSV location
        service_dir = Path(__file__).parent
        csv_path = service_dir / "products.csv"
    
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        logger.warning(f"CSV file not found: {csv_path}. Using default sample products.")
        return _get_default_products()
    
    products = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse metadata if present
                    metadata = {}
                    if 'metadata_json' in row and row['metadata_json']:
                        import json
                        metadata = json.loads(row['metadata_json'])
                    
                    product = Product(
                        product_id=row.get('product_id', ''),
                        title=row.get('title', row.get('name', '')),
                        description=row.get('description', ''),
                        price=float(row.get('price', 0)),
                        category=row.get('category', 'general'),
                        image_url=row.get('image_url'),
                        metadata=metadata
                    )
                    products.append(product)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row in CSV: {e}")
                    continue
        
        _product_cache = products
        _csv_loaded = True
        logger.info(f"Loaded {len(products)} products from CSV: {csv_path}")
        
    except Exception as e:
        logger.error(f"Error loading products from CSV: {e}")
        return _get_default_products()
    
    return products.copy()


def _get_default_products() -> List[Product]:
    """Get default sample products when no data source is available."""
    return [
        Product(
            product_id="PROD-001",
            title="Premium Wireless Headphones",
            description="High-quality noise-canceling wireless headphones with premium sound quality and long battery life. Perfect for music lovers and professionals.",
            price=299.99,
            category="electronics",
            image_url="https://example.com/images/headphones.jpg",
            metadata={"brand": "AudioTech", "warranty": "2 years"}
        ),
        Product(
            product_id="PROD-002",
            title="Smart Watch Pro",
            description="Advanced fitness tracking smartwatch with heart rate monitor, GPS, and 7-day battery life. Waterproof design for active lifestyles.",
            price=399.99,
            category="electronics",
            image_url="https://example.com/images/smartwatch.jpg",
            metadata={"brand": "TechWear", "features": ["GPS", "heart_rate", "waterproof"]}
        ),
        Product(
            product_id="PROD-003",
            title="Bluetooth Speaker",
            description="Portable waterproof Bluetooth speaker with 360-degree sound and 12-hour battery. Perfect for outdoor adventures and parties.",
            price=79.99,
            category="electronics",
            image_url="https://example.com/images/speaker.jpg",
            metadata={"waterproof": True, "battery_hours": 12}
        ),
        Product(
            product_id="PROD-004",
            title="Wireless Charger",
            description="Fast wireless charging pad compatible with all Qi-enabled devices. Sleek design with LED indicator.",
            price=39.99,
            category="accessories",
            image_url="https://example.com/images/charger.jpg",
            metadata={"compatibility": "Qi", "wattage": 15}
        ),
        Product(
            product_id="PROD-005",
            title="USB-C Cable",
            description="Durable USB-C charging cable with fast charging support. 6-foot length with reinforced connectors.",
            price=14.99,
            category="accessories",
            image_url="https://example.com/images/cable.jpg",
            metadata={"length_feet": 6, "fast_charging": True}
        ),
        Product(
            product_id="PROD-006",
            title="Laptop Stand",
            description="Ergonomic aluminum laptop stand with adjustable height. Improves posture and workspace organization.",
            price=49.99,
            category="accessories",
            image_url="https://example.com/images/stand.jpg",
            metadata={"material": "aluminum", "adjustable": True}
        ),
        Product(
            product_id="PROD-007",
            title="Mechanical Keyboard",
            description="RGB backlit mechanical keyboard with Cherry MX switches. Perfect for gaming and typing enthusiasts.",
            price=129.99,
            category="electronics",
            image_url="https://example.com/images/keyboard.jpg",
            metadata={"switch_type": "Cherry MX", "rgb": True}
        ),
        Product(
            product_id="PROD-008",
            title="Gaming Mouse",
            description="High-precision gaming mouse with customizable DPI and RGB lighting. Ergonomic design for long gaming sessions.",
            price=69.99,
            category="electronics",
            image_url="https://example.com/images/mouse.jpg",
            metadata={"dpi": 16000, "rgb": True}
        ),
        Product(
            product_id="PROD-009",
            title="Monitor Stand",
            description="Dual monitor stand with gas spring arms. Supports up to 27-inch monitors with cable management.",
            price=159.99,
            category="accessories",
            image_url="https://example.com/images/monitor_stand.jpg",
            metadata={"max_size": "27 inch", "dual": True}
        ),
        Product(
            product_id="PROD-010",
            title="Webcam HD",
            description="1080p HD webcam with auto-focus and built-in microphone. Perfect for video calls and streaming.",
            price=89.99,
            category="electronics",
            image_url="https://example.com/images/webcam.jpg",
            metadata={"resolution": "1080p", "microphone": True}
        ),
        Product(
            product_id="PROD-011",
            title="General Product A",
            description="A versatile general-purpose product suitable for various use cases. High quality and reliable.",
            price=49.99,
            category="general",
            image_url="https://example.com/images/general_a.jpg",
            metadata={"type": "general", "versatile": True}
        ),
        Product(
            product_id="PROD-012",
            title="General Product B",
            description="Another general-purpose product with excellent value. Perfect for everyday needs.",
            price=39.99,
            category="general",
            image_url="https://example.com/images/general_b.jpg",
            metadata={"type": "general", "value": True}
        )
    ]


def load_products(category: Optional[str] = None) -> List[Product]:
    """
    Load products from available data source (database or CSV).
    
    Priority:
    1. PostgreSQL database (if DATABASE_URL is set)
    2. CSV file (if available)
    3. Default sample products
    
    Args:
        category: Optional category filter
        
    Returns:
        List of Product objects
    """
    # Try database first
    if is_db_available():
        products = load_products_from_db(category)
        if products:
            return products
    
    # Fallback to CSV
    products = load_products_from_csv()
    if products:
        if category:
            # Filter by category (case-insensitive, partial match)
            category_lower = category.lower()
            products = [p for p in products if category_lower in p.category.lower() or p.category.lower() in category_lower]
        return products
    
    # Last resort: default products
    logger.warning("No data source available, using default sample products")
    default_products = _get_default_products()
    if category:
        # Filter by category (case-insensitive, partial match)
        category_lower = category.lower()
        default_products = [p for p in default_products if category_lower in p.category.lower() or p.category.lower() in category_lower]
    return default_products


def get_all_products() -> List[Product]:
    """Get all products from available data source."""
    return load_products()


def get_products_by_category(category: str) -> List[Product]:
    """Get products filtered by category."""
    return load_products(category=category)


def reload_products() -> None:
    """Force reload products from data source (clears cache)."""
    global _product_cache, _csv_loaded
    _product_cache = []
    _csv_loaded = False

