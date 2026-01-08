"""
Portfolio QUBO Preparation Utilities

Provides functions to prepare portfolio optimization problems in QUBO format
from historical stock price data downloaded via Yahoo Finance.

Functions
---------
prepare_portfolio_qubo : Download data and formulate QUBO problem
"""

# Standard library
from typing import List, Dict, Any
from datetime import datetime
import warnings

# Third-party libraries
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.covariance import LedoitWolf


# ---------- Main Function ----------

def prepare_portfolio_qubo(
    tickers: List[str],
    start_date: str,
    end_date: str,
    B: int,
    lambda_param: float = 5.0
) -> Dict[str, Any]:
    """
    Prepare portfolio optimization QUBO problem from historical stock data.

    Downloads historical stock prices from Yahoo Finance, calculates returns,
    estimates covariance matrix using Ledoit-Wolf shrinkage, and formulates
    the QUBO problem for quantum/classical optimization.

    Parameters
    ----------
    tickers : List[str]
        List of stock ticker symbols (e.g., ['NVDA', 'MSFT', 'AAPL']).
    start_date : str
        Start date in format 'YYYY-MM-DD' (e.g., '2020-01-01').
    end_date : str
        End date in format 'YYYY-MM-DD' (e.g., '2023-12-31').
    B : int
        Cardinality constraint - number of assets to select in portfolio.
        Must be positive and <= len(tickers).
    lambda_param : float, optional
        Risk aversion parameter. Default is 5.0.
        - lambda < 1: Aggressive (prioritize returns)
        - lambda = 1: Balanced
        - lambda = 5: Conservative (prioritize risk minimization)
        - lambda > 10: Very conservative

    Returns
    -------
    dict
        Dictionary containing:
        - 'Q' : np.ndarray (n, n) - QUBO quadratic matrix
        - 'q' : np.ndarray (n,) - QUBO linear vector
        - 'mu' : np.ndarray (n,) - Expected daily returns
        - 'Sigma' : np.ndarray (n, n) - Daily covariance matrix (Ledoit-Wolf)
        - 'B' : int - Cardinality constraint
        - 'tickers' : List[str] - Asset ticker symbols
        - 'lambda_param' : float - Risk aversion parameter
        - 'date_range' : tuple - (start_date, end_date)
        - 'returns' : pd.DataFrame - Daily log returns
        - 'metadata' : dict - Additional information (shrinkage, dates, etc.)

    Raises
    ------
    ValueError
        If B <= 0 or B > len(tickers)
        If tickers list is empty
        If date format is invalid
        If lambda_param <= 0
    RuntimeError
        If data download fails
        If insufficient data is available

    Examples
    --------
    >>> data = prepare_portfolio_qubo(
    ...     tickers=['NVDA', 'MSFT', 'AAPL', 'AMZN'],
    ...     start_date='2020-01-01',
    ...     end_date='2023-12-31',
    ...     B=2,
    ...     lambda_param=5.0
    ... )
    >>> print(data['Q'].shape)
    (4, 4)
    >>> print(data['tickers'])
    ['NVDA', 'MSFT', 'AAPL', 'AMZN']
    >>> print(f"Trading days: {data['metadata']['num_trading_days']}")

    Notes
    -----
    The QUBO formulation follows:
        Q = lambda * B^2 * Sigma
        q = -(1/B) * mu
    where Sigma is estimated using Ledoit-Wolf shrinkage for stability.
    """
    # ========== Step 1: Input Validation ==========

    # Validate tickers
    if not tickers or len(tickers) == 0:
        raise ValueError("tickers list cannot be empty")

    # Validate B
    if B <= 0:
        raise ValueError(f"B must be positive, got {B}")
    if B > len(tickers):
        raise ValueError(f"B ({B}) cannot exceed number of tickers ({len(tickers)})")

    # Validate lambda_param
    if lambda_param <= 0:
        raise ValueError(f"lambda_param must be positive, got {lambda_param}")

    # Validate date format
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use 'YYYY-MM-DD': {e}") from e

    # ========== Step 2: Download Price Data ==========

    try:
        # Suppress yfinance progress output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw_data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False
            )

        if raw_data.empty:
            raise RuntimeError("No data downloaded. Check tickers and date range.")

        # Extract adjusted closing prices
        if len(tickers) == 1:
            # Single ticker case
            if 'Adj Close' in raw_data.columns:
                data = raw_data[['Adj Close']].copy()
                data.columns = tickers
            else:
                data = raw_data[['Close']].copy()
                data.columns = tickers
        else:
            # Multiple tickers case - handle MultiIndex
            if isinstance(raw_data.columns, pd.MultiIndex):
                if 'Adj Close' in raw_data.columns.get_level_values(0):
                    data = raw_data.xs('Adj Close', axis=1, level=0)
                else:
                    data = raw_data.xs('Close', axis=1, level=0)
            else:
                data = raw_data.copy()

        # Ensure DataFrame format
        if not isinstance(data, pd.DataFrame):
            data = data.to_frame()

        # Verify all tickers present
        missing_tickers = set(tickers) - set(data.columns)
        if missing_tickers:
            raise RuntimeError(f"Failed to download data for tickers: {missing_tickers}")

    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Data download failed: {e}") from e

    # ========== Step 3: Data Preprocessing ==========

    # Check for missing values
    if data.isnull().sum().sum() > 0:
        # Modern pandas approach (avoids FutureWarning)
        data = data.ffill().bfill()

        # Verify no missing values remain
        if data.isnull().sum().sum() > 0:
            raise RuntimeError("Unable to fill all missing values in price data")

    # Check for invalid prices
    if (data <= 0).sum().sum() > 0:
        raise RuntimeError("Zero or negative prices detected in data")

    # Verify sufficient data
    if len(data) < 30:  # Minimum 30 trading days for meaningful statistics
        raise RuntimeError(
            f"Insufficient data: only {len(data)} trading days available. "
            "Need at least 30 days."
        )

    # ========== Step 4: Calculate Log Returns ==========

    # Calculate daily log returns
    returns = np.log(data / data.shift(1)).dropna()
    
    # Store actual date range
    actual_start = returns.index[0].strftime('%Y-%m-%d')
    actual_end = returns.index[-1].strftime('%Y-%m-%d')
    num_trading_days = len(returns)

    # ========== Step 5: Covariance Estimation ==========

    # Sample covariance (for comparison)
    Sigma_sample = returns.cov().values

    # Ledoit-Wolf shrinkage estimator
    lw = LedoitWolf()
    Sigma_lw = lw.fit(returns).covariance_

    # Extract shrinkage intensity
    shrinkage_intensity = lw.shrinkage_

    # Calculate condition numbers for metadata
    cond_sample = np.linalg.cond(Sigma_sample)
    cond_lw = np.linalg.cond(Sigma_lw)

    # Use Ledoit-Wolf estimate
    Sigma = Sigma_lw
    mu = returns.mean().values

    # ========== Step 6: QUBO Formulation ==========

    # Construct QUBO matrices
    Q = lambda_param * (B ** 2) * Sigma
    q = -(1.0 / B) * mu

    # Check Q matrix symmetry
    is_symmetric = np.allclose(Q, Q.T)

    # Validate QUBO construction
    if not is_symmetric:
        warnings.warn("QUBO matrix Q is not symmetric. Symmetrizing...")
        Q = (Q + Q.T) / 2.0

    # ========== Step 7: Build Metadata ==========

    metadata = {
        'shrinkage_intensity': float(shrinkage_intensity),
        'num_trading_days': int(num_trading_days),
        'actual_start_date': actual_start,
        'actual_end_date': actual_end,
        'condition_number_sample': float(cond_sample),
        'condition_number_lw': float(cond_lw),
        'download_timestamp': datetime.now().isoformat(),
        'n_assets': len(tickers),
        'Q_is_symmetric': bool(is_symmetric)
    }

    # ========== Step 8: Return Dictionary ==========

    return {
        'Q': Q,
        'q': q,
        'mu': mu,
        'Sigma': Sigma,
        'B': B,
        'tickers': tickers,
        'lambda_param': lambda_param,
        'date_range': (start_date, end_date),
        'returns': returns,
        'metadata': metadata
    }
