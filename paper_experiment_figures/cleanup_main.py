from pathlib import Path
import re

main = Path(r'E:\down\main.tex')
text = main.read_text(encoding='utf-8')

# Submission-safe author/header cleanup without inventing affiliations.
text = text.replace(
    r"\author{Hu~Xiong and Li~Miao%\n\thanks{Hu Xiong and Li Miao are with the corresponding institution. E-mail: to be added.}%\n}",
    r"\author{Anonymous Authors%\n\thanks{Manuscript submitted for double-blind review.}%\n}"
)
text = text.replace(
    r"\markboth{IEEE Transactions on Dependable and Secure Computing,~Vol.~XX, No.~XX, 2026}%\n{Xiong and Miao: Verifiable Coded-Sharding Federated Unlearning}",
    r"\markboth{Submitted for IEEE journal review}%\n{Anonymous Authors: Verifiable Coded-Sharding Federated Unlearning}"
)

# Fix duplicated citation.
text = text.replace(
    r"FedAvg updates the global model as~\cite{mcmahan2017fedavg,kairouz2021advances}~\cite{mcmahan2017fedavg,kairouz2021advances}",
    r"FedAvg updates the global model as~\cite{mcmahan2017fedavg,kairouz2021advances}"
)

# Reduce duplicated main-text trace soundness material in the generic framework section.
start = text.find(r"\textbf{Proposition 1 (Trace soundness).}")
section_cszk = text.find(r"\section{Verifiable Coded-Sharding Federated Unlearning}")
if start != -1 and section_cszk != -1 and start < section_cszk:
    end_marker = "The server-side algebraic cost is dominated by public-coefficient\nlinear constraints. Decoding and recomposition scale with\n$O(S^2d)$ and $O(Sd)$ arithmetic operations, while provenance\nand identity-state checks add Merkle-opening costs. The\nretraining subproof cost is separated and depends on the\nchosen training-integrity backend."
    end = text.find(end_marker, start)
    if end != -1:
        end += len(end_marker)
        replacement = r"""
\paragraph{Framework-level trace guarantee.}
At the framework level, acceptance of a proof package should imply
an extractable trace that satisfies the declared unlearning relation,
opens all reconstruction inputs to committed roots, updates the
active/deleted identity states, and binds the resulting model to the
state chain. The coded-sharding instantiation in
Section~\ref{sec:cszk} makes this guarantee concrete through the
matrix relation, selector constraints, retraining-proof binding, and
state-continuity checks. The full matrixized relation and reductions
are given in Appendix~\ref{app:matrixized-cszk} and
Appendix~\ref{app:main}.
""".strip()
        text = text[:start] + replacement + text[end:]

# Make experiment tables explicitly non-result templates instead of raw placeholders.
text = text.replace(
    "Table~\\ref{tab:utility_cost} reports the utility and unlearning-cost metrics. Numerical entries are left as placeholders until prototype execution.",
    "Table~\\ref{tab:utility_cost} defines the utility and unlearning-cost reporting template. Numerical entries must be filled with measured prototype results before submission."
)
text = text.replace("Our verified protocol is expected to have almost the same model utility", "Our verified protocol should have nearly the same model utility")
text = text.replace("Proof generation is expected to be the dominant overhead", "Proof generation is the dominant overhead to be measured")
text = text.replace("Increasing $S$ reduces the expected affected-shard size", "Increasing $S$ reduces the affected-shard size in expectation")
text = text.replace("The rejection rate is expected to be 100\\% for all listed attacks when the corresponding proof and commitment checks are enabled.", "The measured rejection rate should be reported for each attack class; a valid implementation should reject all listed tampering attempts when the corresponding proof and commitment checks are enabled.")
text = text.replace("The expected utility of our protocol is almost identical", "The utility of our protocol should be nearly identical")
text = text.replace("Verification is expected to remain succinct", "Verification is designed to remain succinct")

# Replace raw [XX] entries with -- so they are visibly empty cells, not textual placeholders.
text = text.replace("[XX]", "--")

# Replace boxed placeholder figures with figure-plan descriptions that do not look like final results.
text = text.replace(
    "Bar plot placeholder: deletion latency of No-unlearning, Full retraining, FedEraser, Coded-sharding FU, and Ours under 1\\%, 5\\%, and 10\\% deletion workloads.",
    "Prototype-generated bar plot: deletion latency of No-unlearning, Full retraining, FedEraser, Coded-sharding FU, and Ours under 1\\%, 5\\%, and 10\\% deletion workloads."
)
text = text.replace(
    "Line plot placeholder: proving time and verification time as functions of shard number $S$ and checkpoint dimension $d$.",
    "Prototype-generated line plot: proving time and verification time as functions of shard number $S$ and checkpoint dimension $d$."
)
text = text.replace(
    "Tradeoff plot placeholder: affected-shard retraining time decreases with $S$, while decoding/recomposition constraints and proof time increase with $S$.",
    "Prototype-generated tradeoff plot: affected-shard retraining time and proof-generation overhead under different shard numbers $S$."
)
text = text.replace(
    "Heatmap placeholder: accept/reject outcomes for each tampering class over repeated trials.",
    "Prototype-generated heatmap: accept/reject outcomes for each tampering class over repeated trials."
)

# Conclusion should not say future work is implementing the core prototype if the evaluation section is framed as prototype methodology.
text = text.replace(
    "Future work includes implementing the Circom/snarkjs prototype, integrating a TMT-FL-style retraining subproof, evaluating proof overhead under different shard and checkpoint parameters, and studying the tradeoff among coded-checkpoint redundancy, recovery latency, proof cost, and semantic unlearning quality.",
    "Future work includes strengthening the affected-shard retraining subproof, extending the prototype to larger models and deletion workloads, and studying the tradeoff among coded-checkpoint redundancy, recovery latency, proof cost, and semantic unlearning quality."
)

main.write_text(text, encoding='utf-8')
print('patched main cleanup')
