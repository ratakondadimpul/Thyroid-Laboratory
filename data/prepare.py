"""
Prepare thyroid0387.data -> processed CSV for training & demo uploads
- Parses 29 attrs + diagnosis string (e.g., 'G', 'AK', '-')
- Maps to Overall: Positive (A-H) vs Negative ('-') vs Other (I,J,K,R... handled as Negative for binary but keep original)
- Category: hyperthyroid/hypothyroid sub-types
"""
import pathlib, re, csv, json, collections
ROOT = pathlib.Path(__file__).parent
RAW = ROOT / "raw" / "thyroid0387.data"
OUT_CSV = ROOT / "processed" / "thyroid0387_processed.csv"
OUT_SAMPLE = ROOT / "processed" / "sample_lab.csv"
OUT_LABEL_MAP = ROOT / "processed" / "label_encoding.json"

ATTRS = [
 "age","sex","on_thyroxine","query_on_thyroxine","on_antithyroid_medication","sick","pregnant",
 "thyroid_surgery","I131_treatment","query_hypothyroid","query_hyperthyroid","lithium","goitre",
 "tumor","hypopituitary","psych","TSH_measured","TSH","T3_measured","T3","TT4_measured","TT4",
 "T4U_measured","T4U","FTI_measured","FTI","TBG_measured","TBG","referral_source"
]

# Diagnosis mapping per thyroid0387.names
LETTER_MAP = {
 'A': 'hyperthyroid','B':'T3_toxic','C':'toxic_goitre','D':'secondary_toxic',
 'E':'hypothyroid','F':'primary_hypothyroid','G':'compensated_hypothyroid','H':'secondary_hypothyroid',
 'I':'increased_binding_protein','J':'decreased_binding_protein','K':'concurrent_non_thyroidal_illness',
 'L':'replacement_therapy','M':'underreplaced','N':'overreplaced','O':'antithyroid_drugs',
 'P':'I131_treatment_effect','Q':'surgery_effect','R':'discordant_results','S':'elevated_TBG','T':'elevated_thyroid_hormones'
}
HYPER_LETTERS = set('ABCD')
HYPO_LETTERS = set('EFGH')

def parse_diagnosis(raw):
    diag = raw.split('[')[0].strip()
    if diag == '-':
        return {'raw': '-', 'overall': 'Negative', 'category': 'negative', 'risk': 'Lower Risk', 'letters': []}
    # remove '|Y' keep more likely Y? spec: X|Y = consistent with X but more likely Y
    # take last part after |
    if '|' in diag:
        diag = diag.split('|')[-1]
    letters = list(diag)
    # Determine overall
    if any(l in HYPER_LETTERS or l in HYPO_LETTERS for l in letters):
        overall = 'Positive'
        # pick first hypo/hyper letter for category
        hyp = [l for l in letters if l in HYPO_LETTERS]
        hyp_hyp = [l for l in letters if l in HYPER_LETTERS]
        if hyp:
            cat_letter = hyp[0]
        elif hyp_hyp:
            cat_letter = hyp_hyp[0]
        else:
            cat_letter = letters[0]
        category = LETTER_MAP.get(cat_letter, cat_letter)
        # normalize to hypo/hyper buckets
        if cat_letter in HYPO_LETTERS:
            bucket = 'hypothyroid'
        elif cat_letter in HYPER_LETTERS:
            bucket = 'hyperthyroid'
        else:
            bucket = category
    else:
        # binding protein / general health etc -> treat as Negative for binary but keep category
        overall = 'Negative'
        bucket = LETTER_MAP.get(letters[0], letters[0]) if letters else 'other'
        category = bucket
    return {'raw': raw.split('[')[0], 'overall': overall, 'category': bucket, 'letters': letters}

def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows=[]
    with open(RAW) as f:
        for idx, line in enumerate(f, start=1):
            line=line.strip()
            if not line: continue
            parts=line.split(',')
            if len(parts) != 30:
                print(f"skip line {idx} cols {len(parts)}")
                continue
            attrs = parts[:29]
            diag_raw = parts[29]
            info = parse_diagnosis(diag_raw)
            row = {}
            row['Patient_ID'] = f"P{84000000+idx}" # generate deterministic ID from original record id if present
            # try extract original id inside []
            m = re.search(r'\[(\d+)\]', diag_raw)
            if m:
                row['Patient_ID'] = f"P{m.group(1)}"
            for k,v in zip(ATTRS, attrs):
                # clean ?
                if v == '?':
                    v = ''
                row[k]=v
            row['diagnosis_raw']=info['raw']
            row['diagnosis_letters']=''.join(info['letters'])
            row['Overall']=info['overall']
            row['Category']=info['category']
            # risk: for Negative, model will predict; here set baseline Lower
            row['Risk'] = 'Higher Risk' if row['Overall']=='Negative' and row['age'] and row['age'].isdigit() and int(row['age'])>60 and row['TSH'] not in ('', '?') else 'Lower Risk'
            rows.append(row)

    # Write processed
    fieldnames = ['Patient_ID']+ATTRS+['diagnosis_raw','diagnosis_letters','Overall','Category','Risk']
    with open(OUT_CSV,'w',newline='') as out:
        w=csv.DictWriter(out, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_CSV}")
    # also write sample for upload (500 rows balanced)
    # Stratify: take all Positive + equal Negative sample
    pos = [r for r in rows if r['Overall']=='Positive']
    neg = [r for r in rows if r['Overall']=='Negative']
    import random
    random.seed(42)
    random.shuffle(neg)
    # pick 250 pos + 250 neg if enough
    # Actually pos ~908, neg ~6771
    sample = pos[:300] + neg[:500]
    random.shuffle(sample)
    # also ensure covers hypo/hyper
    c=collections.Counter(r['Category'] for r in sample)
    print("Sample category dist", c)
    c2=collections.Counter(r['Overall'] for r in sample)
    print("Sample overall", c2)
    with open(OUT_SAMPLE,'w',newline='') as out:
        w=csv.DictWriter(out, fieldnames=fieldnames)
        w.writeheader()
        # for upload demo, drop internal cols diagnosis_letters? keep but also provide clean labs
        w.writerows(sample)
    print(f"Wrote sample {len(sample)} to {OUT_SAMPLE}")
    # label map
    cats = sorted(set(r['Category'] for r in rows))
    with open(OUT_LABEL_MAP,'w') as f:
        json.dump({"categories": cats, "overall": ["Positive","Negative"], "total": len(rows), "positive": len(pos), "negative": len(neg), "by_category": dict(collections.Counter(r['Category'] for r in pos))}, f, indent=2)
    print(f"Categories: {cats}")

if __name__ == '__main__':
    main()
