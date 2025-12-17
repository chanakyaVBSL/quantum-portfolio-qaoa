import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import RZZGate, RXXGate, RYYGate
from qiskit.quantum_info import Statevector


# ---------- QUBO -> Ising (Z) ----------
# x_i = (1 - Z_i)/2 ; x_i x_j = (1 - Z_i - Z_j + Z_iZ_j)/4

def qubo_to_ising(Q: np.ndarray, q: np.ndarray, n: int):
    """
    Convert QUBO to Ising Hamiltonian.

    Parameters
    ----------
    Q : np.ndarray (n, n)
        Symmetric QUBO interaction matrix.
    q : np.ndarray (n,)
        Linear QUBO coefficient vector.
    n : int
        Number of variables / qubits.
    """
    J = np.zeros((n, n))
    h = np.zeros(n)
    const = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            Jij = Q[i, j] / 4.0
            J[i, j] = Jij
            h[i] += -Q[i, j] / 4.0
            h[j] += -Q[i, j] / 4.0
            const += Q[i, j] / 4.0

    for i in range(n):
        h[i] += -(Q[i, i] / 2.0) - (q[i] / 2.0)
        const += (Q[i, i] / 2.0) + (q[i] / 2.0)

    return J, h, const


# ---------- QAOA ansatz with XY mixer (ring) ----------

def build_qaoa_xy(n: int, P: int, J: np.ndarray, h: np.ndarray, init_bits):
    """
    Build parameterized QAOA-XY circuit.

    Parameters
    ----------
    n : int
        Number of qubits.
    P : int
        QAOA depth (number of layers).
    J : np.ndarray (n, n)
        Ising coupling matrix.
    h : np.ndarray (n,)
        Local Ising fields.
    init_bits : array-like (n,)
        Initial computational basis state (0/1).
    """
    qc = QuantumCircuit(n, name="QAOA_XY")

    for i, b in enumerate(init_bits):
        if b == 1:
            qc.x(i)

    gammas = [Parameter(f"γ_{k}") for k in range(P)]
    betas = [Parameter(f"β_{k}") for k in range(P)]

    ring_pairs = [(i, (i + 1) % n) for i in range(n)]

    for k in range(P):
        γ = gammas[k]
        β = betas[k]

        for i in range(n):
            if abs(h[i]) > 1e-15:
                qc.rz(2.0 * γ * h[i], i)

        for i in range(n):
            for j in range(i + 1, n):
                if abs(J[i, j]) > 1e-15:
                    qc.append(RZZGate(2.0 * γ * J[i, j]), [i, j])

        # XY mixer (preserves cardinality)
        for (i, j) in ring_pairs:
            qc.append(RXXGate(2.0 * β), [i, j])
            qc.append(RYYGate(2.0 * β), [i, j])

    return qc, gammas + betas


# ---------- Helper Functions ----------

def f_qubo(x: np.ndarray, Q: np.ndarray, q: np.ndarray):
    """
    Evaluate QUBO objective function.

    Parameters
    ----------
    x : np.ndarray (n,)
        Binary decision vector.
    Q : np.ndarray (n, n)
        QUBO interaction matrix.
    q : np.ndarray (n,)
        Linear QUBO coefficient vector.
    """
    return float(x @ Q @ x + q @ x)


def bitstr_from_int(k: int, n: int):
    """
    Convert integer to binary array.

    Parameters
    ----------
    k : int
        Integer in [0, 2^n).
    n : int
        Number of bits.
    """
    return np.array(list(np.binary_repr(k, width=n)), dtype=int)


def bitarray_from_qiskit_string(s: str):
    """
    Convert Qiskit little-endian bitstring to array.

    Parameters
    ----------
    s : str
        Bitstring returned by Qiskit.
    """
    return np.array(list(s[::-1]), dtype=int)


def random_theta(P: int, rng: np.random.Generator):
    """
    Generate random initial parameters.

    Parameters
    ----------
    P : int
        QAOA depth.
    rng : np.random.Generator
        NumPy random number generator.
    """
    return np.concatenate([
        rng.uniform(0.0, 2.0 * np.pi, size=P),
        rng.uniform(0.0, 2.0 * np.pi, size=P),
    ])


def bind_params(circ: QuantumCircuit, mapping: dict[Parameter, float]):
    """
    Bind parameters to a Qiskit circuit.

    Parameters
    ----------
    circ : QuantumCircuit
        Parameterized quantum circuit.
    mapping : dict[Parameter, float]
        Mapping from Qiskit Parameters to numerical values.
    """
    try:
        return circ.assign_parameters(mapping, inplace=False)
    except Exception:
        try:
            return circ.bind_parameters(mapping)
        except Exception as e:
            raise RuntimeError(f"Could not assign parameters: {e}")


# ---------- Exact expectation via statevector ----------

def expectation_statevector(theta: np.ndarray):
    """
    Compute exact expectation value using statevector simulation.

    Parameters
    ----------
    theta : np.ndarray (2P,)
        Numerical values of variational parameters.
    """
    bind = {p: float(t) for p, t in zip(theta_params, theta)}
    circ_b = bind_params(ansatz, bind)
    sv = Statevector.from_instruction(circ_b)

    exp = 0.0
    for idx, amp in enumerate(sv.data):
        p = (amp.conjugate() * amp).real
        if p < 1e-16:
            continue

        x = bitstr_from_int(idx, n)
        if x.sum() != B:
            continue

        exp += p * f_qubo(x, Q, q)

    return exp
