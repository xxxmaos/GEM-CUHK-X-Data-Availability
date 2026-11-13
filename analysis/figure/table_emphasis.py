"""Consistent, numeric emphasis for manuscript result tables."""
NOTES = {
    'table_results_main.tex': 'Bold highlights the proposed guarded methods, not column-wise maxima. The rule guard gains 6.12 percentage points over the baseline and reduces harms by 34.2 percent relative to unprotected debate.',
    'table_results_ablation.tex': 'Bold identifies the complete proposed rule guard as the reference configuration; ablated variants can achieve higher accuracy.',
    'table_model_composition.tex': 'Bold highlights accuracy, macro-F1, and harms with the proposed protection in each assignment; it does not indicate the best model assignment.',
    'table_results_robustness.tex': 'Bold highlights the proposed rule guard and its change from the numerical baseline, including the negative change under heavy blur.',
}

def emphasize(filename, rows):
    rows = [[str(x) for x in row] for row in rows]
    for row in rows:
        cols = []
        if filename == 'table_results_main.tex' and row[0] in ('Rule guard', 'Learned guard'):
            cols = range(len(row))
        elif filename == 'table_results_ablation.tex' and row[0] == 'Full rule guard':
            cols = range(len(row))
        elif filename == 'table_model_composition.tex' and row[0].endswith('Rule guard'):
            cols = (0, 1, 2, 4)
        elif filename == 'table_results_robustness.tex':
            cols = (3, 4)
        for j in cols:
            row[j] = r'\textbf{' + row[j] + '}'
    return rows

if __name__ == '__main__':
    import re
    from pathlib import Path
    folder = Path(__file__).resolve().parent
    for filename, note in NOTES.items():
        path = folder / filename
        text = path.read_text(encoding='utf-8-sig')
        text = re.sub(r' Bold (?:marks|highlights|identifies)[^\n]*?(?=\}\n\\label)', '', text)
        before, rest = text.split('\\midrule\n', 1)
        body, after = rest.split('\\bottomrule', 1)
        body = re.sub(r'\\textbf\{([^{}]*)\}', r'\1', body)
        rows = [line.strip().removesuffix(r'\\').strip().split(' & ') for line in body.strip().splitlines()]
        lines = [' & '.join(row) + r' \\' for row in emphasize(filename, rows)]
        if note not in before:
            before = before.replace('\n\\label', '\n\\label', 1)
            before = before.replace('}\n\\label', ' ' + note + '}\n\\label', 1)
        path.write_text(before+'\\midrule\n'+'\n'.join(lines)+'\n\\bottomrule'+after, encoding='utf-8')
