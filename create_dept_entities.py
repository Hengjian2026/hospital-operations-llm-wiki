import glob
import re
import os
import datetime

# Find all markdown files in wiki/来源/
files = glob.glob('wiki/来源/*.md')

departments = {}

# Regular expression to catch common Chinese department names ending in 科, 室, 部, 中心
dept_suffix = ('科', '部', '室', '中心')

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            basename = os.path.basename(f).replace('.md', '')
            
            # Extract [[科室名]] from content
            links = re.findall(r'\[\[(.*?)\]\]', content)
            for link in links:
                if link.startswith('实体/'):
                    link = link.split('实体/', 1)[1]
                
                # Check if it looks like a department name
                if link.endswith(dept_suffix) and 2 <= len(link) <= 8 and '科室' not in link and '事件' not in link and '分析' not in link and '指标' not in link and '数据' not in link and '中心' not in link and '部分' not in link:
                    if link not in departments:
                        departments[link] = set()
                    departments[link].add(basename)
                    
            # Also extract from title if possible
            title_deps = re.findall(r'([\u4e00-\u9fa5]+科)', basename)
            for dep in title_deps:
                if 2 <= len(dep) <= 8 and '科室' not in dep and '事件' not in dep and '分析' not in dep and '指标' not in dep and '数据' not in dep:
                    if dep not in departments:
                        departments[dep] = set()
                    departments[dep].add(basename)
                    
    except Exception as e:
        print(f'Error reading {f}: {e}')

# Ensure the entity directory exists
os.makedirs('wiki/实体', exist_ok=True)

created_departments = []

# Generate markdown files for each department
for dep, source_files in departments.items():
    file_path = f'wiki/实体/{dep}.md'
    
    # Don't overwrite existing ones, or maybe we want to append? 
    # The prompt just says "establish entity pages". If it doesn't exist, we create it.
    if not os.path.exists(file_path):
        created_departments.append(dep)
        
        with open(file_path, 'w', encoding='utf-8') as out:
            out.write(f'# {dep}\n\n')
            out.write('## 部门简介\n')
            out.write('（待补充）\n\n')
            out.write('## 核心指标\n')
            out.write('（待补充，可参考来源文档）\n\n')
            out.write('## 包含的来源\n')
            
            for source in sorted(list(source_files)):
                out.write(f'- [[来源/{source}]]\n')
                
            out.write('\n## 关联概念/方法论\n')
            out.write('- [[概念/描述性统计]]\n')
            out.write('- [[方法论/DRG分析]]\n')
            out.write('（待补充）\n')

# Log to log.md
if created_departments:
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    with open('log.md', 'a', encoding='utf-8') as log_file:
        log_file.write(f'\n## [{today}] create_entities | 建立科室实体页\n')
        log_file.write(f'批量创建了 {len(created_departments)} 个科室实体页面：{", ".join(created_departments)}\n')
    
    # Print the result to stdout so the Bash tool captures it
    print(f"Created {len(created_departments)} department entity pages: {', '.join(created_departments)}")
else:
    print("No new department entities needed to be created.")
