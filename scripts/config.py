"""
OmniRetail Synthetic Data Generator - Configuration
Author: [Your Name]
Purpose: Generate realistic retailer credit data for ML modeling
"""

# ============================================================================
# RETAILER GENERATION SETTINGS
# ============================================================================

NUM_RETAILERS = 10000  # Total number of retailers to generate
RANDOM_SEED = 42  # For reproducibility

# ============================================================================
# BUSINESS PARAMETERS (Based on OmniRetail's actual operations)
# ============================================================================

# Geographic distribution (OmniRetail operates in Nigeria primarily)
STATES = {
    'Lagos': 0.35,      # 35% of retailers in Lagos
    'Kano': 0.12,
    'Rivers': 0.10,
    'Oyo': 0.08,
    'Kaduna': 0.07,
    'FCT': 0.06,       # Federal Capital Territory (Abuja)
    'Ogun': 0.05,
    'Anambra': 0.05,
    'Delta': 0.04,
    'Edo': 0.04,
    'Others': 0.04
}

# Shop types distribution
SHOP_TYPES = {
    'Kiosk': 0.40,           # Small roadside shops
    'Provision Store': 0.30,  # Medium-sized stores
    'Mini Mart': 0.15,        # Larger retail outlets
    'Market Stall': 0.10,     # Market-based retailers
    'Superette': 0.05         # Small supermarkets
}

# Urbanization levels
URBANIZATION = {
    'Urban': 0.45,
    'Peri-Urban': 0.35,
    'Rural': 0.20
}

# Gender distribution (OmniRetail targets women entrepreneurs)
GENDER_DISTRIBUTION = {
    'Female': 0.62,  # 62% women (financial inclusion focus)
    'Male': 0.38
}

# ============================================================================
# CREDIT BEHAVIOR DISTRIBUTION
# ============================================================================

# Credit segments (matches OmniRetail's near-zero default rate)
CREDIT_SEGMENTS = {
    'Excellent': {
        'proportion': 0.35,
        'default_rate': 0.002,  # 0.2% default
        'avg_order_value': (8000, 25000),
        'order_frequency': (15, 30),  # Orders per year
        'payment_timeliness': (0, 3),  # Days late (0-3 days)
    },
    'Good': {
        'proportion': 0.30,
        'default_rate': 0.008,  # 0.8% default
        'avg_order_value': (5000, 18000),
        'order_frequency': (10, 20),
        'payment_timeliness': (0, 7),  # 0-7 days late
    },
    'Fair': {
        'proportion': 0.20,
        'default_rate': 0.025,  # 2.5% default
        'avg_order_value': (3000, 12000),
        'order_frequency': (6, 15),
        'payment_timeliness': (3, 14),  # 3-14 days late
    },
    'Moderate Risk': {
        'proportion': 0.10,
        'default_rate': 0.06,  # 6% default
        'avg_order_value': (2000, 8000),
        'order_frequency': (4, 10),
        'payment_timeliness': (7, 21),  # 7-21 days late
    },
    'High Risk': {
        'proportion': 0.05,
        'default_rate': 0.15,  # 15% default
        'avg_order_value': (1000, 5000),
        'order_frequency': (2, 6),
        'payment_timeliness': (14, 45),  # 14-45 days late
    }
}

# ============================================================================
# TRANSACTION PARAMETERS
# ============================================================================

TRANSACTION_MONTHS = 12  # Generate 12 months of transaction history
START_DATE = '2024-01-01'
END_DATE = '2024-12-31'

# Product categories available on OmniRetail
PRODUCT_CATEGORIES = [
    'Beverages', 'Confectionery', 'Dairy', 'Frozen Foods',
    'Grains & Pasta', 'Personal Care', 'Household Items',
    'Snacks', 'Cooking Ingredients', 'Baby Products'
]

# Manufacturers/Suppliers
MANUFACTURERS = [
    'Nestle', 'Unilever', 'Procter & Gamble', 'Coca-Cola',
    'Dangote', 'Flour Mills', 'Nigerian Breweries', 'PZ Cussons',
    'Cadbury', 'Chi Limited'
]

# ============================================================================
# ALTERNATIVE DATA PARAMETERS
# ============================================================================

# Mobile money transaction patterns
MOBILE_MONEY_PATTERNS = {
    'Heavy User': {'monthly_txns': (20, 40), 'proportion': 0.25},
    'Regular User': {'monthly_txns': (10, 20), 'proportion': 0.45},
    'Light User': {'monthly_txns': (3, 10), 'proportion': 0.20},
    'Non-User': {'monthly_txns': (0, 2), 'proportion': 0.10}
}

# ============================================================================
# CREDIT LIMITS (in Naira)
# ============================================================================

CREDIT_LIMITS = {
    'Excellent': (400000, 750000),     # ₦400K - ₦750K
    'Good': (250000, 500000),          # ₦250K - ₦500K
    'Fair': (150000, 350000),          # ₦150K - ₦350K
    'Moderate Risk': (50000, 200000),  # ₦50K - ₦200K
    'High Risk': (20000, 100000)       # ₦20K - ₦100K
}

# ============================================================================
# FILE PATHS
# ============================================================================

OUTPUT_DIR = 'synthetic_data/'
RETAILERS_FILE = OUTPUT_DIR + 'retailers.csv'
TRANSACTIONS_FILE = OUTPUT_DIR + 'transactions.csv'
REPAYMENTS_FILE = OUTPUT_DIR + 'repayments.csv'
FEATURES_FILE = OUTPUT_DIR + 'ml_features.csv'