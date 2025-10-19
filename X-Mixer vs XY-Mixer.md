# Mixers in QAOA

In the **QAOA (Quantum Approximate Optimization Algorithm)**, the quantum evolution dynamics are constructed by alternating two types of operators:

1. The **cost Hamiltonian**, which encodes the combinatorial optimization problem to be solved.  
2. The **mixing Hamiltonian** or *mixer*, which provides the ability to explore the solution space.

While the cost Hamiltonian selects which states are more favorable (lower energy), the mixer determines how the search space is connected and explored through transitions between binary configurations. Thus, the design of the mixer is crucial, as it defines the subspace of states that the algorithm can visit during evolution.

In this section, we will develop in detail the two most commonly used mixers in QAOA: the **X-mixer** (basic or standard) and the **XY-mixer** (cardinality-preserving mixer). We will analyze their definitions, algebraic properties, implications for constraint preservation, and practical examples related to the cardinality problem:

$$
\sum_{i=1}^n x_i = B.
$$

---

## General Definition of a Mixer

Consider an optimization problem over binary variables $x_i \in \{0,1\}$, with $i = 1, \dots, n$.  
Each $x_i$ is associated with a qubit and the corresponding Pauli operator $Z_i$.  
The full Hilbert space has dimension $2^n$, containing all possible binary configurations.

The mixer is defined as a Hamiltonian $H_M$ whose unitary evolution is:

$$
U_M(\beta) = e^{-i \beta H_M},
$$

where $\beta$ is a variational angle optimized together with the parameters of the cost Hamiltonian.

---

## X-mixer (Basic Mixer)

### Definition

The **X-mixer**, also known as the *standard mixer*, is defined as the sum of Pauli-$X$ operators applied to each qubit:

$$
H_M^{(X)} = \sum_{i=1}^n X_i.
$$

---

### Interpretation

The operator $X_i$ acts as a *flip* that exchanges the state $\ket{0}$ with $\ket{1}$.  
In the binary context, this corresponds to flipping the variable $x_i$: from $0$ to $1$ or from $1$ to $0$.  

Therefore, the X-mixer allows free transitions between any binary configuration, since each application of $X_i$ changes the value of one bit.

The associated unitary evolution is:

$$
U_M^{(X)}(\beta) = \prod_{i=1}^n e^{-i \beta X_i},
$$

which can be implemented through local rotations $R_X(2\beta)$ on each qubit.

---

### Relation to Cardinality

We define the number operator:

$$
\hat{N} = \sum_{i=1}^n \frac{1 - Z_i}{2}.
$$

This operator counts how many qubits are in the $\ket{1}$ state, i.e., the **Hamming weight** of the configuration.

A mixer **preserves cardinality** if it commutes with $\hat{N}$.  
However, we have:

$$
[X_i, \tfrac{1 - Z_i}{2}] \neq 0,
$$

and consequently:

$$
[H_M^{(X)}, \hat{N}] \neq 0.
$$

This means that the X-mixer **does not preserve** the total number of ones.  
Even if the system is initialized in a state with $\hat{N} = B$, the dynamics under the X-mixer will explore configurations with $B-1$, $B+1$, etc.

---

### Implications

To enforce the exact cardinality constraint:

$$
\sum_{i=1}^n x_i = B,
$$

the X-mixer alone is not sufficient.  
A penalty term must be added to the cost Hamiltonian to penalize deviations from $B$, for example:

$$
H_{\text{pen}} = \lambda \left( \sum_{i=1}^n x_i - B \right)^2.
$$

In this way, even though the mixer explores states outside the subspace of cardinality $B$, those states will have much higher energy, and the optimization process will tend to avoid them.

## XY-mixer (Conservative Mixer)

### Definition

The XY-mixer is constructed as a sum of bilocal terms between pairs of qubits:

$$
H_M^{(XY)} = \sum_{(i,j)\in E_M} \left( X_i X_j + Y_i Y_j \right),
$$

where $E_M$ is the set of qubit pairs on which the mixer acts.  
This set can be a complete graph (all pairs) or a reduced one (ring, lattice, etc.), depending on the desired architecture and connectivity level.

---

### Interpretation in Terms of Creation and Annihilation Operators

Recall that:

$$
\sigma_i^+ = \frac{X_i + iY_i}{2}, \qquad \sigma_i^- = \frac{X_i - iY_i}{2}.
$$

With these definitions, each term can be rewritten as:

$$
X_i X_j + Y_i Y_j = 2\left(\sigma_i^+ \sigma_j^- + \sigma_i^- \sigma_j^+\right).
$$

This means that the XY-mixer implements *hopping* processes of excitations:  
it moves a “1” from qubit $j$ to qubit $i$, or vice versa.  
No new ones are created or destroyed—only transferred.

---

### Conservation of Cardinality

Since each hopping process keeps the total number of ones constant, we have:

$$
[H_M^{(XY)}, \hat N] = 0.
$$

This implies that evolution under the XY-mixer strictly preserves the subspace of cardinality $B$.  
If the system begins in a state with $\hat N = B$, it will *always* remain within that subspace, exploring only configurations that respect the constraint.

---

### Choice of Mixing Graph

The set of edges $E_M$ determines the mixer’s connectivity:

- **Complete graph:** allows transitions between all pairs of qubits, ensuring uniform exploration of the feasible subspace at the cost of more gates.  
- **Ring or reduced mesh:** uses only a subset of edges (e.g., $(i,i+1)$ modulo $n$), reducing circuit depth but limiting connectivity.

---

## Implementation of Mixers in Circuit Form (Case $n=4$ Qubits)

This section explicitly illustrates one **mixer layer circuit** for $n=4$ qubits, comparing the **X-mixer** and the **XY-mixer**.  
We also show how to implement the XY-mixer in a **ring topology** and explain the two-qubit gates $\mathrm{RXX}$ and $\mathrm{RYY}$ that realize it.

---

### Preliminaries and Notation

- Qubits are labeled as $1,2,3,4$ (top to bottom).  
- A *mixer layer* carries a variational angle $\beta$ that is optimized.  
- For the **X-mixer**:

  $H_M^{(X)} = \sum_{i=1}^4 X_i, \qquad$
  $U_M^{(X)}(\beta) = e^{-i\beta \sum_i X_i} = \bigotimes_{i=1}^4 e^{-i\beta X_i}.$

- For the **XY-mixer** (over a set of edges $E_M$):

  $H_M^{(XY)} = \sum_{(i,j)\in E_M} (X_iX_j + Y_iY_j), \qquad$
  $U_M^{(XY)}(\beta) = e^{-i\beta H_M^{(XY)}}.$

- We use the **ring topology** $E_M = (1,2), (2,3), (3,4), (4,1), which allows parallelization in two “sublayers” (disjoint pairs).

---

### Two-Qubit Gates $\mathrm{RXX}$ and $\mathrm{RYY}$: Definition and Relation to $XX$ and $YY$

The two-qubit rotations $\mathrm{RXX}(\theta)$ and $\mathrm{RYY}(\theta)$ are defined as:

$\mathrm{RXX}(\theta) = e^{-i\frac{\theta}{2}(X\otimes X)}, \qquad$
$\mathrm{RYY}(\theta) = e^{-i\frac{\theta}{2}(Y\otimes Y)}.$

With these definitions, evolution under a term $XX + YY$ with parameter $\beta$ can be implemented as:


$e^{-i\beta (X_iX_j + Y_iY_j)} =e^{-i\frac{(2\beta)}{2} X_iX_j}e^{-i\frac{(2\beta)}{2} Y_iY_j} = RXX_{(i,j)}(2\beta) RXX_{(i,j)}(2\beta)$



That is, an $\mathrm{RXX}$ gate followed by an $\mathrm{RYY}$ gate with the *same* angle $2\beta$ on the pair $(i,j)$.  
Each $\mathrm{RXX}$–$\mathrm{RYY}$ block *exchanges excitations* between $i$ and $j$ without creating or destroying them, thus conserving $\hat N$.

---

### Single-Layer Circuit of the **X-mixer** (4 Qubits)

The X-mixer is implemented with single-qubit rotations $R_X(2\beta) = e^{-i\beta X}$ on *each* qubit:

$U_M^{(X)}(\beta) = \bigotimes_{i=1}^4 R_X^{(i)}(2\beta).$

All gates are local (one per qubit):

<p align="center">
  <img src="X-mixer.png" alt="X-mixer" width="200"/>
</p>

### Comments

- **Depth and noise:** very low circuit depth; only local single-qubit gates are used.  
- **Cardinality:** does **not** preserve \( \sum_i x_i \). Even if the system starts in a configuration with weight $B$, the dynamics can explore states with weights $B \pm 1, \dots$.  
  To enforce $\sum_i x_i = B$ with this mixer, one must add **penalty terms** to the cost Hamiltonian.

---

### Single-layer circuit of the XY-mixer in ring topology (4 qubits)

For the ring topology  
$E_M = (1,2), (2,3), (3,4), (4,1)$,  
we can **parallelize** the implementation into two sublayers:  
first act on pairs $(1,2)$ and $(3,4)$ simultaneously,  
then on pairs $(2,3)$ and $(4,1)$.  
Each edge is implemented with an $\mathrm{RXX}(2\beta)$ gate followed by an $\mathrm{RYY}(2\beta)$ gate:

<p align="center">
  <img src="XY-mixer.png" alt="XY-mixer" width="600"/>
</p>

## Comparison between X-mixer and XY-mixer

- **X-mixer:** allows exploring the entire hypercube of configurations. It is easy to implement (only single-qubit gates), but it does **not** preserve cardinality constraints. To enforce them, additional penalty terms must be added to the cost Hamiltonian.
- **XY-mixer:** strictly preserves the number of ones. This allows enforcing the cardinality constraint as a symmetry of the dynamics. One needs to prepare a feasible initial state and use two-qubit gates (RXX and RYY), which increases the circuit depth, but the exploration is limited to valid states only.

---




