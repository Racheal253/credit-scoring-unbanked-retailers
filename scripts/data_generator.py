"""
OmniRetail Synthetic Data Generator - Main Script
Generates realistic retailer, transaction, and repayment data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random
import os
from config import *

# Initialize
fake = Faker('en_NG')  # Nigerian locale
Faker.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("OMNIRETAIL SYNTHETIC DATA GENERATOR")
print("=" * 70)
print(f"Generating data for {NUM_RETAILERS:,} retailers...")
print(f"Transaction period: {START_DATE} to {END_DATE}")
print()

# ============================================================================
# PART 1: GENERATE RETAILER PROFILES
# ============================================================================

def generate_gps_coordinates(state):
    """Generate realistic GPS coordinates for Nigerian states"""
    # Approximate coordinates for major Nigerian states
    state_coords = {
        'Lagos': (6.5244, 3.3792),
        'Kano': (12.0022, 8.5920),
        'Rivers': (4.8156, 7.0498),
        'Oyo': (7.8500, 3.9300),
        'Kaduna': (10.5105, 7.4165),
        'FCT': (9.0765, 7.3986),  # Abuja
        'Ogun': (6.9082, 3.3470),
        'Anambra': (6.2209, 7.0596),
        'Delta': (5.6803, 5.9080),
        'Edo': (6.3350, 5.6037),
        'Others': (9.0820, 8.6753)
    }
    
    base_lat, base_lon = state_coords.get(state, (9.0820, 8.6753))
    
    # Add random variation (within ~50km)
    lat = base_lat + np.random.uniform(-0.5, 0.5)
    lon = base_lon + np.random.uniform(-0.5, 0.5)
    
    return round(lat, 6), round(lon, 6)

def assign_credit_segment():
    """Assign credit segment based on configured proportions"""
    segments = list(CREDIT_SEGMENTS.keys())
    proportions = [CREDIT_SEGMENTS[seg]['proportion'] for seg in segments]
    return np.random.choice(segments, p=proportions)

def generate_phone_number():
    """Generate Nigerian phone number"""
    prefixes = ['0803', '0806', '0810', '0813', '0814', '0816', '0703', '0706', '0803', '0805', '0807', '0811', '0815', '0905', '0907']
    prefix = random.choice(prefixes)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return prefix + suffix

print("Generating retailer profiles...")

retailers_data = []

for i in range(NUM_RETAILERS):
    # Assign credit segment first (determines behavior)
    credit_segment = assign_credit_segment()
    segment_params = CREDIT_SEGMENTS[credit_segment]
    
    # Will this retailer default?
    is_defaulter = np.random.random() < segment_params['default_rate']
    
    # Basic info
    retailer_id = f"RTL_{str(i+1).zfill(6)}"
    
    # Gender
    gender = np.random.choice(
        list(GENDER_DISTRIBUTION.keys()),
        p=list(GENDER_DISTRIBUTION.values())
    )
    
    # Name based on gender
    if gender == 'Female':
        owner_name = fake.name_female()
    else:
        owner_name = fake.name_male()
    
    # Business name (often owner's name + store type)
    business_name = f"{owner_name.split()[0]}'s {random.choice(['Store', 'Shop', 'Mart', 'Provisions', 'Ventures'])}"
    
    # Location
    state = np.random.choice(
        list(STATES.keys()),
        p=list(STATES.values())
    )
    
    urbanization = np.random.choice(
        list(URBANIZATION.keys()),
        p=list(URBANIZATION.values())
    )
    
    latitude, longitude = generate_gps_coordinates(state)
    
    # Shop characteristics
    shop_type = np.random.choice(
        list(SHOP_TYPES.keys()),
        p=list(SHOP_TYPES.values())
    )
    
    # Age and experience
    owner_age = np.random.randint(22, 65)
    years_in_business = min(np.random.randint(1, 25), owner_age - 20)
    months_in_business = years_in_business * 12 + np.random.randint(0, 12)
    
    # Employees (correlated with shop type)
    if shop_type in ['Kiosk', 'Market Stall']:
        num_employees = np.random.choice([1, 2], p=[0.8, 0.2])
    elif shop_type == 'Provision Store':
        num_employees = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
    else:
        num_employees = np.random.choice([2, 3, 4, 5], p=[0.3, 0.4, 0.2, 0.1])
    
    # Registration status (more formal in urban areas)
    if urbanization == 'Urban':
        has_business_registration = np.random.choice([True, False], p=[0.7, 0.3])
    else:
        has_business_registration = np.random.choice([True, False], p=[0.3, 0.7])
    
    # Mobile money usage pattern
    mm_pattern = np.random.choice(
        list(MOBILE_MONEY_PATTERNS.keys()),
        p=[MOBILE_MONEY_PATTERNS[k]['proportion'] for k in MOBILE_MONEY_PATTERNS.keys()]
    )
    
    monthly_mm_txns = np.random.randint(
        *MOBILE_MONEY_PATTERNS[mm_pattern]['monthly_txns']
    )
    
    # Credit details
    credit_limit_range = CREDIT_LIMITS[credit_segment]
    credit_limit = np.random.randint(*credit_limit_range)
    
    # Onboarding date (between 6-18 months ago for established history)
    onboarding_days_ago = np.random.randint(180, 540)  # 6-18 months
    onboarding_date = datetime.now() - timedelta(days=onboarding_days_ago)
    
    # Contact info
    phone_number = generate_phone_number()
    email = f"{owner_name.lower().replace(' ', '.')}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
    
    retailer = {
        'retailer_id': retailer_id,
        'business_name': business_name,
        'owner_name': owner_name,
        'owner_gender': gender,
        'owner_age': owner_age,
        'phone_number': phone_number,
        'email': email,
        'shop_type': shop_type,
        'state': state,
        'urbanization_level': urbanization,
        'latitude': latitude,
        'longitude': longitude,
        'years_in_business': years_in_business,
        'months_in_business': months_in_business,
        'num_employees': num_employees,
        'has_business_registration': has_business_registration,
        'mobile_money_pattern': mm_pattern,
        'monthly_mobile_money_txns': monthly_mm_txns,
        'credit_segment': credit_segment,
        'credit_limit': credit_limit,
        'is_defaulter': is_defaulter,
        'onboarding_date': onboarding_date.strftime('%Y-%m-%d'),
        'account_status': 'Active'
    }
    
    retailers_data.append(retailer)
    
    if (i + 1) % 1000 == 0:
        print(f"  Generated {i+1:,} retailers...")

retailers_df = pd.DataFrame(retailers_data)

print(f"✓ Generated {len(retailers_df):,} retailer profiles")
print()

# ============================================================================
# PART 2: GENERATE TRANSACTIONS
# ============================================================================

print("Generating transaction history...")

transactions_data = []
transaction_id_counter = 1

start_dt = datetime.strptime(START_DATE, '%Y-%m-%d')
end_dt = datetime.strptime(END_DATE, '%Y-%m-%d')

for idx, retailer in retailers_df.iterrows():
    credit_segment = retailer['credit_segment']
    segment_params = CREDIT_SEGMENTS[credit_segment]
    
    # How many orders will this retailer place in 12 months?
    num_orders = np.random.randint(*segment_params['order_frequency'])
    
    # Average order value for this retailer
    avg_order_value = np.random.uniform(*segment_params['avg_order_value'])
    
    # Generate order dates (spread across 12 months)
    onboarding_dt = datetime.strptime(retailer['onboarding_date'], '%Y-%m-%d')
    
    # Earliest transaction is 7 days after onboarding
    first_txn_date = max(onboarding_dt + timedelta(days=7), start_dt)
    
    # Generate random order dates
    days_range = (end_dt - first_txn_date).days
    if days_range <= 0:
        continue  # Skip if onboarded too recently
    
    order_days = sorted([
        first_txn_date + timedelta(days=np.random.randint(0, days_range))
        for _ in range(num_orders)
    ])
    
    for order_num, order_date in enumerate(order_days, 1):
        # Order amount (with some variation around average)
        order_amount = max(
            1000,  # Minimum order
            int(np.random.normal(avg_order_value, avg_order_value * 0.3))
        )
        
        # Ensure doesn't exceed credit limit
        order_amount = min(order_amount, retailer['credit_limit'])
        
        # Products in order (1-5 product categories)
        num_products = np.random.randint(1, 6)
        product_categories = random.sample(PRODUCT_CATEGORIES, num_products)
        
        # Manufacturers
        manufacturers = random.sample(MANUFACTURERS, min(num_products, 3))
        
        transaction = {
            'transaction_id': f"TXN_{str(transaction_id_counter).zfill(8)}",
            'retailer_id': retailer['retailer_id'],
            'order_date': order_date.strftime('%Y-%m-%d'),
            'order_amount': order_amount,
            'num_products': num_products,
            'product_categories': '|'.join(product_categories),
            'manufacturers': '|'.join(manufacturers),
            'payment_method': 'BNPL',  # Buy Now Pay Later
            'credit_used': order_amount,
            'order_number': order_num
        }
        
        transactions_data.append(transaction)
        transaction_id_counter += 1
    
    if (idx + 1) % 1000 == 0:
        print(f"  Generated transactions for {idx+1:,} retailers...")

transactions_df = pd.DataFrame(transactions_data)

print(f"✓ Generated {len(transactions_df):,} transactions")
print()

# ============================================================================
# PART 3: GENERATE REPAYMENT DATA
# ============================================================================

print("Generating repayment data...")

repayments_data = []

for idx, transaction in transactions_df.iterrows():
    retailer = retailers_df[
        retailers_df['retailer_id'] == transaction['retailer_id']
    ].iloc[0]
    
    credit_segment = retailer['credit_segment']
    segment_params = CREDIT_SEGMENTS[credit_segment]
    is_defaulter = retailer['is_defaulter']
    
    order_date = datetime.strptime(transaction['order_date'], '%Y-%m-%d')
    
    # Payment terms: typically 30 days
    due_date = order_date + timedelta(days=30)
    
    if is_defaulter:
        # Defaulters: either don't pay or pay very late
        defaulter_behavior = np.random.choice(['no_payment', 'very_late'], p=[0.6, 0.4])
        
        if defaulter_behavior == 'no_payment':
            # No payment - still outstanding
            payment_date = None
            payment_amount = 0
            days_late = (datetime.now() - due_date).days
            payment_status = 'Defaulted'
        else:
            # Very late payment (60-120 days late)
            days_late = np.random.randint(60, 120)
            payment_date = due_date + timedelta(days=days_late)
            
            # Might pay partial amount
            payment_amount = int(transaction['order_amount'] * np.random.uniform(0.5, 1.0))
            
            if payment_amount >= transaction['order_amount']:
                payment_status = 'Paid Late'
            else:
                payment_status = 'Partially Paid'
    else:
        # Good payers: pay within segment's typical range
        days_late = np.random.randint(*segment_params['payment_timeliness'])
        payment_date = due_date + timedelta(days=days_late)
        payment_amount = transaction['order_amount']
        
        if days_late == 0:
            payment_status = 'Paid On Time'
        elif days_late <= 7:
            payment_status = 'Paid (Slight Delay)'
        else:
            payment_status = 'Paid Late'
    
    repayment = {
        'repayment_id': f"REP_{str(idx+1).zfill(8)}",
        'transaction_id': transaction['transaction_id'],
        'retailer_id': transaction['retailer_id'],
        'order_date': transaction['order_date'],
        'due_date': due_date.strftime('%Y-%m-%d'),
        'payment_date': payment_date.strftime('%Y-%m-%d') if payment_date else None,
        'amount_due': transaction['order_amount'],
        'amount_paid': payment_amount,
        'days_late': days_late if payment_date else (datetime.now() - due_date).days,
        'payment_status': payment_status
    }
    
    repayments_data.append(repayment)
    
    if (idx + 1) % 5000 == 0:
        print(f"  Generated repayment records for {idx+1:,} transactions...")

repayments_df = pd.DataFrame(repayments_data)

print(f"✓ Generated {len(repayments_df):,} repayment records")
print()

# ============================================================================
# PART 4: FEATURE ENGINEERING FOR ML
# ============================================================================

print("Engineering features for ML...")

ml_features = []

for idx, retailer in retailers_df.iterrows():
    retailer_id = retailer['retailer_id']
    
    # Get all transactions for this retailer
    retailer_txns = transactions_df[transactions_df['retailer_id'] == retailer_id]
    retailer_payments = repayments_df[repayments_df['retailer_id'] == retailer_id]
    
    if len(retailer_txns) == 0:
        continue  # Skip if no transactions
    
    # ========================================================================
    # TRANSACTION-BASED FEATURES
    # ========================================================================
    
    total_orders = len(retailer_txns)
    total_order_value = retailer_txns['order_amount'].sum()
    avg_order_value = retailer_txns['order_amount'].mean()
    max_order_value = retailer_txns['order_amount'].max()
    min_order_value = retailer_txns['order_amount'].min()
    order_value_std = retailer_txns['order_amount'].std()
    
    # Order frequency
    if total_orders > 1:
        order_dates = pd.to_datetime(retailer_txns['order_date'])
        days_between_orders = order_dates.diff().dt.days.mean()
        orders_per_month = total_orders / 12
    else:
        days_between_orders = 365
        orders_per_month = total_orders / 12
    
    # Product diversity
    all_categories = '|'.join(retailer_txns['product_categories'].values)
    unique_categories = len(set(all_categories.split('|')))
    
    all_manufacturers = '|'.join(retailer_txns['manufacturers'].values)
    unique_manufacturers = len(set(all_manufacturers.split('|')))
    
    # Order growth trend (early orders vs. recent orders)
    if total_orders >= 4:
        early_orders = retailer_txns.iloc[:total_orders//2]
        recent_orders = retailer_txns.iloc[total_orders//2:]
        early_avg = early_orders['order_amount'].mean()
        recent_avg = recent_orders['order_amount'].mean()
        order_growth_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
    else:
        order_growth_rate = 0
    
    # ========================================================================
    # PAYMENT BEHAVIOR FEATURES
    # ========================================================================
    
    total_paid = retailer_payments['amount_paid'].sum()
    payment_rate = total_paid / total_order_value if total_order_value > 0 else 0
    
    # Payment timeliness
    avg_days_late = retailer_payments['days_late'].mean()
    max_days_late = retailer_payments['days_late'].max()
    
    on_time_payments = len(retailer_payments[retailer_payments['days_late'] <= 3])
    on_time_payment_rate = on_time_payments / total_orders if total_orders > 0 else 0
    
    defaulted_orders = len(retailer_payments[retailer_payments['payment_status'] == 'Defaulted'])
    default_rate = defaulted_orders / total_orders if total_orders > 0 else 0
    
    # ========================================================================
    # CREDIT UTILIZATION
    # ========================================================================
    
    credit_utilization = avg_order_value / retailer['credit_limit'] if retailer['credit_limit'] > 0 else 0
    
    # ========================================================================
    # ALTERNATIVE DATA FEATURES
    # ========================================================================
    
    # Mobile money (already in retailer profile)
    mobile_money_score = {
        'Heavy User': 1.0,
        'Regular User': 0.7,
        'Light User': 0.4,
        'Non-User': 0.1
    }.get(retailer['mobile_money_pattern'], 0.5)
    
    # Location stability (number of months at same location)
    location_stability_months = retailer['months_in_business']
    
    # Business formality score
    formality_score = 0
    if retailer['has_business_registration']:
        formality_score += 0.5
    if retailer['num_employees'] >= 2:
        formality_score += 0.3
    if retailer['shop_type'] in ['Mini Mart', 'Superette']:
        formality_score += 0.2
    
    # ========================================================================
    # DEMOGRAPHIC FEATURES
    # ========================================================================
    
    # Encode categorical variables
    gender_encoded = 1 if retailer['owner_gender'] == 'Female' else 0
    
    urbanization_encoded = {
        'Urban': 2,
        'Peri-Urban': 1,
        'Rural': 0
    }.get(retailer['urbanization_level'], 1)
    
    shop_type_encoded = {
        'Superette': 4,
        'Mini Mart': 3,
        'Provision Store': 2,
        'Market Stall': 1,
        'Kiosk': 0
    }.get(retailer['shop_type'], 2)
    
    # ========================================================================
    # TARGET VARIABLE
    # ========================================================================
    
    # Default if any payment is defaulted or payment rate < 80%
    is_default = 1 if (retailer['is_defaulter'] or payment_rate < 0.8) else 0
    
    # Credit score (we'll calculate this later, but include segment as proxy)
    credit_score_estimate = {
        'Excellent': np.random.randint(800, 851),
        'Good': np.random.randint(750, 800),
        'Fair': np.random.randint(700, 750),
        'Moderate Risk': np.random.randint(650, 700),
        'High Risk': np.random.randint(550, 650)
    }.get(retailer['credit_segment'], 700)
    
    # ========================================================================
    # COMPILE FEATURES
    # ========================================================================
    
    features = {
        'retailer_id': retailer_id,
        
        # Transaction features
        'total_orders': total_orders,
        'total_order_value': total_order_value,
        'avg_order_value': avg_order_value,
        'max_order_value': max_order_value,
        'min_order_value': min_order_value,
        'order_value_std': order_value_std,
        'days_between_orders': days_between_orders,
        'orders_per_month': orders_per_month,
        'unique_product_categories': unique_categories,
        'unique_manufacturers': unique_manufacturers,
        'order_growth_rate': order_growth_rate,
        
        # Payment features
        'payment_rate': payment_rate,
        'avg_days_late': avg_days_late,
        'max_days_late': max_days_late,
        'on_time_payment_rate': on_time_payment_rate,
        'default_rate': default_rate,
        
        # Credit features
        'credit_limit': retailer['credit_limit'],
        'credit_utilization': credit_utilization,
        
        # Alternative data
        'mobile_money_score': mobile_money_score,
        'monthly_mobile_money_txns': retailer['monthly_mobile_money_txns'],
        'location_stability_months': location_stability_months,
        'formality_score': formality_score,
        
        # Demographics
        'owner_age': retailer['owner_age'],
        'gender_encoded': gender_encoded,
        'years_in_business': retailer['years_in_business'],
        'num_employees': retailer['num_employees'],
        'urbanization_encoded': urbanization_encoded,
        'shop_type_encoded': shop_type_encoded,
        'has_business_registration': int(retailer['has_business_registration']),
        
        # Target
        'is_default': is_default,
        'credit_segment': retailer['credit_segment'],
        'credit_score_estimate': credit_score_estimate
    }
    
    ml_features.append(features)
    
    if (idx + 1) % 1000 == 0:
        print(f"  Engineered features for {idx+1:,} retailers...")

ml_features_df = pd.DataFrame(ml_features)

print(f"✓ Engineered {len(ml_features_df.columns)} features for {len(ml_features_df):,} retailers")
print()

# ============================================================================
# PART 5: SAVE ALL DATASETS
# ============================================================================

print("Saving datasets to CSV...")

retailers_df.to_csv(RETAILERS_FILE, index=False)
print(f"  ✓ Saved: {RETAILERS_FILE}")

transactions_df.to_csv(TRANSACTIONS_FILE, index=False)
print(f"  ✓ Saved: {TRANSACTIONS_FILE}")

repayments_df.to_csv(REPAYMENTS_FILE, index=False)
print(f"  ✓ Saved: {REPAYMENTS_FILE}")

ml_features_df.to_csv(FEATURES_FILE, index=False)
print(f"  ✓ Saved: {FEATURES_FILE}")

print()

# ============================================================================
# PART 6: GENERATE DATA SUMMARY STATISTICS
# ============================================================================

print("=" * 70)
print("DATA GENERATION SUMMARY")
print("=" * 70)
print()

print("RETAILERS:")
print(f"  Total retailers: {len(retailers_df):,}")
print(f"  Female-owned: {len(retailers_df[retailers_df['owner_gender']=='Female']):,} ({len(retailers_df[retailers_df['owner_gender']=='Female'])/len(retailers_df)*100:.1f}%)")
print(f"  Male-owned: {len(retailers_df[retailers_df['owner_gender']=='Male']):,} ({len(retailers_df[retailers_df['owner_gender']=='Male'])/len(retailers_df)*100:.1f}%)")
print()

print("CREDIT SEGMENTS:")
for segment in CREDIT_SEGMENTS.keys():
    count = len(retailers_df[retailers_df['credit_segment'] == segment])
    pct = count / len(retailers_df) * 100
    print(f"  {segment}: {count:,} ({pct:.1f}%)")
print()

print("GEOGRAPHIC DISTRIBUTION:")
top_states = retailers_df['state'].value_counts().head(5)
for state, count in top_states.items():
    pct = count / len(retailers_df) * 100
    print(f"  {state}: {count:,} ({pct:.1f}%)")
print()

print("TRANSACTIONS:")
print(f"  Total transactions: {len(transactions_df):,}")
print(f"  Total transaction value: ₦{transactions_df['order_amount'].sum():,.0f}")
print(f"  Average order value: ₦{transactions_df['order_amount'].mean():,.0f}")
print(f"  Average orders per retailer: {len(transactions_df)/len(retailers_df):.1f}")
print()

print("PAYMENT PERFORMANCE:")
paid_on_time = len(repayments_df[repayments_df['payment_status'].str.contains('On Time', na=False)])
defaulted = len(repayments_df[repayments_df['payment_status'] == 'Defaulted'])
print(f"  Paid on time: {paid_on_time:,} ({paid_on_time/len(repayments_df)*100:.1f}%)")
print(f"  Defaulted: {defaulted:,} ({defaulted/len(repayments_df)*100:.1f}%)")
print(f"  Average days late: {repayments_df['days_late'].mean():.1f} days")
print()

print("ML FEATURES:")
print(f"  Total feature records: {len(ml_features_df):,}")
print(f"  Number of features: {len(ml_features_df.columns)}")
print(f"  Default rate: {ml_features_df['is_default'].mean()*100:.2f}%")
print()

print("=" * 70)
print("DATA GENERATION COMPLETE!")
print("=" * 70)
print()
print("Next steps:")
print("1. Review the generated CSV files in the synthetic_data/ folder")
print("2. Upload to Microsoft Fabric Lakehouse")
print("3. Begin exploratory data analysis")
print("4. Train credit scoring models")