from pathlib import Path
p = Path(r'E:\down\main-1.tex')
s = p.read_text(encoding='utf-8')

rt_block = r'''
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

'''
if r'\label{subsec:rt-proof-boundary}' not in s:
    s = s.replace('\n\\subsection{Binding Semantics}\n', '\n' + rt_block + '\\subsection{Binding Semantics}\n', 1)

s = s.replace('Here $\\mathcal C_{mat}$ enforces\n$\\mathcal E_{cs}=0$, $\\mathcal C_{open}$ verifies the coded',
              'Here $\\mathcal C_{mat}$ enforces the core coded-sharding\ntrace relation, $\\mathcal C_{open}$ verifies the coded')
s = s.replace('the affected shard. The batched matrix relation\n$\\mathcal E_{cs}=0$ enforces selected decoding, localized\nreplacement, and normalized recomposition.',
              'the affected shard. The core trace relation enforces selected\ndecoding, localized replacement, and normalized recomposition.')
s = s.replace('coded-sharding trace in~\\eqref{eq:core-transition-trace},\nequivalently $\\mathcal E_{cs}=0$; (iv)',
              'coded-sharding trace in~\\eqref{eq:core-transition-trace}; (iv)')
s = s.replace('is valid if it satisfies the batched matrix relation, consistency\nconstraints, binding predicates, and deletion-state continuity',
              'is valid if it satisfies the core trace relation, consistency\nconstraints, binding predicates, and deletion-state continuity')

p.write_text(s, encoding='utf-8')
print('inserted rt boundary and cleaned Ecs references')
