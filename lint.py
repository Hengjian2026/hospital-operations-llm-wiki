import os
import re
import sys

def scan_markdown_files(directory):
    """Scan all markdown files in a directory and its subdirectories."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def extract_links(content):
    """Extract all wikilinks [[Page Name]] from content."""
    # Match [[Page Name]] or [[Page Name|Display Text]] or [[folder/Page Name]]
    links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    return set(links)

def check_orphans():
    """Check for orphan pages in wiki directory."""
    print("Running Orphan Pages Check...")
    
    wiki_dir = 'wiki'
    if not os.path.exists(wiki_dir):
        print(f"Directory '{wiki_dir}' not found. Skipping orphan check.")
        return 0

    all_md_files = scan_markdown_files(wiki_dir)
    # Also check index.md for links to wiki pages
    if os.path.exists('index.md'):
        all_md_files.append('index.md')
    
    # Also check CLAUDE.md just in case
    if os.path.exists('CLAUDE.md'):
        all_md_files.append('CLAUDE.md')

    all_links = set()
    for file in all_md_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                links = extract_links(content)
                # Some links might include paths or extensions, let's normalize them
                normalized_links = set()
                for link in links:
                    # Remove path if present
                    # Use split since it might be forward or backward slash
                    basename = link.replace('\\\\', '/').split('/')[-1]
                    # Remove extension if present
                    if basename.endswith('.md'):
                        basename = basename[:-3]
                    normalized_links.add(basename.strip())
                all_links.update(normalized_links)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    # Now check which files in wiki/ are not linked
    wiki_files = scan_markdown_files(wiki_dir)
    orphans = []
    for file in wiki_files:
        basename = os.path.basename(file)
        page_name = basename[:-3] # Remove .md
        
        # Don't consider index pages as orphans typically
        if page_name.lower() in ['index', '-首页']:
            continue
            
        if page_name.strip() not in all_links:
            orphans.append(file)

    if orphans:
        print(f"Found {len(orphans)} orphan pages:")
        for orphan in orphans:
            try:
                print(f"  - {orphan}")
            except UnicodeEncodeError:
                print(f"  - {orphan.encode('utf-8').decode('cp1252', 'ignore')}")
        return len(orphans)
    else:
        print("No orphan pages found.")
        return 0

def check_entity_frontmatter():
    """Check if entity pages have standard YAML frontmatter."""
    print("\nRunning Entity Frontmatter Check...")
    
    entity_dir = os.path.join('wiki', '实体')
    if not os.path.exists(entity_dir):
        print(f"Directory '{entity_dir}' not found. Skipping entity check.")
        return 0

    entity_files = scan_markdown_files(entity_dir)
    missing_frontmatter = []

    for file in entity_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line != '---':
                    missing_frontmatter.append(file)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if missing_frontmatter:
        print(f"Found {len(missing_frontmatter)} entity pages missing standard YAML frontmatter (starting with '---'):")
        for file in missing_frontmatter:
            try:
                print(f"  - {file}")
            except UnicodeEncodeError:
                print(f"  - {file.encode('utf-8').decode('cp1252', 'ignore')}")
        return len(missing_frontmatter)
    else:
        print("All entity pages have valid YAML frontmatter.")
        return 0

def main():
    # Set console output encoding to utf-8 if possible
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    print("==================================================")
    print("Knowledge Base Linter")
    print("==================================================")
    
    # Check if we are in the root directory (should have CLAUDE.md)
    if not os.path.exists('CLAUDE.md'):
        print("Warning: CLAUDE.md not found. Are you running this from the repository root?")
    
    orphan_count = check_orphans()
    frontmatter_count = check_entity_frontmatter()
    
    print("\n==================================================")
    print("Lint Summary")
    print("==================================================")
    total_issues = orphan_count + frontmatter_count
    if total_issues > 0:
        print(f"Total issues found: {total_issues}")
        sys.exit(1)
    else:
        print("All checks passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
