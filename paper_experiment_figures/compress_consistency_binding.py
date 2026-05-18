from pathlib import Path
p = Path(r'E:\down\main-1.tex')
s = p.read_text(encoding='utf-8')

start = s.index(r'\subsection{Consistency Constraints}')
end = s.index(r'\subsection{Retraining-Proof Interface and Boundary}', start)
new_consistency = r'''
\subsection{Consistency Constraints}
\label{subsec:cs-consistency-summary}

Beyond the core transition in~\eqref{eq:core-transition-trace}, the
proof enforces four consistency obligations. First, the public
decoding matrix must be the inverse of the selected coding submatrix,
so that the prover cannot decode from an unrelated row set. Second,
the affected-shard selector is constrained to be one-hot, which fixes
a unique shard $s^\star$ for the deleted identity. Third, localized
replacement preserves every row $w_s^g$ with $s\neq s^\star$ and
replaces only the affected row by the retrained checkpoint
$w_{s^\star}^{rt}$. Fourth, the recomposition coefficients are
normalized before forming $w^u$. These obligations are enforced
element-wise in the arithmetic circuit; the corresponding inverse,
selector, row-preservation, and normalization constraints are given
in the supplementary appendix.

'''
s = s[:start] + new_consistency + s[end:]

start = s.index(r'\subsection{Binding Semantics}')
end = s.index(r'\subsection{Deletion-State Continuity}', start)
new_binding = r'''
\subsection{Binding Semantics}
\label{subsec:binding-summary}

The algebraic trace is meaningful only when its inputs originate
from committed protocol state. The proof therefore binds three kinds
of objects. First, the selected coded rows
$(\mathcal I,\widetilde W_S^g)$ must open to the coded-checkpoint
root $r_C$, and the selected indices determine
$\Lambda_S=\Lambda[\mathcal I,:]$. Second, the target identity $a$
must open to the affected shard $s^\star$ under the shard-assignment
root $r_S$, and the one-hot selector must select that shard. Third,
the affected-shard retraining backend is linked to the coded-sharding
trace through the shared public tuple
\begin{equation}
(a,s^\star,h_{in},h_{out},r_{U,t-1},\mathsf{TrainCfg}),
\label{eq:binding-tuple}
\end{equation}
where $h_{in}$ hashes the affected-shard checkpoint decoded from
committed coded rows, $h_{out}$ hashes the retrained affected-shard
checkpoint, $r_{U,t-1}$ fixes the deletion set used for exclusion,
and $\mathsf{TrainCfg}$ fixes the public retraining configuration.
The verifier accepts the composed transition only when the tuple used
inside $\pi_{cs}$ matches the tuple verified by $\pi_{rt}$. Full
Merkle-opening predicates, hash definitions, and public-input equality
constraints are deferred to the supplementary appendix.

'''
s = s[:start] + new_binding + s[end:]

s = s.replace('the public-input equality in\n\\eqref{eq:proof-bind} binds the inserted affected shard to the same\nretraining statement as $\\pi_{rt}$.',
              'the shared tuple in~\\eqref{eq:binding-tuple} binds the inserted affected shard to the same\nretraining statement as $\\pi_{rt}$.')

p.write_text(s, encoding='utf-8')
print('compressed consistency and binding sections')
