# ---------- QUBO -> Ising (Z) ----------
# x_i = (1 - Z_i)/2 ; x_i x_j = (1 - Z_i - Z_j + Z_iZ_j)/4
def qubo_to_ising(Q, q, n):
    J = np.zeros((n, n))
    h = np.zeros(n)
    const = 0.0
    for i in range(n):
        for j in range(i+1, n):
            Jij = Q[i, j] / 4.0
            J[i, j] = Jij
            h[i] += -Q[i, j] / 4.0
            h[j] += -Q[i, j] / 4.0
            const += Q[i, j] / 4.0
    for i in range(n):
        h[i] += -(Q[i, i] / 2.0) - (q[i] / 2.0)
        const += (Q[i, i] / 2.0) + (q[i] / 2.0)
    return J, h, const

# J, h, const_shift = qubo_to_ising(Q, q)

# ---------- Initial state with |x|=B (RANDOM) ----------
init_idx = rng.choice(n, size=B, replace=False)   # <-- requested change
init_bits = np.zeros(n, dtype=int)
init_bits[init_idx] = 1

# ---------- QAOA ansatz with XY mixer (ring) ----------
def build_qaoa_xy(n, P, J, h, init_bits):
    qc = QuantumCircuit(n, name="QAOA_XY")
    for i, b in enumerate(init_bits):
        if b == 1:
            qc.x(i)

    gammas = [Parameter(f"γ_{k}") for k in range(P)]
    betas  = [Parameter(f"β_{k}") for k in range(P)]

    ring_pairs = [(i, (i+1) % n) for i in range(n)]  # ring connectivity

    for k in range(P):
        γ = gammas[k]
        β = betas[k]
        # Cost: RZ(2γ h_i) + RZZ(2γ J_ij)
        for i in range(n):
            if abs(h[i]) > 1e-15:
                qc.rz(2.0 * γ * h[i], i)
        for i in range(n):
            for j in range(i+1, n):
                if abs(J[i, j]) > 1e-15:
                    qc.append(RZZGate(2.0 * γ * J[i, j]), [i, j])
        # XY mixer (preserves cardinality)
        for (i, j) in ring_pairs:
            qc.append(RXXGate(2.0 * β), [i, j])
            qc.append(RYYGate(2.0 * β), [i, j])
    return qc, gammas + betas

ansatz, theta_params = build_qaoa_xy(n, P_LAYERS, J, h, init_bits)

# ---------- Utilities ----------
def f_qubo(x):
    return float(x @ Q @ x + q @ x)

def bitstr_from_int(k, n):
    return np.array(list(np.binary_repr(k, width=n)), dtype=int)

def bitarray_from_qiskit_string(s):
    # Qiskit returns string little-endian (q_{n-1} ... q_0)
    return np.array(list(s[::-1]), dtype=int)

def bind_params(circ, mapping):
    """Terra compatibility: first try assign_parameters, if not available, bind_parameters."""
    try:
        return circ.assign_parameters(mapping, inplace=False)
    except Exception:
        try:
            return circ.bind_parameters(mapping)
        except Exception as e:
            raise RuntimeError(f"Could not assign parameters: {e}")

# Exact expectation via statevector (diagonal in computational basis)
def expectation_statevector(theta):
    bind = {p: float(t) for p, t in zip(theta_params, theta)}
    circ_b = bind_params(ansatz, bind)
    sv = Statevector.from_instruction(circ_b)
    amps = sv.data
    exp = 0.0
    for idx, amp in enumerate(amps):
        p = (amp.conjugate() * amp).real
        if p < 1e-16:
            continue
        x = bitstr_from_int(idx, n)
        if x.sum() != B:  # robustness (XY should preserve it)
            continue
        exp += p * f_qubo(x)
    return exp

# ---------- Optimization with energy trace ----------
qaoa_trace = []

def objective_with_trace(th):
    val = expectation_statevector(th)
    qaoa_trace.append(val)
    return val

try:
    from scipy.optimize import minimize
    use_scipy = True
except Exception as e:
    print(f"[Warning] SciPy not available ({e}). Random search will be used.")
    use_scipy = False

def random_theta():
    return np.concatenate([
        rng.uniform(0.0, 2.0*np.pi, size=P_LAYERS),  # gammas
        rng.uniform(0.0, 2.0*np.pi, size=P_LAYERS),  # betas
    ])

t0_opt = time.perf_counter()
if use_scipy:
    best_val, best_theta = np.inf, None
    for _ in range(5):  # light multi-start
        x0 = random_theta()
        res = minimize(objective_with_trace, x0, method="COBYLA",
                       options={"maxiter": 250, "rhobeg": 0.5})
        if res.fun < best_val:
            best_val, best_theta = res.fun, res.x
else:
    best_val, best_theta = np.inf, None
    for _ in range(100):
        th = random_theta()
        val = objective_with_trace(th)
        if val < best_val:
            best_val, best_theta = val, th
t1_opt = time.perf_counter()

print(f"\n[QAOA] Best estimated expectation: {best_val:.6f}")
print(f"[QAOA] θ* = {best_theta}")

# ---------- Sampling and selection ----------
meas_qc = bind_params(ansatz, {p: float(t) for p, t in zip(theta_params, best_theta)}).copy()
meas_qc.measure_all()

backend = AerSimulator()
tqc = transpile(meas_qc, backend, optimization_level=1, seed_transpiler=SEED)

t0_samp = time.perf_counter()
res = backend.run(tqc, shots=SHOTS, seed_simulator=SEED).result()
t1_samp = time.perf_counter()

counts = res.get_counts()

# Filter |x|=B and choose best cost
cands = []
for s, c in counts.items():
    x = bitarray_from_qiskit_string(s)
    if x.sum() == B:
        cands.append((s, c, f_qubo(x)))

if not cands:
    raise RuntimeError("No bitstrings with cardinality B were observed (very rare with XY mixer).")

s_best, c_best, fx_best = min(cands, key=lambda t: t[2])
x_best = bitarray_from_qiskit_string(s_best)
sel_idx = np.where(x_best == 1)[0]
sel_tickers = [TICKERS[i] for i in sel_idx]

print("\n[QAOA-XY Result]")
print(f"Bitstring (little-endian): {s_best}  (freq {c_best}/{SHOTS})")
print(f"Selected ({len(sel_idx)} = B): {sel_tickers}")
print(f"f(x*) = {fx_best:.6f}")

# Metrics (equal weights)
w = np.zeros(n)
w[sel_idx] = 1.0 / B
mu_day = float(mu @ w)
var_day = float(w @ Sigma @ w)
mu_ann = 252 * mu_day
std_ann = np.sqrt(252 * var_day)
print("\n[Approx. Metrics]")
print(f"Expected annual return ≈ {mu_ann:.2%}")
print(f"Annual volatility ≈ {std_ann:.2%}")