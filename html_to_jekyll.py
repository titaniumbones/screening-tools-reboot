import os
import re
import shutil
from bs4 import BeautifulSoup
from datetime import datetime

def create_jekyll_site():
    # Create Jekyll site directory structure
    jekyll_dir = 'jekyll-site'
    if os.path.exists(jekyll_dir):
        shutil.rmtree(jekyll_dir)
    
    os.makedirs(jekyll_dir)
    os.makedirs(os.path.join(jekyll_dir, '_layouts'))
    os.makedirs(os.path.join(jekyll_dir, '_includes'))
    os.makedirs(os.path.join(jekyll_dir, 'assets', 'css'))
    os.makedirs(os.path.join(jekyll_dir, 'assets', 'js'))
    os.makedirs(os.path.join(jekyll_dir, 'assets', 'images'))
    
    # Create _config.yml
    with open(os.path.join(jekyll_dir, '_config.yml'), 'w') as f:
        f.write('''title: Screening Tools
description: Public Environmental Data Partners
baseurl: ""
url: ""
markdown: kramdown
plugins:
  - jekyll-feed
''')
    
    # Create default layout
    with open(os.path.join(jekyll_dir, '_layouts', 'default.html'), 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} - {{ site.title }}</title>
    <link rel="stylesheet" href="{{ "/assets/css/main.css" | relative_url }}">
</head>
<body>
    <header>
        <h1><a href="{{ "/" | relative_url }}">{{ site.title }}</a></h1>
    </header>
    <main>
        {{ content }}
    </main>
    <footer>
        <p>&copy; {{ site.time | date: '%Y' }} Public Environmental Data Partners</p>
    </footer>
</body>
</html>''')
    
    # Create main CSS file
    with open(os.path.join(jekyll_dir, 'assets', 'css', 'main.css'), 'w') as f:
        f.write('''body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
}

header, footer {
    background-color: #f4f4f4;
    padding: 1rem;
    text-align: center;
}

main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}
''')

def html_to_markdown(html_content):
    """Convert HTML content to markdown-like format with YAML front matter."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to extract title
    title = "Screening Tools"
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.text.strip()
    elif soup.find('h1'):
        title = soup.find('h1').text.strip()
    
    # Extract main content
    content = ""
    main_content = soup.find('body')
    if main_content:
        # Remove script and style elements
        for script in main_content.find_all(['script', 'style']):
            script.decompose()
        content = main_content.get_text(separator='\n\n')
        
        # Clean up the content
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
    
    # Create YAML front matter
    yaml_front_matter = f"""---
layout: default
title: "{title}"
---

"""
    
    return yaml_front_matter + content

def process_html_files():
    """Process all HTML files in the crawled_pages directory."""
    create_jekyll_site()
    
    if not os.path.exists('crawled_pages'):
        print("Error: crawled_pages directory not found!")
        return
    
    for filename in os.listdir('crawled_pages'):
        if filename.endswith('.html'):
            # Read HTML file
            with open(os.path.join('crawled_pages', filename), 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Convert to markdown
            markdown_content = html_to_markdown(html_content)
            
            # Determine output path
            if filename == 'index.html':
                output_path = os.path.join('jekyll-site', 'index.md')
            else:
                # Remove .html extension and create path
                page_name = filename.replace('.html', '')
                output_path = os.path.join('jekyll-site', f"{page_name}.md")
            
            # Write markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Converted {filename} to {output_path}")

if __name__ == "__main__":
    process_html_files()
    print("Jekyll site created in the 'jekyll-site' directory")
    print("To preview the site, navigate to the jekyll-site directory and run:")
    print("  bundle exec jekyll serve")
