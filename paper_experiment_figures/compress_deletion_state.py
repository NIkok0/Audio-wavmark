from pathlib import Path
p = Path(r'E:\down\main-1.tex')
s = p.read_text(encoding='utf-8')
old = r'''The deleted client receives a deletion certificate
\begin{equation}
\VerifyDeleted(r_{U,t},a,\pi_a^{del})
=
1.
\label{eq:del-cert}
\end{equation}

For every future training or affected-shard retraining step,
selected identities must prove non-membership in the previous
deletion set:
\begin{equation}
\begin{aligned}
&\forall i\in\mathcal P_t,
\\
&\VerifyNotDeleted(r_{U,t-1},i,\pi_i^{notdel})
=
1.
\end{aligned}
\label{eq:notdel}
\end{equation}

The state commitment binds the unlearned model, audit log,
'''
new = r'''The deletion event is accompanied by an authenticated deletion
certificate for $a$ under the new deletion root $r_{U,t}$. In every
later training or affected-shard retraining step, selected identities
must also provide not-deleted witnesses against the latest available
deletion root. These witness checks are part of the public transcript
verification, but their Merkle or accumulator-level predicates are
left to the supplementary appendix.

The state commitment binds the unlearned model, audit log,
'''
if old not in s:
    raise SystemExit('deletion witness block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('compressed deletion witness formulas')
