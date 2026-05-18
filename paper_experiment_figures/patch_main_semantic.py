from pathlib import Path

path = Path(r'E:\down\main.tex')
text = path.read_text(encoding='utf-8')

block_def = r'''

\subsection{Protocol Verification and Semantic Forgetting}
\label{subsec:protocol-vs-semantic}

We distinguish protocol-level verifiability from semantic
forgetting. Let $w$ be the model before deletion, let $a$ be the
deleted client, let $w^u$ be the model output by the unlearning
protocol, and let $w^{-a}$ denote a reference model obtained by
full retraining after removing client $a$ and all records that
are effective under identity $a$. Let $\mathcal D_{\mathrm{test}}$
be the test distribution and $\mathcal D_a$ be the distribution
of samples associated with the deleted client. For an input $x$,
we write $p_w(x)$ for the predictive distribution of model $w$.

\begin{myDef}[Protocol-Level Verifiable Federated Unlearning]
A federated unlearning protocol provides protocol-level
verifiable unlearning if, for every accepted deletion transcript
for target client $a$, there exists an efficient extractor that
outputs an execution trace satisfying the declared unlearning
relation except with negligible probability. The extracted trace
must certify that: (i) all reconstruction inputs open to committed
historical, shard-assignment, and coded-checkpoint states; (ii)
the deletion-state update moves $a$ from the active identity set
to the deleted identity set; (iii) the affected-shard retraining
excludes $a$ under the current deletion root; (iv) unaffected
shards are preserved; (v) the global unlearned model is correctly
recomposed from the certified shard states; and (vi) the resulting
state is bound to the public transcript chain so that later
accepted training or retraining steps must prove non-membership
in the latest deletion set.
\end{myDef}

\begin{myDef}[Semantic Federated Unlearning]
A federated unlearning algorithm provides semantic unlearning
with respect to a reference full-retraining procedure if the
unlearned model $w^u$ is close to the reference model $w^{-a}$
under behavioral or distributional metrics. A generic semantic
distance can be written as
\begin{equation}
\Delta_{\mathrm{sem}}(w^u,w^{-a})
=
\mathbb E_{x\sim\mathcal D_{\mathrm{test}}}
\left[
d\big(p_{w^u}(x),p_{w^{-a}}(x)\big)
\right],
\label{eq:semantic-distance}
\end{equation}
where $d(\cdot,\cdot)$ may be instantiated by prediction
disagreement, total variation distance, KL divergence,
Jensen--Shannon divergence, or another task-specific behavioral
distance. Smaller $\Delta_{\mathrm{sem}}$ indicates that the
unlearned model is behaviorally closer to full retraining.
\end{myDef}

\textbf{Remark.}
Our protocol proves execution of the declared coded-sharding
unlearning transition rather than semantic forgetting itself.
In particular, an accepted zero-knowledge transcript certifies
that the server used committed checkpoints, updated the deletion
state, excluded the target identity from the affected retraining
base, preserved unaffected shards, and recomposed the final model
according to the public relation. It does not by itself prove that
$w^u$ is distributionally indistinguishable from $w^{-a}$. If the
underlying coded-sharding federated unlearning algorithm satisfies
a semantic forgetting guarantee, our proof layer certifies that
the server executed that algorithm on committed states. Thus,
cryptographic verifiability and semantic forgetting are
complementary guarantees, not interchangeable ones.
'''

block_boundary = r'''

\textbf{Security boundary.}
The security theorem establishes trace soundness, deletion-state
consistency, and post-deletion exclusion under the stated
cryptographic assumptions. That is, an accepted proof package
implies an extractable coded-sharding unlearning trace in which
the selected coded checkpoints open to committed roots, the
target client is removed from the active set and inserted into
the deleted set, the affected-shard replacement is bound to the
declared retraining proof, unaffected shards are preserved, and
later accepted rounds must prove non-membership with respect to
the latest deletion root. We do not claim that the theorem proves
perfect semantic deletion, distributional indistinguishability
from full retraining, or immunity to fresh-identity Sybil
re-registration. Semantic forgetting quality is inherited from
the underlying unlearning algorithm and should be evaluated by
behavioral audits against a reference full-retraining model,
whereas fresh-identity re-registration requires external identity
governance. This boundary does not weaken the protocol-level
claim: the contribution of the proof layer is to make the
declared unlearning execution publicly auditable under malicious
or deviant server behavior.
'''

block_metrics = r'''

\subsection{Semantic Forgetting Metrics}
\label{subsec:semantic-metrics}

Although the proposed proof system verifies execution correctness,
we also evaluate semantic forgetting behavior using a reference
full-retraining model. For each deletion target $a$, we compare
the unlearned model $w^u$ with the original model $w$ and the
reference model $w^{-a}$ trained after removing $a$. The following
metrics are reported as behavioral audits; they complement the
cryptographic trace proof but do not replace it.

\textbf{Accuracy after unlearning.}
We report the test accuracy of $w^u$ on $\mathcal D_{\mathrm{test}}$
and the accuracy drop relative to the original model:
\begin{equation}
\Delta_{\mathrm{acc}}
=
\mathrm{Acc}(w,\mathcal D_{\mathrm{test}})
-
\mathrm{Acc}(w^u,\mathcal D_{\mathrm{test}}).
\end{equation}

\textbf{Distance to full retraining.}
We measure parameter-level deviation from the full-retraining
reference:
\begin{equation}
\Delta_{\ell_2}
=
\left\|w^u-w^{-a}\right\|_2 .
\end{equation}
When model parameters are evaluated after fixed-point conversion
or chunking, the same representation is used for both models.

\textbf{Prediction disagreement.}
We compute the fraction of test samples on which $w^u$ and
$w^{-a}$ predict different labels:
\begin{equation}
\Delta_{\mathrm{pred}}
=
\Pr_{x\sim\mathcal D_{\mathrm{test}}}
\left[
\arg\max p_{w^u}(x)
\ne
\arg\max p_{w^{-a}}(x)
\right].
\end{equation}

\textbf{Distributional divergence.}
We instantiate~\eqref{eq:semantic-distance} with Jensen--Shannon
divergence:
\begin{equation}
\Delta_{\mathrm{JS}}
=
\mathbb E_{x\sim\mathcal D_{\mathrm{test}}}
\left[
\mathrm{JS}
\big(p_{w^u}(x)\,\|\,p_{w^{-a}}(x)\big)
\right].
\end{equation}
KL divergence can also be reported when the predictive
distributions are appropriately smoothed.

\textbf{Deleted-client confidence reduction.}
For samples from the deleted-client distribution $\mathcal D_a$,
we measure the reduction in confidence assigned to the ground-truth
label $y$:
\begin{equation}
\Delta_{\mathrm{conf}}
=
\mathbb E_{(x,y)\sim\mathcal D_a}
\left[
p_w(y\mid x)-p_{w^u}(y\mid x)
\right].
\end{equation}

\textbf{Membership-inference success.}
Let $\mathcal M$ be a membership-inference auditor that outputs
$1$ when it predicts that a sample was used in training. We report
the attack success rate on deleted-client samples after unlearning:
\begin{equation}
\mathrm{Succ}_{\mathrm{MIA}}(w^u)
=
\Pr_{x\sim\mathcal D_a}
\left[
\mathcal M(p_{w^u}(x))=1
\right].
\end{equation}
We also report the reduction relative to the original model:
\begin{equation}
\Delta_{\mathrm{MIA}}
=
\mathrm{Succ}_{\mathrm{MIA}}(w)
-
\mathrm{Succ}_{\mathrm{MIA}}(w^u).
\end{equation}

\textbf{Marker or backdoor removal.}
If marker-based auditing is used, we report the removal rate of
target-client markers:
\begin{equation}
\mathrm{Remove}_{\mathrm{marker}}
=
1-
\frac{
\mathrm{ASR}(w^u,\mathcal D_a^{\mathrm{mark}})
}{
\mathrm{ASR}(w,\mathcal D_a^{\mathrm{mark}})
},
\end{equation}
where $\mathrm{ASR}$ denotes the marker or backdoor attack success
rate.

Lower $\Delta_{\mathrm{sem}}$, $\Delta_{\ell_2}$,
$\Delta_{\mathrm{pred}}$, and $\Delta_{\mathrm{JS}}$ indicate that
the unlearned model is closer to the full-retraining reference.
Lower membership-inference success after unlearning and higher
marker-removal rate indicate stronger behavioral evidence of
forgetting on the deleted client. These measurements are empirical
behavioral audits; they complement, but do not replace, the
cryptographic proof that the declared unlearning transition was
executed correctly.
'''

needle_def = "The protocol satisfies continuous-verification security if every PPT adversary wins with probability at most $\\negl(\\lambda)$.\n"
if block_def.strip() not in text:
    text = text.replace(needle_def, needle_def + block_def, 1)

needle_boundary = "Thus reintroducing $a$ later requires forging a non-membership\nwitness or rolling back the chained state commitment. $\\square$\n"
if block_boundary.strip() not in text:
    text = text.replace(needle_boundary, needle_boundary + block_boundary, 1)

needle_metrics = "Cost is measured by deletion latency, affected-shard retraining time, coded-checkpoint decoding time, storage overhead, and communication overhead. Proof-system overhead is measured by constraint count, witness generation time, proving time, verification time, proof size, and peak memory. Security robustness is measured by attack rejection rate over tampered transcripts.\n"
if block_metrics.strip() not in text:
    text = text.replace(needle_metrics, needle_metrics + block_metrics, 1)

path.write_text(text, encoding='utf-8')
print('patched', path)
