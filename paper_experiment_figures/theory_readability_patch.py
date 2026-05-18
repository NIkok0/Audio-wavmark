from pathlib import Path
import re

p = Path(r'E:\down\main-1.tex')
s = p.read_text(encoding='utf-8')

old_threat = r"""\textbf{Threat model.} The server may be malicious or rationally deviant: it may skip unlearning, use uncommitted coded checkpoints, decode inconsistent shard states, retrain the wrong shard, keep the target client inside retraining, modify unaffected shards, recompute an incorrect global model, roll back deletion state, or reintroduce a deleted identity later. Clients may collude with the server, but adversaries are PPT and cannot break the underlying hash, commitment, accumulator, or proof-system assumptions. We do not solve identity governance, poisoning, update privacy, or Sybil re-registration under a fresh identity; these are orthogonal mechanisms.
"""
new_threat = r"""\textbf{Threat model.}
We use a layered threat model to separate the deletion-transition
claim from orthogonal FL security issues. The aggregation and
unlearning server is malicious or rationally deviant: it may skip
unlearning, use uncommitted coded checkpoints, decode inconsistent
shard states, retrain the wrong shard, keep the target client inside
retraining, modify unaffected shards, recompute an incorrect global
model, roll back deletion state, or later reintroduce a deleted
identity. Clients may collude with the server, but client identities
are assumed to belong to a fixed authenticated namespace. Under this
namespace, a deleted identity must prove non-membership in the latest
deletion set before participating in later training or retraining.
Auditors are public verifiers that check transcripts, commitments,
and proof objects without accessing raw client data or plaintext
checkpoints. We do not address poisoning, false local-data claims,
client-side data authenticity, or Sybil re-registration under a fresh
identity; these require complementary mechanisms such as identity
governance, authenticated enrollment, data-origin attestation, or
poisoning-robust training.
"""
if old_threat in s:
    s = s.replace(old_threat, new_threat, 1)
else:
    raise SystemExit('threat block not found')

# Insert claim-to-mechanism table after framework-level trace guarantee paragraph.
needle_framework = r"""At the framework level, acceptance of a proof package should imply
an extractable trace that satisfies the declared unlearning relation,
opens all reconstruction inputs to committed roots, updates the
active/deleted identity states, and binds the resulting model to the
state chain. The coded-sharding instantiation in
Section~\ref{sec:cszk} makes this guarantee concrete through the
matrix relation, selector constraints, retraining-proof binding, and
state-continuity checks. The full matrixized relation and reductions
are given in the supplementary appendix.
"""
claim_table = r"""

Table~\ref{tab:claim_mechanism} summarizes the correspondence
between the main security claims and the mechanisms that enforce
them. The table is intended as a roadmap: the main text states the
core objects and proof obligations, while the supplementary appendix
contains the row-level openings, coordinate constraints, algorithms,
and reductions.

\begin{table*}[t]
\caption{Security Claims and Enforcing Mechanisms}
\label{tab:claim_mechanism}
\centering
\scriptsize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.1}
\begin{tabularx}{\textwidth}{@{}p{0.20\textwidth}p{0.28\textwidth}p{0.20\textwidth}X@{}}
\toprule
\textbf{Claim} & \textbf{Mechanism} & \textbf{Main Object} & \textbf{Where Formalized} \\
\midrule
Checkpoint provenance & Merkle opening and commitment binding & $r_C,\mathcal I,\widetilde W_S^g$ & coded-checkpoint opening relation \\
Affected-shard locality & shard opening and one-hot selector & $r_S,s^\star,\chi_a$ & selector and shard-opening constraints \\
Correct coded decoding & public inverse check & $\Lambda_S,\Gamma$ & $\Gamma\Lambda_S=I$ and decoding trace \\
Localized replacement & diagonal selector masking & $D_\chi,W^g,W^{rt},W^u$ & affected-row replacement relation \\
Retraining binding & shared public inputs across proofs & $\pi_{rt},h_{in},h_{out},r_{U,t-1}$ & retraining-proof interface \\
State continuity & chained state commitment & $com_t,r_A,r_U,r_H,r_S,r_C$ & deletion-state relation \\
Future exclusion & not-deleted witnesses against latest root & $r_U,\pi_i^{notdel}$ & persistent deletion theorem \\
\bottomrule
\end{tabularx}
\end{table*}
"""
if claim_table.strip() not in s:
    s = s.replace(needle_framework, needle_framework + claim_table, 1)

# Compress matrix-oriented realization formula block.
old_matrix = r"""\paragraph{Matrix-oriented realization.}
The algebraic part of the trace can be implemented as a
batched matrix residual:
\begin{equation}
\mathcal E_{cs}
=
\begin{bmatrix}
\Lambda_S W^g-\widetilde W_S^g
\\
\Gamma\widetilde W_S^g-W^g
\\
(I-D_\chi)W^g+D_\chi W^{rt}-W^u
\\
(\rho^u)^\top W^u-w^u
\end{bmatrix}.
\label{eq:cs-residual}
\end{equation}
The circuit enforces
\begin{equation}
\mathcal E_{cs}=0.
\label{eq:cs-residual-zero}
\end{equation}
The last block is viewed as a $1\times d$ row residual, so
$\mathcal E_{cs}\in\mathbb F^{(3S+1)\times d}$. Hence the
four transition equations are verified as one batched matrix
relation. The implementation-level circuit specification is
given in the supplementary appendix.
"""
new_matrix = r"""\paragraph{Matrix-oriented realization.}
For circuit implementation, the four equations in
\eqref{eq:core-transition-trace} are batched into a single residual
relation and enforced element-wise over the fixed-point field
representation. The main text uses this compact trace as the
security-relevant object; the full residual matrix, row-level
openings, coordinate constraints, and witness-construction algorithm
are deferred to the supplementary appendix.
"""
if old_matrix in s:
    s = s.replace(old_matrix, new_matrix, 1)
else:
    raise SystemExit('matrix block not found')

# Add retraining proof boundary before Binding Semantics if not present.
needle_binding_section = r"\subsection{Binding Semantics}\n"
rt_block = r"""
\subsection{Retraining-Proof Interface and Boundary}
\label{subsec:rt-proof-boundary}

The coded-sharding proof $\pi_{cs}$ verifies how the retrained
affected shard is integrated into the committed deletion transition;
it does not, by itself, re-prove the entire local training procedure.
We therefore treat the affected-shard retraining proof $\pi_{rt}$ as
a modular backend with a public statement
\begin{equation}
(a,s^\star,h_{in},h_{out},r_{U,t-1},\mathsf{TrainCfg}).
\label{eq:rt-interface}
\end{equation}
A weak prototype instantiation may use a hash-bound retraining
certificate, which binds the supplied output shard to the target
identity, input checkpoint, deletion root, and retraining
configuration. This weak instantiation validates transcript
integration but does not prove that the retraining computation was
executed step by step. A strong deployment instantiates $\pi_{rt}$
with a sound training-integrity proof that certifies the declared
retraining computation after excluding $a$. The security theorem is
modular: its retraining-correctness component relies on the soundness
guarantee provided by the chosen $\pi_{rt}$ backend.

"""
if rt_block.strip() not in s:
    s = s.replace(needle_binding_section, rt_block + needle_binding_section, 1)

# Add guarantees table before privacy boundary.
needle_privacy = r"\textbf{Privacy boundary.}"
guarantee_table = r"""
\begin{table}[t]
\caption{Security Boundary of the Protocol}
\label{tab:security_boundary}
\centering
\scriptsize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabularx}{\columnwidth}{@{}X X@{}}
\toprule
\textbf{Guaranteed by Accepted Transcripts} & \textbf{Not Guaranteed by This Layer} \\
\midrule
Committed checkpoint use & Perfect semantic indistinguishability \\
Target identity exclusion under the same namespace & Fresh-identity Sybil resistance \\
Affected-shard replacement binding & Poisoning robustness or data authenticity \\
Unaffected-shard preservation & Correctness of a weak hash-only retraining certificate \\
Deletion-state continuity on the accepted chain & Fork prevention without a public publication mechanism \\
Future not-deleted checks & Privacy of public metadata such as timing or deletion frequency \\
\bottomrule
\end{tabularx}
\end{table}

"""
if guarantee_table.strip() not in s:
    s = s.replace(needle_privacy, guarantee_table + needle_privacy, 1)

# Rewrite proof sketch as roadmap.
old_proof = r"""\emph{Proof sketch.}
Knowledge soundness extracts a witness for $\pi_{cs}$. The
openings to $r_C$ and $r_S$ bind the selected coded checkpoints,
their row index set, and the target-shard assignment; otherwise,
the prover forges a committed opening or finds a hash collision.
The matrix constraint $\mathcal E_{cs}=0$ fixes decoding,
affected-shard replacement, and global recomposition. The
public-input binding in~\eqref{eq:proof-bind} enforces
\[
(a,s^\star,h_{in},h_{out},r_{U,t-1},\mathsf{TrainCfg})_{cs}
=
(a,s^\star,h_{in},h_{out},r_{U,t-1},\mathsf{TrainCfg})_{rt},
\]
and therefore prevents using a retraining proof for another
target, shard, input checkpoint, output shard, deletion-set
root, or retraining configuration. The deletion certificate establishes $a\in U_t$, and later
not-deleted proofs are checked against the latest deletion root.
Thus reintroducing $a$ later requires forging a non-membership
witness or rolling back the chained state commitment. $\square$
"""
new_proof = r"""\emph{Proof roadmap.}
The proof proceeds in four steps. First, knowledge soundness
extracts the witness used by $\pi_{cs}$. Second, commitment binding
fixes the selected coded rows, the affected-shard assignment, and
the state roots; otherwise the adversary forges an opening or finds
a hash collision. Third, the core trace relation in
\eqref{eq:core-transition-trace} fixes decoding, localized
replacement, and recomposition, while the public-input equality in
\eqref{eq:proof-bind} binds the inserted affected shard to the same
retraining statement as $\pi_{rt}$. Finally, the deletion certificate,
not-deleted witnesses, and chained state commitment enforce deletion
monotonicity and future exclusion. The detailed bad-event reduction
is given in the supplementary appendix. $\square$
"""
if old_proof in s:
    s = s.replace(old_proof, new_proof, 1)
else:
    raise SystemExit('security proof sketch not found')

p.write_text(s, encoding='utf-8')
print('theory readability patch applied')
