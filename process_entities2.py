import os, glob, re, sys

sys.stdout.reconfigure(encoding='utf-8')

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
    
    print("Will process the following entities:")
    for ef, count, links in top_10:
        print(f"  {os.path.basename(ef)} ({count} links)")
        
    for ef, count, links in top_10:
        entity_name = os.path.basename(ef).replace('.md', '')
        print(f"\nProcessing {entity_name}...")
        
        sources_content = ""
        for link in links:
            source_file = f"wiki/来源/{link}.md"
            if os.path.exists(source_file):
                with open(source_file, 'r', encoding='utf-8') as sf:
                    content = sf.read()
                    sources_content += f"\n\n--- Source: {link} ---\n"
                    sources_content += content
            else:
                print(f"Warning: source file not found {source_file}")
                
        # Simple extraction based on entity name
        lines = sources_content.split('\n')
        extracted_facts = []
        metrics = []
        
        for i, line in enumerate(lines):
            # Look for lines mentioning the entity
            if entity_name in line and len(line.strip()) > 5:
                # If it looks like a metric or data point
                if any(x in line for x in ['%', '元', '例', '次', '天', '系数', '倍率', 'CMI', '床位', '费用']):
                    metrics.append(line.strip())
                else:
                    extracted_facts.append(line.strip())
                    
        # Also look for data tables in markdown
        in_table = False
        table_header = []
        for line in lines:
            if line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_header = [x.strip() for x in line.split('|') if x.strip()]
                elif '---' not in line:
                    cells = [x.strip() for x in line.split('|') if x.strip()]
                    if any(entity_name in cell for cell in cells):
                        metrics.append(line.strip())
            else:
                in_table = False
                
        # Deduplicate and clean
        metrics = list(set([m for m in metrics if not m.startswith('---') and not m.startswith('##')]))
        extracted_facts = list(set([f for f in extracted_facts if not f.startswith('---') and not f.startswith('##')]))
        
        # Sort metrics: keep table rows separate or format them
        formatted_metrics = []
        for m in metrics:
            if m.startswith('|'):
                formatted_metrics.append(m)
            else:
                formatted_metrics.append(f"- {m.replace('- ', '')}")
                
        formatted_facts = []
        for f in extracted_facts:
            formatted_facts.append(f"- {f.replace('- ', '')}")
            
        # Limit to reasonable amount
        formatted_metrics = formatted_metrics[:15]
        formatted_facts = formatted_facts[:10]
        
        if not formatted_metrics:
            formatted_metrics = ["- 暂无从来源提取到具体指标数据。"]
        if not formatted_facts:
            formatted_facts = ["- 暂无从来源提取到具体简介描述。"]
            
        # Write back to entity file
        with open(ef, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Replace 部门简介
        # We need a robust regex replacement for the sections
        new_desc = "## 部门简介\n" + "\n".join(formatted_facts) + "\n"
        # Find everything between ## 部门简介 and the next ## 
        original_content = re.sub(r'## 部门简介\n.*?(?=\n## )', new_desc, original_content, flags=re.DOTALL)
        # If it didn't match (because it's at the end or no newlines), we can fallback
        if new_desc not in original_content and '## 部门简介' in original_content:
            original_content = re.sub(r'## 部门简介.*?(?=\n## |$)', new_desc, original_content, flags=re.DOTALL)
            
        # Replace 核心指标
        new_metrics = "## 核心指标\n" + "\n".join(formatted_metrics) + "\n"
        original_content = re.sub(r'## 核心指标\n.*?(?=\n## )', new_metrics, original_content, flags=re.DOTALL)
        if new_metrics not in original_content and '## 核心指标' in original_content:
            original_content = re.sub(r'## 核心指标.*?(?=\n## |$)', new_metrics, original_content, flags=re.DOTALL)
            
        with open(ef, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        print(f"Updated {entity_name}.md with {len(formatted_facts)} facts and {len(formatted_metrics)} metrics.")

if __name__ == '__main__':
    process()
