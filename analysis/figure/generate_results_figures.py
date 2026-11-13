"""Rebuild paper figures from frozen per-clip predictions; no model calls.
Run: python figure/generate_results_figures.py (from paper/, or any directory).
Requires numpy, matplotlib. Outputs PDF/SVG/PNG, editable TeX tables and JSON.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

OUT = Path(__file__).resolve().parent
PAPER = OUT.parent
OLD = PAPER / 'results1046_snapshot_20261030T093341Z/results/paper_suite_v1'
NEW = PAPER / 'completed_experiments_20261101'
SOURCES = {}

def read(path):
    raw = path.read_bytes()
    SOURCES[str(path.relative_to(PAPER)).replace('\\', '/')] = hashlib.sha256(raw).hexdigest()
    if path.suffix == '.jsonl':
        return [json.loads(line) for line in raw.decode('utf-8-sig').splitlines()]
    return json.loads(raw.decode('utf-8-sig'))

main = read(OLD / 'main/predictions.jsonl')
reference = {r['key']: (r['label'], r['subject']) for r in main}
assert len(reference) == len(main) == 1046
def group(path):
    rows = read(path / 'predictions.jsonl')
    assert len(rows) == len({r['key'] for r in rows}) == 1046
    assert {r['key']: (r['label'], r['subject']) for r in rows} == reference
    summary = read(path / 'summary.json')
    return rows, summary.get('cohorts', {}).get('full1046', summary)

def metrics(rows, arm, baseline='numeric_baseline'):
    y = np.array([r['label'] for r in rows])
    p = np.array([r['predictions'][arm] for r in rows])
    b = np.array([r['predictions'][baseline] for r in rows])
    a = np.array([not r['rejected'] for r in rows])
    f1 = []
    for c in range(40):
        tp = np.sum((p == c) & (y == c)); fp = np.sum((p == c) & (y != c)); fn = np.sum((p != c) & (y == c))
        f1.append(float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 0.)
    fixed = int(np.sum((b != y) & (p == y))); broken = int(np.sum((b == y) & (p != y)))
    return dict(correct=int(np.sum(p == y)), accuracy=float(np.mean(p == y)), macro_f1=float(np.mean(f1)),
                fixed=fixed, broken=broken, net=fixed-broken, accepted=int(a.sum()),
                accepted_correct=int(np.sum(a & (p == y))), coverage=float(a.mean()),
                accepted_accuracy=float(np.mean((p == y)[a])))

def verify(rows, summary):
    for arm, saved in summary['arms'].items():
        got = metrics(rows, arm)
        for k, v in got.items():
            if k in saved:
                assert np.isclose(v, saved[k], atol=1e-10), (arm, k, v, saved[k])

main_summary = read(OLD / 'main/summary.json'); verify(main, main_summary)
recheck, recheck_summary = group(NEW / 'tables/recheck_full'); verify(recheck, recheck_summary)
protection, protection_summary = group(OLD / 'protection'); verify(protection, protection_summary)
conditions = ['clean','missing_depth','missing_ir','missing_thermal','mismatch_ir','observation_blur_light','observation_blur_heavy']
robust = {}
for condition in conditions:
    rows, summary = group(NEW / 'tables/robust_full' / condition)
    verify(rows, summary); robust[condition] = rows
hetero = {}
for variant in ['heterogeneous','qwen_pair','gemma_pair']:
    rows, summary = group(NEW / 'tables/heterogeneity/1046' / variant)
    verify(rows, summary); hetero[variant] = rows
audit = read(NEW / 'audit.json')
failures = {g['group'].split('/')[-1]: g['protocol_failure_reports'] for g in audit['groups'] if g['group'].startswith('heterogeneity/')}

# Verify matching primary protocols across bundles, not just matching totals.
by_key = {r['key']: r for r in main}
for r in recheck:
    for new_arm, old_arm in [('numeric_baseline','numeric_baseline'),('debate','anchored_three_agent'),('debate_rule','rule_balanced')]:
        assert r['predictions'][new_arm] == by_key[r['key']]['predictions'][old_arm]
    assert r['rejected'] == by_key[r['key']]['rejected']

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
                     'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,
                     'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,
                     'axes.linewidth':.6,'lines.linewidth':1.4,'savefig.facecolor':'white'})
COL = {'Baseline':'#666666','Unprotected':'#D55E00','Rule guard':'#0072B2','Learned guard':'#009E73'}
arms = ['numeric_baseline','anchored_three_agent','rule_balanced','learned_balanced']
names = ['Baseline','Unprotected','Rule guard','Learned guard']
data = {'n':1046, 'main':{a:metrics(main,a) for a in arms}}
def save(fig, name):
    for ext in ['pdf','svg','png']:
        fig.savefig(OUT / f'{name}.{ext}', dpi=300)
    plt.close(fig)

# Figure 2: common baseline versus a distinct direct method-to-method comparison.
fig, ax = plt.subplots(1,2,figsize=(7.2,3.1),layout='constrained',gridspec_kw={'width_ratios':[1.2,1]})
for i, (arm,name) in enumerate(zip(arms[1:],names[1:])):
    m = metrics(main,arm)
    ax[0].bar(i,m['fixed'],color=COL[name],width=.58)
    ax[0].bar(i,-m['broken'],color=COL[name],alpha=.35,hatch='//',width=.58)
    ax[0].scatter(i,m['net'],c='black',marker='D',s=22,zorder=3)
    ax[0].text(i,m['fixed']+8,str(m['fixed']),ha='center',fontsize=8)
    ax[0].text(i,-m['broken']-18,str(-m['broken']),ha='center',fontsize=8)
    ax[0].annotate(f"+{m['net']}",(i,m['net']),xytext=(9,0),textcoords='offset points',fontsize=7)
ax[0].axhline(0,c='black',lw=.6); ax[0].set_xticks(range(3),['Unprotected','Rule guard','Learned guard'])
ax[0].set_ylim(-210,225); ax[0].set_ylabel('Clips relative to numerical baseline')
ax[0].set_title('(a) Beneficial and harmful revisions',loc='left')
ax[0].text(.02,.02,'Solid: corrections   Hatched: harms   Diamond: net',transform=ax[0].transAxes,fontsize=6.5)
trans = metrics(main,'rule_balanced','anchored_three_agent'); data['unprotected_to_rule'] = trans
vals=[trans['fixed'],-trans['broken'],trans['net']]
ax[1].bar(range(3),vals,color=['#0072B2','#D55E00','#333333'],width=.6)
for i,v in enumerate(vals): ax[1].text(i,v+(3 if v>=0 else -6),f'{v:+d}',ha='center')
ax[1].set_xticks(range(3),['Wrong to\ncorrect','Correct to\nwrong','Net gain'])
ax[1].axhline(0,c='black',lw=.6); ax[1].set_ylim(-40,75)
ax[1].set_ylabel('Clips relative to unprotected debate')
ax[1].set_title('(b) Switching to the rule guard',loc='left')
save(fig,'fig2_correction_benefits_harms')

def paired(rows, before, after):
    subjects=sorted({r['subject'] for r in rows}); sizes=[]; nums=[]
    for s in subjects:
        sub=[r for r in rows if r['subject']==s]; sizes.append(len(sub))
        nums.append(sum(int(r['predictions'][after]==r['label'])-int(r['predictions'][before]==r['label']) for r in sub))
    sizes=np.array(sizes); nums=np.array(nums)
    idx=np.random.default_rng(42).integers(0,len(subjects),size=(2000,len(subjects)))
    ci=np.quantile(nums[idx].sum(1)/sizes[idx].sum(1),[.025,.975])*100
    return dict(delta=float(nums.sum()/sizes.sum()*100),ci=ci.tolist(),subjects=subjects,n=sizes.tolist(),subject_delta=(nums/sizes*100).tolist())

comparisons=[(main,'numeric_baseline','rule_balanced','Rule guard vs baseline'),
             (recheck,'direct_rule','debate_rule','Protected debate vs direct'),
             (recheck,'independent_recheck_rule','debate_rule','Protected debate vs reinspection'),
             (recheck,'independent_recheck','debate','Unprotected debate vs reinspection')]
pairs=[paired(r,b,a) for r,b,a,_ in comparisons]; data['paired_comparisons']={c[3]:v for c,v in zip(comparisons,pairs)}
saved_recheck=read(NEW/'tables/recheck_full/summary.json')['comparisons']
for index,key in [(2,'independent_recheck_rule->debate_rule'),(3,'independent_recheck->debate')]:
    assert np.allclose(np.array(pairs[index]['ci'])/100,saved_recheck[key]['subject_cluster_bootstrap_95ci'])
for index,path,key in [(0,OLD/'main/summary.json','rule_balanced'),(1,OLD/'debate/summary.json','direct_rule->debate_rule')]:
    assert np.allclose(np.array(pairs[index]['ci'])/100,read(path)['comparisons'][key]['subject_cluster_bootstrap_95ci'])
fig,ax=plt.subplots(1,2,figsize=(7.2,3.9),layout='constrained',gridspec_kw={'width_ratios':[1.5,1]})
comparison_colors=['#0072B2','#009E73','#CC79A7','#D55E00']; markers=['o','s','D','^']
for i,p in enumerate(pairs):
    lo,hi=p['ci']; ax[0].errorbar(p['delta'],i,xerr=[[p['delta']-lo],[hi-p['delta']]],fmt=markers[i],color=comparison_colors[i],capsize=3)
    ax[0].text(12.0,i+.24,f"{p['delta']:+.2f} [{lo:+.2f}, {hi:+.2f}]",va='center',ha='right',fontsize=6.5)
ax[0].set_yticks(range(4),['Rule guard\nvs baseline','Protected debate\nvs direct','Protected debate\nvs reinspection','Unprotected debate\nvs reinspection'])
ax[0].set_ylim(3.6,-.6); ax[0].set_xlim(-2,12.4); ax[0].axvline(0,c='gray',ls='--',lw=.8)
ax[0].set_xlabel('Accuracy difference (percentage points)'); ax[0].set_title('(a) Paired differences (95% intervals)',loc='left')
for i,p in enumerate(pairs):
    ax[1].scatter(p['subject_delta'],np.arange(6)+(i-1.5)*.14,color=comparison_colors[i],marker=markers[i],s=20)
ax[1].set_yticks(range(6),[f'{s} (n={n})' for s,n in zip(pairs[0]['subjects'],pairs[0]['n'])]); ax[1].invert_yaxis()
ax[1].axvline(0,c='gray',ls='--',lw=.8); ax[1].set_xlabel('Accuracy difference (pp)'); ax[1].set_title('(b) Subject differences',loc='left')
save(fig,'fig3_paired_differences')

fig,ax=plt.subplots(1,2,figsize=(7.2,3.2),layout='constrained',gridspec_kw={'width_ratios':[1.1,1]})
r_arms=['numeric_baseline','debate','debate_rule']; r_names=names[:3]
robust_values={c:{a:metrics(rows,a) for a in r_arms} for c,rows in robust.items()}; data['robustness']=robust_values
for i,(arm,name,marker) in enumerate(zip(r_arms,r_names,['o','^','s'])):
    ax[0].scatter([robust_values[c][arm]['accuracy']*100 for c in conditions[:5]],np.arange(5)+(i-1)*.18,color=COL[name],marker=marker,s=25,label=name)
    ax[1].plot(range(3),[robust_values[c][arm]['accuracy']*100 for c in ['clean','observation_blur_light','observation_blur_heavy']],marker=marker,color=COL[name],label=name)
ax[0].set_yticks(range(5),['Complete','Missing depth','Missing IR','Missing thermal','IR clip mismatch']); ax[0].invert_yaxis()
ax[0].set_xlabel('Accuracy (%)'); ax[0].set_xlim(20,51); ax[0].grid(axis='x',alpha=.2)
ax[0].set_title('(a) Modality availability and mismatch',loc='left')
ax[1].set_xticks(range(3),['Complete','Light blur','Heavy blur']); ax[1].set_ylim(20,51)
ax[1].set_ylabel('Accuracy (%)'); ax[1].grid(axis='y',alpha=.2); ax[1].legend(loc='lower left',frameon=False)
ax[1].set_title('(b) Observation-only degradation',loc='left')
save(fig,'fig4_input_robustness')

fig,ax=plt.subplots(1,2,figsize=(7.2,3.6),layout='constrained',gridspec_kw={'width_ratios':[1.1,1]})
ordered=sorted(main,key=lambda r:(-r['confidence'],r['key'])); risk_saved=read(OLD/'risk/summary.json')['arms']; data['aurc']={}
for arm,name in zip(arms,names):
    err=np.array([r['predictions'][arm]!=r['label'] for r in ordered]); risk=err.cumsum()/np.arange(1,1047)
    area=float(risk.mean()); assert np.isclose(area,risk_saved[arm]['aurc'],atol=1e-12); data['aurc'][arm]=area
    ax[0].plot(np.arange(1,1047)/1046,risk,color=COL[name],label=f'{name} ({area:.4f})',lw=1.1,ls='--' if name=='Learned guard' else '-')
ax[0].xaxis.set_major_formatter(PercentFormatter(1)); ax[0].set_xlim(0,1); ax[0].set_ylim(0,1)
ax[0].set_xlabel('Coverage'); ax[0].set_ylabel('Selective risk'); ax[0].legend(frameon=False,loc='upper left',title='Method (AURC)',title_fontsize=7)
ax[0].set_title('(a) Shared numerical confidence ranking',loc='left')
parts=[]
for arm in ['numeric_baseline','rule_balanced']:
    m=metrics(main,arm); parts.append([m['accepted_correct'],m['accepted']-m['accepted_correct'],m['correct']-m['accepted_correct'],1046-m['accepted']-m['correct']+m['accepted_correct']])
data['acceptance_decomposition']=parts
labels=['Accepted, correct','Accepted, wrong','Rejected, internally correct','Rejected, internally wrong']
colors=['#0072B2','#D55E00','#A9CEE5','#EBC3AC']; left=np.zeros(2)
for j in range(4):
    vals=np.array(parts)[:,j]/1046
    ax[1].barh(range(2),vals,left=left,color=colors[j],height=.42,label=labels[j],edgecolor='white',linewidth=.5)
    for i,v in enumerate(vals): ax[1].text(left[i]+v/2,i,str(parts[i][j]),ha='center',va='center',color='white' if j<2 else 'black',fontsize=7)
    left+=vals
ax[1].set_yticks(range(2),['Baseline','Rule guard']); ax[1].set_ylim(1.8,-.7); ax[1].set_xlim(0,1)
ax[1].axvline(770/1046,c='black',ls='--',lw=.8); ax[1].text(770/1046,-.48,'73.61%',ha='center',fontsize=7)
ax[1].xaxis.set_major_formatter(PercentFormatter(1)); ax[1].set_xlabel('Fraction of all 1,046 clips')
ax[1].legend(frameon=False,loc='lower left',fontsize=6.5); ax[1].set_title('(b) Fixed acceptance, counts in segments',loc='left')
save(fig,'fig5_selective_prediction')

# Supplementary figures do not require external raw images or unfilled human ratings.
class_counts=Counter(r['label'] for r in main); subject_counts=Counter(r['subject'] for r in main)
fig,ax=plt.subplots(1,2,figsize=(7.2,3),layout='constrained',gridspec_kw={'width_ratios':[1.6,1]})
ax[0].bar(range(40),[class_counts[c] for c in range(40)],color='#0072B2'); ax[0].set_xticks(range(0,40,5))
ax[0].set_xlabel('Activity class ID'); ax[0].set_ylabel('Clips'); ax[0].set_title('(a) Class distribution',loc='left')
subjects=sorted(subject_counts); ax[1].barh(subjects,[subject_counts[s] for s in subjects],color='#666666')
for i,s in enumerate(subjects): ax[1].text(subject_counts[s]+3,i,str(subject_counts[s]),va='center',fontsize=7)
ax[1].set_xlim(0,max(subject_counts.values())*1.25); ax[1].set_xlabel('Clips'); ax[1].set_title('(b) Subject distribution',loc='left')
save(fig,'figS1_cohort_distribution')
ablation_arms=['rule_balanced','without_independent','without_modality','without_confidence','learned_balanced']
ablation_names=['Full rule guard','Without initial-opinion protection','Without modality support','Without confidence cap','Learned guard']
data['ablation']={a:metrics(protection,a) for a in ablation_arms}
fig,ax=plt.subplots(figsize=(5.2,3.5),layout='constrained')
for i,(a,n) in enumerate(zip(ablation_arms,ablation_names)):
    m=data['ablation'][a]; ax.scatter(m['broken'],m['fixed'],s=35,marker=['o','s','^','D','v'][i],color=['#0072B2','#E69F00','#CC79A7','#666666','#009E73'][i],label=n)
ax.set_xlabel('Harmful revisions'); ax.set_ylabel('Beneficial corrections'); ax.set_title('Guard trade-offs relative to numerical baseline',loc='left')
ax.grid(alpha=.2); ax.legend(loc='lower right',fontsize=6.5,frameon=False); ax.set_ylim(145,190)
save(fig,'figS2_guard_tradeoffs')
recall=[]
for c in range(40):
    rows=[r for r in main if r['label']==c]
    recall.append(100*np.mean([int(r['predictions']['rule_balanced']==c)-int(r['predictions']['numeric_baseline']==c) for r in rows]))
fig,ax=plt.subplots(2,1,figsize=(7.2,4),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[2,1]})
ax[0].bar(range(40),recall,color=['#0072B2' if x>=0 else '#D55E00' for x in recall]); ax[0].axhline(0,c='black',lw=.6)
ax[0].set_ylabel('Recall difference (pp)'); ax[0].set_title('Rule guard minus numerical baseline',loc='left')
ax[1].bar(range(40),[class_counts[c] for c in range(40)],color='#777777')
for c in range(40): ax[1].text(c,class_counts[c]+2,str(class_counts[c]),ha='center',fontsize=5.5,rotation=90)
ax[1].set_ylim(0,180); ax[1].set_xticks(range(40)); ax[1].tick_params(axis='x',labelsize=5.5); ax[1].set_xlabel('Activity class ID'); ax[1].set_ylabel('Clips')
save(fig,'figS3_class_recall')

# Native LaTeX tables (no rasterized text); row values are all computed above.
def table(filename,caption,label,headers,rows):
    from table_emphasis import emphasize, NOTES
    rows = emphasize(filename, rows)
    caption += ' ' + NOTES.get(filename, '')
    lines=[r'\begin{table*}[pos=t]',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\centering\small',
           r'\begin{tabular}{@{}l'+('r'*(len(headers)-1))+r'@{}}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule']
    lines += [' & '.join(map(str,row))+r' \\' for row in rows]
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table*}']
    (OUT/filename).write_text('\n'.join(lines)+'\n',encoding='utf-8')
def perfrow(name,m): return [name,m['correct'],f"{100*m['accuracy']:.2f}",f"{100*m['macro_f1']:.2f}",m['fixed'],m['broken'],f"{m['net']:+d}"]
table('table_results_main.tex','Overall performance on all 1,046 clips. Corrections and harms are relative to the numerical baseline. Missing unimodal predictions count as incorrect; available denominators are given in Table~\\ref{tab:cohort}.','tab:results_main',
      ['Method','Correct',r'Acc. (\%)',r'Macro-F1 (\%)','Corrections','Harms','Net'],
      [perfrow(n,metrics(main,a)) for a,n in [('depth','Depth'),('ir','IR'),('thermal','Thermal'),('mean_fusion','Mean fusion')]+list(zip(arms,names))])
table('table_results_ablation.tex','Guard ablations on identical discussion outputs. Corrections and harms are relative to the numerical baseline.','tab:results_ablation',
      ['Configuration','Correct',r'Acc. (\%)',r'Macro-F1 (\%)','Corrections','Harms','Net'],
      [perfrow(n,data['ablation'][a]) for a,n in zip(ablation_arms,ablation_names)])
rows=[]; data['heterogeneity']={}
robust_rows=[]
condition_names=['Complete','Missing depth','Missing IR','Missing thermal','IR clip mismatch','Light observation blur','Heavy observation blur']
for c,n in zip(conditions,condition_names):
    comparison=paired(robust[c],'numeric_baseline','debate_rule')
    lo,hi=comparison['ci']
    low_text=f'{lo:+.3f}' if 0 < abs(lo) < .005 else f'{lo:+.2f}'
    robust_rows.append([n]+[f"{robust_values[c][a]['accuracy']*100:.2f}" for a in r_arms]+[f"{comparison['delta']:+.2f}",f'[{low_text}, {hi:+.2f}]'])
table('table_results_robustness.tex','Accuracy under seven input conditions, each with 1,046 clips. Differences compare the rule guard with the same-condition numerical baseline. Intervals use subject-clustered resampling; all differences and interval bounds are in percentage points.','tab:results_robustness',
      ['Condition',r'Baseline (\%)',r'Unprotected (\%)',r'Rule guard (\%)','Difference',r'95\% interval'],robust_rows)
for v,n in [('heterogeneous','Heterogeneous'),('qwen_pair','Qwen pair'),('gemma_pair','Gemma pair')]:
    data['heterogeneity'][v]={}
    for arm,suffix in [('debate','Unprotected'),('debate_rule','Rule guard')]:
        m=metrics(hetero[v],arm); data['heterogeneity'][v][arm]=m
        rows.append([f'{n}: {suffix}',f"{m['accuracy']*100:.2f}",f"{m['macro_f1']*100:.2f}",m['fixed'],m['broken'],failures[v]])
table('table_model_composition.tex','Controlled observer-model composition on 1,046 clips. All variants use the same distinct observer-role prompts and text auditor. These prompts differ from the primary experiment. Protocol failures are report counts shared by both guard settings, not additional failures caused by protection.','tab:model_composition',
      ['Observer configuration',r'Acc. (\%)',r'Macro-F1 (\%)','Corrections','Harms','Failures'],rows)
data['verification']={'status':'passed','checks':['1046 unique aligned keys/labels/subjects in every group','Recomputed accuracy, macro-F1, correction/harms and acceptance counts match summaries','Primary predictions identical between old snapshot and completed reinspection bundle','Four paired bootstrap intervals match archived intervals','All four AURC values recomputed from individual predictions match archived values'],
                      'bootstrap':{'resamples':2000,'seed':42,'unit':'subject','percentiles':[2.5,97.5]},'sources_sha256':SOURCES}
(OUT/'results_figure_data.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
captions = {
 'fig2_correction_benefits_harms': 'Benefits and harms of baseline-anchored correction on 1,046 clips. (a) Beneficial corrections, harmful revisions, and net corrections relative to the numerical baseline. (b) Paired transitions when replacing unprotected debate with the rule guard: 53 incorrect predictions become correct, while 23 correct predictions become incorrect. Failed protocols retain their prescribed numerical fallback. The reference method differs between panels.',
 'fig3_paired_differences': 'Paired accuracy differences and subject-level variability. (a) Point estimates and 95\\% subject-clustered bootstrap intervals (2,000 resamples; seed 42). Each difference is the first named method minus the second; direct and reinspection comparators in protected comparisons also use the rule guard. (b) The corresponding differences for each of six subjects, with sample counts. Colors and symbols identify the same comparisons in both panels. Only debate and reinspection are matched at six logical calls; direct arbitration uses three. Intervals are descriptive for this exploratory cohort and do not remove selection bias.',
 'fig4_input_robustness': 'Performance under missing, degraded, and mismatched inputs. Each condition contains 1,046 clips. (a) Accuracy under modality removal and synthetic cross-clip IR replacement. (b) Accuracy as agent observations are increasingly blurred. Blur affects only the observation branch, leaving numerical probabilities unchanged. Synthetic IR mismatch is not physical temporal misalignment. Protection mitigates severe-blur damage but remains below the numerical baseline.',
 'fig5_selective_prediction': 'Classification quality and selective prediction. (a) Risk--coverage curves and AURC computed from a shared numerical-confidence ranking, with ties resolved by sample key. Curves do not measure calibration of agent probabilities. (b) Outcome decomposition over all 1,046 clips; numbers within bars are clip counts. Both methods accept the same 770 clips (73.61\\% coverage). Correct accepted outputs increase by a net 50, without changing the acceptance set. Rejected outcomes refer to internal predictions.',
 'figS1_cohort_distribution': 'Distribution of clips across 40 activity classes and six subjects in the 1,046-clip cohort. Activity class IDs follow the prediction-label vocabulary. The class imbalance motivates reporting macro-F1 alongside accuracy.',
 'figS2_guard_tradeoffs': 'Beneficial corrections versus harmful revisions, each relative to the numerical baseline. Points compare the full rule guard, three single-condition removals, and the learned guard. Higher correction counts and lower harm counts are desirable, but individual constraints trade off both quantities.',
 'figS3_class_recall': 'Class-specific recall changes for the rule guard relative to the numerical baseline, with sample counts below. Differences are in percentage points. Large changes in classes with very few clips, particularly class 25 with three clips, should not be interpreted as stable class-level effects.'
}
preview = [r'\documentclass[a4paper]{article}',r'\usepackage[margin=16mm]{geometry}',r'\usepackage[T1]{fontenc}',r'\usepackage{graphicx,booktabs,hyperref}',
           r'\graphicspath{{figure/}}',r'\begin{document}',r'\setcounter{figure}{1}']
for name, caption in captions.items():
    code = '\n'.join([r'\begin{figure*}[pos=t]',r'\centering',r'\includegraphics[width=\textwidth]{'+name+'.pdf}',r'\caption{'+caption+'}',r'\label{fig:'+name+'}',r'\end{figure*}'])
    (OUT/(name+'.tex')).write_text(code+'\n',encoding='utf-8')
    if name.startswith('figS1'):
        preview += [r'\setcounter{figure}{0}',r'\renewcommand{\thefigure}{S\arabic{figure}}']
    preview += [code.replace('figure*','figure').replace('[pos=t]','[htbp]'),r'\clearpage']
preview += [r'\setcounter{table}{3}']
for name in ['table_results_main.tex','table_results_ablation.tex','table_model_composition.tex','table_results_robustness.tex']:
    preview += [(OUT/name).read_text().replace('table*','table').replace('[pos=t]','[htbp]'),r'\clearpage']
preview += [r'\end{document}']
# The standalone preview has no Chapter 4 table; keep its caption self-contained.
preview_text='\n'.join(preview).replace(r'available denominators are given in Table~\ref{tab:cohort}', 'available denominators are 980 (depth), 981 (IR), and 1,019 (thermal)')
(OUT/'results_figures_preview.tex').write_text(preview_text+'\n',encoding='utf-8')
(OUT/'results_figure_captions.txt').write_text('\n\n'.join(k+'\n'+v for k,v in captions.items())+'\n',encoding='utf-8')
print('Generated 7 figures (PDF/SVG/PNG), 4 editable LaTeX tables, and verified figure data.')
