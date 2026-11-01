import json
import sqlite3
from pathlib import Path

eval_path = Path('evaluation/evaluation_dataset.json')
with open(eval_path, 'r', encoding='utf-8') as f:
    eval_ds = json.load(f)
ref_map = {item['id']: item for item in eval_ds['questions']}

results_path = Path('submission/colab_evidence/schemasense_colab_model_results.json')
with open(results_path, 'r', encoding='utf-8') as f:
    results = json.load(f)

db_path = Path('data/databases/campus_intelligence.db')
conn = sqlite3.connect(f'file:{db_path.resolve()}?mode=ro', uri=True)
cursor = conn.cursor()

for r in results:
    qid = r['question_id']
    q = r['question']
    gsql = r.get('generated_sql')
    ref_item = ref_map.get(qid, {})
    rsql = ref_item.get('reference_sql')
    sv = r.get('syntax_valid')
    sc = r.get('schema_valid')
    ex = r.get('execution_status')
    em = r.get('exact_match')
    cat = r.get('category')
    intent = ref_item.get('intent', 'N/A')
    
    g_rows, g_cols, g_err = None, None, None
    r_rows, r_cols, r_err = None, None, None
    if gsql:
        try:
            cursor.execute(gsql)
            g_cols = [d[0] for d in cursor.description] if cursor.description else []
            g_rows = cursor.fetchall()
        except Exception as e:
            g_err = str(e)
            
    if rsql:
        try:
            cursor.execute(rsql)
            r_cols = [d[0] for d in cursor.description] if cursor.description else []
            r_rows = cursor.fetchall()
        except Exception as e:
            r_err = str(e)

    print('='*80)
    print(f'[{qid}] {cat} | Exact Match: {em} | Exec: {ex}')
    print(f'Intent: {intent}')
    print(f'Question: {q}')
    print(f'Generated SQL: {gsql}')
    print(f'Reference SQL: {rsql}')
    if g_err:
        print(f'Generated Error: {g_err}')
    else:
        print(f'Gen Cols: {g_cols} | Row count: {len(g_rows) if g_rows is not None else 0}')
        if g_rows and len(g_rows) <= 5:
            print(f'Gen sample rows: {g_rows}')
    if r_err:
        print(f'Ref Error: {r_err}')
    else:
        print(f'Ref Cols: {r_cols} | Row count: {len(r_rows) if r_rows is not None else 0}')
        if r_rows and len(r_rows) <= 5:
            print(f'Ref sample rows: {r_rows}')
