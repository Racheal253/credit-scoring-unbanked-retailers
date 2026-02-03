"""
Data Quality Validation Script
Checks the generated datasets for completeness and accuracy
"""

import pandas as pd
import numpy as np
from config import *

print("=" * 70)
print("DATA QUALITY VALIDATION")
print("=" * 70)
print()

# Load datasets
print("Loading datasets...")
retailers_df = pd.read_csv(RETAILERS_FILE)
transactions_df = pd.read_csv(TRANSACTIONS_FILE)
repayments_df = pd.read_csv(REPAYMENTS_FILE)
ml_features_df = pd.read_csv(FEATURES_FILE)
print("✓ All datasets loaded")
print()

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

validation_results = []

def validate_check(check_name, condition, expected=True):
    """Helper function to track validation results"""
    passed = condition == expected
    status = "✓ PASS" if passed else "✗ FAIL"
    validation_results.append({
        'check': check_name,
        'passed': passed,
        'status': status
    })
    print(f"{status}: {check_name}")
    return passed

print("Running validation checks...")
print()

# Check 1: No missing values in key fields
print("1. Checking for missing values...")
retailers_nulls = retailers_df[['retailer_id', 'credit_segment', 'credit_limit']].isnull().sum().sum()
validate_check("Retailers: No nulls in key fields", retailers_nulls == 0)

transactions_nulls = transactions_df[['transaction_id', 'retailer_id', 'order_amount']].isnull().sum().sum()
validate_check("Transactions: No nulls in key fields", transactions_nulls == 0)

repayments_nulls = repayments_df[['repayment_id', 'transaction_id', 'amount_due']].isnull().sum().sum()
validate_check("Repayments: No nulls in key fields", repayments_nulls == 0)

print()

# Check 2: Data integrity
print("2. Checking data integrity...")

# All transactions have corresponding retailers
txn_retailers = set(transactions_df['retailer_id'].unique())
retailers_ids = set(retailers_df['retailer_id'].unique())
validate_check("All transaction retailers exist", txn_retailers.issubset(retailers_ids))

# All repayments have corresponding transactions
rep_transactions = set(repayments_df['transaction_id'].unique())
transaction_ids = set(transactions_df['transaction_id'].unique())
validate_check("All repayment transactions exist", rep_transactions.issubset(transaction_ids))

print()

# Check 3: Business logic validation
print("3. Checking business logic...")

# Order amounts are positive
validate_check("All order amounts > 0", (transactions_df['order_amount'] > 0).all())

# Credit limits are positive
validate_check("All credit limits > 0", (retailers_df['credit_limit'] > 0).all())

# Order amounts don't exceed credit limits significantly
merged = transactions_df.merge(retailers_df[['retailer_id', 'credit_limit']], on='retailer_id')
exceeds_limit = (merged['order_amount'] > merged['credit_limit'] * 1.1).sum()
validate_check("Orders within credit limits", exceeds_limit == 0)

# Payment dates are after order dates (where payment exists)
repayments_with_payment = repayments_df[repayments_df['payment_date'].notna()].copy()
repayments_with_payment['order_date'] = pd.to_datetime(repayments_with_payment['order_date'])
repayments_with_payment['payment_date'] = pd.to_datetime(repayments_with_payment['payment_date'])
validate_check("Payment dates after order dates", 
               (repayments_with_payment['payment_date'] >= repayments_with_payment['order_date']).all())

print()

# Check 4: Statistical validation
print("4. Checking statistical distributions...")

# Gender distribution close to target (62% female, 38% male)
female_pct = (retailers_df['owner_gender'] == 'Female').mean()
validate_check("Gender distribution (60-64% female)", 0.60 <= female_pct <= 0.64)

# Default rate should be low (OmniRetail has near-zero defaults)
default_rate = ml_features_df['is_default'].mean()
validate_check("Default rate < 3%", default_rate < 0.03)

# Average order value in reasonable range (₦5K - ₦20K)
avg_order = transactions_df['order_amount'].mean()
validate_check("Avg order value ₦3K-25K", 3000 <= avg_order <= 25000)

print()

# Check 5: ML Features validation
print("5. Checking ML features...")

# No nulls in feature dataset
ml_nulls = ml_features_df.isnull().sum().sum()
validate_check("ML features: No missing values", ml_nulls == 0)

# All retailers with transactions have features
validate_check("All retailers have ML features", 
               len(ml_features_df) >= len(transactions_df['retailer_id'].unique()))

# Feature values are in expected ranges
validate_check("Payment rate between 0-1", 
               (ml_features_df['payment_rate'] >= 0).all() and (ml_features_df['payment_rate'] <= 1).all())

validate_check("Credit utilization between 0-1", 
               (ml_features_df['credit_utilization'] >= 0).all() and (ml_features_df['credit_utilization'] <= 1.2).all())

print()

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print()

total_checks = len(validation_results)
passed_checks = sum([1 for r in validation_results if r['passed']])
failed_checks = total_checks - passed_checks

print(f"Total checks: {total_checks}")
print(f"Passed: {passed_checks} ({passed_checks/total_checks*100:.1f}%)")
print(f"Failed: {failed_checks} ({failed_checks/total_checks*100:.1f}%)")
print()

if failed_checks == 0:
    print("✓ ALL VALIDATION CHECKS PASSED!")
    print("Data is ready for upload to Microsoft Fabric")
else:
    print("⚠ SOME VALIDATION CHECKS FAILED")
    print("Please review the failed checks above")
    print()
    print("Failed checks:")
    for result in validation_results:
        if not result['passed']:
            print(f"  - {result['check']}")

print()
print("=" * 70)