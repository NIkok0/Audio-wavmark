from pathlib import Path
p=Path(r'E:\down\main.tex')
s=p.read_text(encoding='utf-8')
# Remove the duplicate graphicx package occurrence, keeping the first one.
first = s.find('\\usepackage{graphicx}')
second = s.find('\\usepackage{graphicx}', first + 1)
if second != -1:
    s = s[:second] + s[second + len('\\usepackage{graphicx}\n'):]
# Avoid unresolved cross-file appendix labels when main.tex is compiled standalone.
s=s.replace('given in Appendix~\\ref{app:matrixized-cszk}.', 'given in the supplementary appendix.')
s=s.replace('given in Appendix~\\ref{app:matrixized-cszk}', 'given in the supplementary appendix')
# Consistent model notation.
s=s.replace('\\|w_{\\mathsf{unlearn}}-w_{\\mathsf{retrain}}\\|_2', '\\|w^u-w^{-a}\\|_2')
s=s.replace('\\makecell{$\\|w_u-w_r\\|_2$}', '\\makecell{$\\|w^u-w^{-a}\\|_2$}')
# Remove remaining casual expected wording in the experiment narrative.
s=s.replace('The client population size is varied over', 'The client population size is varied over')
s=s.replace('Full retraining serves as the closest semantic reference but incurs the largest deletion latency because it repeats training after removing the deleted clients. No-unlearning provides an invalid lower bound on latency because it ignores the deletion request and should exhibit poor forgetting behavior on deleted clients.', 'Full retraining serves as the closest semantic reference but incurs the largest deletion latency because it repeats training after removing the deleted clients. No-unlearning provides an invalid lower bound on latency because it ignores the deletion request and is included only to expose the cost of non-compliance.')
p.write_text(s, encoding='utf-8')
print('patched final main cleanup')
