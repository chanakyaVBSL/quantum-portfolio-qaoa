 # 🧠 Quantum Portfolio Optimization — October 19–25, 2025

## 📘 Introduction
**Topic:** Introduction to QAOA and Portfolio Optimization

### Objectives
1. Understand what a **QUBO problem** and the **QAOA algorithm** are.  
2. Study the difference between an **X-mixer** and an **XY-mixer**.  
3. Understand the financial components: **mean returns**, **covariance matrix**, and **Ledoit–Wolf shrinkage**.

---

## 💻 Code to Implement

1. **Import close prices** with `yfinance` for 10 assets:  
   `NVDA`, `MSFT`, `AAPL`, `AMZN`, `META`, `AVGO`, `GOOGL`, `TSLA`, `BRK-B`, `WMT`  
   *(1-day time frame)*    @cometta interested

2. **Calculate** mean returns and covariance matrix.    @cometta interested
3. **Implement** a **Ledoit–Wolf function** for the covariance matrix.  
4. **Build the QAOA code** using the 10 assets and set **B = 5**.

---

## 🧪 Experiments to Run

Return the **Risk**, **Return**, and **Sharpe Ratio**.  
Also, **plot** the following:
- **Energy values** (to observe convergence)
- **QAOA result histogram**

### Experiment Ideas
1. Vary the **QAOA depth** `p = 1, 2, 3, …`  
2. Investigate the effect of changing the **B value**.  
3. Study different values of **λ (lambda)** — the risk-aversion factor.  
4. Compare **different optimizers** to see which performs best:
   - `COBYLA`
   - `SPSA`
   - `Nelder-Mead`
   - `L-BFGS-B`
   - `ADAM`
   - `Gradient Descent`
   - `P-BFGS`
   - `QN-SPSA (Qiskit Runtime)`

---

📅 **Week:** October 19–25, 2025  
🚀 **Goal:** Understand QAOA, formulate a financial QUBO, and perform experiments on quantum optimization of portfolios.
