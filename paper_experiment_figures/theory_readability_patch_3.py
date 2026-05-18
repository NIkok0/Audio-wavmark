from pathlib import Path
p = Path(r'E:\down\main-1.tex')
s = p.read_text(encoding='utf-8')
old = r'''The affected-shard retraining proof $\pi_{rt}$ certifies the
execution and integration correctness of the retraining step
used to replace the affected shard. Its purpose is not to prove
semantic forgetting directly, but to bind the retrained checkpoint
inserted into the coded-sharding trace to the declared deletion
state and retraining procedure. The proof starts from the
committed affected-shard input checkpoint, excludes the target
client $a$, and certifies that the output checkpoint is generated
under the public retraining configuration $\mathsf{TrainCfg}$ and
the previous deletion-set root $r_{U,t-1}$.

The retraining proof is linked to the coded-sharding proof through
the public binding tuple
'''
new = r'''Given the retraining-proof interface above, the coded-sharding
proof links the inserted affected-shard row to the retraining
backend through the public binding tuple
'''
if old not in s:
    raise SystemExit('rt duplicate paragraph not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('compressed duplicate rt binding text')
