##Script for the presentation

##Team introduction (Briefly mention your team members and their roles)
Manuel:
Chanakya:
Cheewei:
Andrés:

##Project overview -- What problem are you solving? What is your project goals.
Our goal is to build and benchmark a QAOA-based portfolio selection pipeline that uses an XY mixer to enforce cardinality

##MVP and deliverables -- Clearly define your Minimum Viable Product and expected deliverables
Our MVP is a 20-asset portfolio demo:
we import real price data, construct a Markowitz-style QUBO with a cardinality constraint, solve it with CVXPy and brute force, and run QAOA with an XY mixer on a simulator for a direct comparison.
The key deliverables are a clean, documented GitHub repository with all the code and notebooks, plus a short written report summarizing performance and limitations.

##Progress update -- What work has been completed so far?
So far, we have:
-Selected a universe of 20 real assets and preprocessed returns.
-Built the Markowitz cost function and its QUBO encoding with cardinality.
-Implemented classical solvers using CVXPy and brute force, and implemented QAOA with an XY mixer on a simulator, with first comparisons to the classical optimum.

##Approach and methodology -- How are you tackling the project?
Our methodology is:
Start from historical prices, compute expected returns and covariance, map the problem to a binary QUBO with a cardinality constraint, and then apply QAOA with an XY mixer in Qiskit.
Each week we divide the tasks to do and present it to our Mentor how guided us in the process.

##Next steps -- What are your plans moving forward?
Next, we plan to:
-Add more realistic constraints to the Hamiltonian.
-Integrate error-mitigation techniques when running on IBM hardware
-And scale to larger portfolios, with 60+ assets, exploring both advanced simulation and real-device executions.
