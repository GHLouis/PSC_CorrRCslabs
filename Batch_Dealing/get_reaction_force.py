import os
import csv

def get_reaction_force():
    csv_path = os.path.join(os.getcwd(), "temp_8points_sum.csv")

    exportResults(csv_path, {
        'analysis': 'Analysis1',           
        'result': 'Reaction Forces',
        'components': ['FBZ'],
        'block': outputBlocks('Analysis1')[0]
    })

    step_data = {} 
    header_found = False
    n_idx = s_idx = f_idx = -1
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        for row in csv.reader(f):
            if not row: continue
            
            if not header_found:
                clean_row = [str(item).strip().lower() for item in row]
                if 'node' in clean_row:
                    n_idx = clean_row.index('node')
                    s_idx = clean_row.index('case-id') if 'case-id' in clean_row else clean_row.index('step')
                    f_idx = next(i for i, col in enumerate(clean_row) if 'fbz' in col)
                    header_found = True
                continue
            
            try:
                fbz_val = float(row[f_idx])
                if fbz_val < -100.0:
                    step_data.setdefault(row[s_idx].strip(), {})[row[n_idx].strip()] = fbz_val
            except ValueError:
                pass 
    
    step_sums = {step: sum(nodes.values()) for step, nodes in step_data.items()}
    max_step = max(step_sums, key=lambda k: abs(step_sums[k]))
    max_force = round(step_sums[max_step], 2)
    
    return max_force
