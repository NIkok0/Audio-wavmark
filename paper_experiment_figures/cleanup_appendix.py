from pathlib import Path

main = Path(r'E:\down\main.tex')
s = main.read_text(encoding='utf-8')
s = s.replace(
    'The full matrixized relation and reductions\nare given in Appendix~\\ref{app:matrixized-cszk} and\nAppendix~\\ref{app:main}.',
    'The full matrixized relation and reductions\nare given in the supplementary appendix.'
)
main.write_text(s, encoding='utf-8')

app = Path(r'E:\down\security_appendix.tex')
a = app.read_text(encoding='utf-8')
a = a.replace(
    '% IEEE-style supplementary appendix for Coded-Sharding-ZK\n% Standalone review file; remove the preamble/document wrapper when merging.',
    '% IEEE-style supplementary appendix for Coded-Sharding-ZK.\n% This file is standalone for review. When merging into the main manuscript,\n% remove the preamble, \\begin{document}, \\maketitle, and \\end{document} wrapper.'
)
a = a.replace(
    'This appendix gives a compact, statement-oriented security construction for the coded-sharding zero-knowledge proof used in the main text. The presentation follows the standard style of zk-SNARK applications: we define a public instance, a private witness, an arithmetic circuit, and the corresponding proving and verification algorithms. We do not introduce a new zero-knowledge proof system. Instead, we define an NP relation for coded-sharding federated unlearning and instantiate it with any complete, zero-knowledge, and knowledge-sound argument system for arithmetic circuits over $\\F$.',
    'This supplementary appendix provides the formal coded-sharding zero-knowledge relation and the corresponding security reductions for the construction summarized in the main text. The presentation follows the standard style of zk-SNARK applications: we define a public instance, a private witness, an arithmetic circuit, and the corresponding proving and verification algorithms. We do not introduce a new zero-knowledge proof system. Instead, we define an NP relation for coded-sharding federated unlearning and instantiate it with any complete, zero-knowledge, and knowledge-sound argument system for arithmetic circuits over $\\F$.'
)
a = a.replace(
    'This appendix gives an implementation-oriented description of\nthe coded-sharding zero-knowledge construction.',
    'This section gives an implementation-oriented description of\nthe coded-sharding zero-knowledge construction.'
)
app.write_text(a, encoding='utf-8')
print('patched appendix cleanup')
