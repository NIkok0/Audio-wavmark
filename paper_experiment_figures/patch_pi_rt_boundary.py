from pathlib import Path
p = Path(r'E:\down\main-2.tex')
s = p.read_text(encoding='utf-8')

old_boundary = '''A weak prototype instantiation may use a hash-bound retraining
certificate, which binds the supplied output shard to the target
identity, input checkpoint, deletion root, and retraining
configuration. This weak instantiation validates transcript
integration but does not prove that the retraining computation was
executed step by step. A strong deployment instantiates $\\pi_{rt}$
with a sound training-integrity proof that certifies the declared
retraining computation after excluding $a$. The security theorem is
modular: its retraining-correctness component relies on the soundness
guarantee provided by the chosen $\\pi_{rt}$ backend.
'''
new_boundary = '''The strength of the retraining claim is inherited from the
chosen $\\pi_{rt}$ backend. A weak prototype instantiation may use a
hash-bound retraining certificate, which binds the supplied output
shard to the target identity, input checkpoint, deletion root, and
retraining configuration. This weak instantiation validates transcript
integration and output binding, but it does not prove that the
retraining computation was executed step by step. A strong deployment
instantiates $\\pi_{rt}$ with a sound training-integrity proof that
certifies the declared retraining computation after excluding $a$.
Accordingly, the security theorem should be read modularly: the
coded-sharding proof establishes integration of the replacement row,
while retraining-computation correctness is exactly as strong as the
soundness guarantee provided by the selected $\\pi_{rt}$ backend.
'''
if old_boundary not in s:
    raise SystemExit('boundary paragraph not found')
s = s.replace(old_boundary, new_boundary, 1)

old_theorem = '''coded-sharding trace in~\\eqref{eq:core-transition-trace}; (iv) the replacement row is
bound to a valid retraining proof with the same $a$, $s^\\star$,
input checkpoint hash, output shard hash, and deletion-set root
$r_{U,t-1}$; (v) $a\\in U_t$ and $a\\notin A_t$; and (vi) later
'''
new_theorem = '''coded-sharding trace in~\\eqref{eq:core-transition-trace}; (iv) the replacement row is
bound to the retraining backend through the same public tuple
$(a,s^\\star,h_{in},h_{out},r_{U,t-1},\\mathsf{TrainCfg})$, and the
strength of the retraining-correctness claim is inherited from the
soundness of the chosen $\\pi_{rt}$ backend; (v) $a\\in U_t$ and
$a\\notin A_t$; and (vi) later
'''
if old_theorem not in s:
    raise SystemExit('theorem item iv block not found')
s = s.replace(old_theorem, new_theorem, 1)

s = s.replace('Unaffected-shard preservation & Correctness of a weak hash-only retraining certificate \\\\',
              'Unaffected-shard preservation & Step-by-step retraining correctness when $\\pi_{rt}$ is only hash-bound \\\\')

# Tighten nearby security-boundary prose to mention modular pi_rt explicitly.
old_sec_boundary = '''the latest deletion root. We do not claim that the theorem proves
perfect semantic deletion, distributional indistinguishability
from full retraining, or immunity to fresh-identity Sybil
re-registration.'''
new_sec_boundary = '''the latest deletion root. The retraining component is modular: a
hash-bound $\\pi_{rt}$ proves replacement-output binding, whereas a
training-integrity $\\pi_{rt}$ is required for step-by-step retraining
correctness. We do not claim that the theorem proves perfect semantic
deletion, distributional indistinguishability from full retraining, or
immunity to fresh-identity Sybil re-registration.'''
if old_sec_boundary not in s:
    raise SystemExit('security boundary prose not found')
s = s.replace(old_sec_boundary, new_sec_boundary, 1)

p.write_text(s, encoding='utf-8')
print('patched pi_rt modular security wording')
