import os, glob, re, sys
import json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# A helper to extract more meaningful sentences rather than just metadata
def extract_meaningful(lines, entity_name):
    facts = []
    metrics = []
    
    # Exclude list of entities or raw metadata
    skip_keywords = ['raw/docx', '## ', 'title:', 'source:', 'entities:', 'tags:', '实体:']
    
    in_table = False
    
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
            
        # Check if table
        if line_s.startswith('|'):
            if entity_name in line_s:
                # Basic cleanup of table line
                cells = [c.strip() for c in line_s.split('|') if c.strip()]
                if cells:
                    metrics.append(" | ".join(cells))
            continue
            
        # Check if it contains the entity
        if entity_name in line_s:
            # Skip metadata
            if any(k in line_s for k in skip_keywords):
                continue
            
            # Remove leading bullet points
            clean_line = line_s.lstrip('-* \t').strip()
            if not clean_line:
                continue
                
            # Classify as metric or fact
            metric_keywords = ['%', '元', '例', '次', '天', '系数', '倍率', 'CMI', '床位', '费用', '增长', '下降', '万']
            if any(k in clean_line for k in metric_keywords) and any(c.isdigit() for c in clean_line):
                if clean_line not in metrics:
                    metrics.append(clean_line)
            else:
                if clean_line not in facts and len(clean_line) > 10:
                    facts.append(clean_line)
                    
    return facts, metrics

def process():
    entity_files = glob.glob('wiki/实体/*.md')
    link_counts = []

    for ef in entity_files:
        with open(ef, 'r', encoding='utf-8') as f:
            content = f.read()
        links = re.findall(r'\[\[来源/(.*?)\]\]', content)
        if links:
            link_counts.append((ef, len(links), links))

    link_counts.sort(key=lambda x: x[1], reverse=True)
    top_10 = link_counts[:10]
    
    print("Refining extraction for the following entities:")
    
    for ef, count, links in top_10:
        entity_name = os.path.basename(ef).replace('.md', '')
        print(f"\nProcessing {entity_name}...")
        
        all_lines = []
        for link in links:
            source_file = f"wiki/来源/{link}.md"
            if os.path.exists(source_file):
                with open(source_file, 'r', encoding='utf-8') as sf:
                    all_lines.extend(sf.read().split('\n'))
                    
        facts, metrics = extract_meaningful(all_lines, entity_name)
        
        # Deduplicate and limit
        facts = list(dict.fromkeys(facts))[:8]
        metrics = list(dict.fromkeys(metrics))[:8]
        
        # Format
        formatted_facts = [f"- {f}" for f in facts]
        formatted_metrics = [f"- {m}" for m in metrics]
        
        if not formatted_facts:
            formatted_facts = ["- 暂无从来源提取到具体的简介描述。"]
        if not formatted_metrics:
            formatted_metrics = ["- 暂无从来源提取到具体的指标数据。"]
            
        # Read current content
        with open(ef, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace 部门简介
        new_desc = "## 部门简介\n" + "\n".join(formatted_facts) + "\n"
        content = re.sub(r'## 部门简介\n.*?(?=\n## )', new_desc, content, flags=re.DOTALL)
        
        # Replace 核心指标
        new_metrics = "## 核心指标\n" + "\n".join(formatted_metrics) + "\n"
        content = re.sub(r'## 核心指标\n.*?(?=\n## )', new_metrics, content, flags=re.DOTALL)
        
        # Write back
        with open(ef, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Updated {entity_name}.md with {len(formatted_facts)} facts and {len(formatted_metrics)} metrics.")

if __name__ == '__main__':
    process()
