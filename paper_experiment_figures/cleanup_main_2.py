from pathlib import Path
import re
p=Path(r'E:\down\main.tex')
s=p.read_text(encoding='utf-8')
s=re.sub(r"\\author\{Hu~Xiong and Li~Miao%\s*\\thanks\{Hu Xiong and Li Miao are with the corresponding institution\. E-mail: to be added\.\}%\s*\}", r"\\author{Anonymous Authors%\n\\thanks{Manuscript submitted for double-blind review.}%\n}", s, count=1)
s=re.sub(r"\\markboth\{IEEE Transactions on Dependable and Secure Computing,~Vol\.~XX, No\.~XX, 2026\}%\s*\{Xiong and Miao: Verifiable Coded-Sharding Federated Unlearning\}", r"\\markboth{Submitted for IEEE journal review}%\n{Anonymous Authors: Verifiable Coded-Sharding Federated Unlearning}", s, count=1)
s=s.replace('Full retraining is expected to provide the closest semantic reference but incurs the largest deletion latency because it repeats training after removing the deleted clients. No-unlearning is expected to have the lowest latency but violates deletion correctness and should exhibit poor forgetting behavior on deleted clients.', 'Full retraining serves as the closest semantic reference but incurs the largest deletion latency because it repeats training after removing the deleted clients. No-unlearning provides an invalid lower bound on latency because it ignores the deletion request and should exhibit poor forgetting behavior on deleted clients.')
s=s.replace('We summarize the expected cost as', 'We summarize the asymptotic cost as')
p.write_text(s,encoding='utf-8')
print('patched header and expected wording')
