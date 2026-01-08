"""
Example usage of the portfolio QUBO preparation function.

This script demonstrates how to use the prepare_portfolio_qubo function
to prepare portfolio optimization data from Yahoo Finance.
"""

from portfolio_qubo_prep import prepare_portfolio_qubo

# Example configuration
TICKERS = [
    'NVDA', 'MSFT', 'AAPL', 'AMZN', 'META', 'AVGO', 'GOOGL', 'TSLA',
    'JPM', 'V', 'MA', 'XOM', 'JNJ', 'UNH', 'PG', 'WMT', 'MS', 'KO',
    'CAT', 'VZ', 'TMO'
]

START_DATE = '2020-01-01'
END_DATE = '2025-12-31'
B = 4  # Cardinality: number of assets to select

# Prepare QUBO data
print("Preparing portfolio QUBO data...")
data = prepare_portfolio_qubo(
    tickers=TICKERS,
    start_date=START_DATE,
    end_date=END_DATE,
    B=B,
    lambda_param=5.0
)

# Display results
print(f"\n{'='*60}")
print("QUBO Data Preparation Complete")
print(f"{'='*60}\n")

print(f"Number of assets: {len(data['tickers'])}")
print(f"Cardinality (B): {data['B']}")
print(f"Risk aversion (λ): {data['lambda_param']}")
print(f"\nDate range: {data['date_range'][0]} to {data['date_range'][1]}")
print(f"Actual dates: {data['metadata']['actual_start_date']} to {data['metadata']['actual_end_date']}")
print(f"Trading days: {data['metadata']['num_trading_days']}")

print(f"\n{'─'*60}")
print("QUBO Matrices")
print(f"{'─'*60}")
print(f"Q matrix shape: {data['Q'].shape}")
print(f"Q matrix range: [{data['Q'].min():.6f}, {data['Q'].max():.6f}]")
print(f"Q matrix is symmetric: {data['metadata']['Q_is_symmetric']} {'✓' if data['metadata']['Q_is_symmetric'] else '✗'}")
print(f"\nq vector shape: {data['q'].shape}")
print(f"q vector range: [{data['q'].min():.6f}, {data['q'].max():.6f}]")

print(f"\n{'─'*60}")
print("Covariance Estimation")
print(f"{'─'*60}")
print(f"Ledoit-Wolf shrinkage intensity: {data['metadata']['shrinkage_intensity']:.4f}")
print(f"Condition number (sample): {data['metadata']['condition_number_sample']:.2e}")
print(f"Condition number (Ledoit-Wolf): {data['metadata']['condition_number_lw']:.2e}")
print(f"Improvement factor: {data['metadata']['condition_number_sample']/data['metadata']['condition_number_lw']:.2f}x")

print(f"\n{'─'*60}")
print("Returns Statistics")
print(f"{'─'*60}")
print(f"Mean daily return: {data['mu'].mean():.6f}")
print(f"Std daily return: {data['mu'].std():.6f}")
print(f"Returns dataframe shape: {data['returns'].shape}")

print(f"\n{'='*60}")
print("Ready for optimization!")
print(f"{'='*60}\n")

# Show how to access QUBO matrices for optimization
Q = data['Q']
q = data['q']
print(f"Access QUBO matrices: Q.shape = {Q.shape}, q.shape = {q.shape}")

mu = data['mu']
Sigma = data['Sigma']
B = int(data['B'])
TICKERS = list(data['tickers'])
n = len(TICKERS)

print(f"  n = {n} assets")
print(f"  B = {B} cardinality")
print(f"  Q shape: {Q.shape}")
print(f"  q shape: {q.shape}")