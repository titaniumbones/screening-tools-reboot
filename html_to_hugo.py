import os
import re
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import datetime

def create_hugo_site():
    """Create the basic Hugo site structure."""
    hugo_dir = 'hugo_site'
    
    # Create main directories
    if os.path.exists(hugo_dir):
        shutil.rmtree(hugo_dir)
    
    os.makedirs(hugo_dir)
    os.makedirs(os.path.join(hugo_dir, 'content'))
    os.makedirs(os.path.join(hugo_dir, 'static'))
    os.makedirs(os.path.join(hugo_dir, 'layouts'))
    os.makedirs(os.path.join(hugo_dir, 'layouts', '_default'))
    os.makedirs(os.path.join(hugo_dir, 'layouts', 'partials'))
    os.makedirs(os.path.join(hugo_dir, 'assets', 'scss'))
    
    # Create config.toml
    with open(os.path.join(hugo_dir, 'config.toml'), 'w') as f:
        f.write('''baseURL = "/"
languageCode = "en-us"
title = "Screening Tools"
disableKinds = ["taxonomy", "taxonomyTerm"]

[params]
  description = "Public Environmental Data Partners"

[markup.goldmark.renderer]
  unsafe = true
''')
    
    # Create default layout
    with open(os.path.join(hugo_dir, 'layouts', '_default', 'baseof.html'), 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ if .Title }}{{ .Title }} - {{ end }}{{ .Site.Title }}</title>
    {{ $style := resources.Get "scss/main.scss" | resources.ToCSS | resources.Minify | resources.Fingerprint }}
    <link rel="stylesheet" href="{{ $style.Permalink }}">
</head>
<body>
    <header>
        <div class="container">
            <h1><a href="/">{{ .Site.Title }}</a></h1>
        </div>
    </header>
    <main>
        <div class="container">
            {{ block "main" . }}{{ end }}
        </div>
    </main>
    <footer>
        <div class="container">
            <p>&copy; {{ now.Format "2006" }} Public Environmental Data Partners</p>
        </div>
    </footer>
</body>
</html>''')
    
    # Create single.html template
    with open(os.path.join(hugo_dir, 'layouts', '_default', 'single.html'), 'w') as f:
        f.write('''{{ define "main" }}
<article>
    <h1>{{ .Title }}</h1>
    {{ .Content }}
</article>
{{ end }}''')
    
    # Create list.html template
    with open(os.path.join(hugo_dir, 'layouts', '_default', 'list.html'), 'w') as f:
        f.write('''{{ define "main" }}
<h1>{{ .Title }}</h1>
{{ .Content }}
<ul class="page-list">
    {{ range .Pages }}
    <li>
        <a href="{{ .Permalink }}">{{ .Title }}</a>
    </li>
    {{ end }}
</ul>
{{ end }}''')
    
    # Create home.html template
    with open(os.path.join(hugo_dir, 'layouts', '_default', 'home.html'), 'w') as f:
        f.write('''{{ define "main" }}
<div class="home-content">
    {{ .Content }}
</div>
{{ end }}''')
    
    # Create SCSS file
    with open(os.path.join(hugo_dir, 'assets', 'scss', 'main.scss'), 'w') as f:
        f.write('''// Variables
$primary-color: #0066cc;
$secondary-color: #333;
$background-color: #fff;
$header-bg: #f4f4f4;
$footer-bg: #f4f4f4;
$font-family: Arial, sans-serif;
$container-width: 800px;

// Base styles
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: $font-family;
  line-height: 1.6;
  color: $secondary-color;
  background-color: $background-color;
}

.container {
  max-width: $container-width;
  margin: 0 auto;
  padding: 0 20px;
}

// Typography
h1, h2, h3, h4, h5, h6 {
  margin: 1.5rem 0 1rem;
  line-height: 1.2;
}

h1 {
  font-size: 2rem;
}

h2 {
  font-size: 1.75rem;
}

h3 {
  font-size: 1.5rem;
}

h4 {
  font-size: 1.25rem;
}

p, ul, ol {
  margin-bottom: 1rem;
}

a {
  color: $primary-color;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

// Layout
header {
  background-color: $header-bg;
  padding: 1.5rem 0;
  margin-bottom: 2rem;
  
  h1 {
    margin: 0;
    
    a {
      color: $secondary-color;
      text-decoration: none;
    }
  }
}

main {
  min-height: 70vh;
  padding: 1rem 0 3rem;
}

footer {
  background-color: $footer-bg;
  padding: 1.5rem 0;
  text-align: center;
  margin-top: 2rem;
}

// Components
.page-list {
  list-style: none;
  
  li {
    margin-bottom: 0.5rem;
  }
}

article {
  h1 {
    margin-bottom: 1.5rem;
  }
}

// Home page specific
.home-content {
  h4 {
    font-weight: bold;
    margin-top: 2rem;
  }
  
  ul {
    list-style-position: inside;
    margin-left: 1rem;
  }
  
  strong {
    font-weight: bold;
  }
}

// Responsive
@media (max-width: 768px) {
  h1 {
    font-size: 1.75rem;
  }
  
  .container {
    padding: 0 15px;
  }
}
''')

def extract_title(soup):
    """Extract title from HTML."""
    # Try to get title from title tag
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    
    # Try to get from h1
    h1_tag = soup.find('h1')
    if h1_tag and h1_tag.string:
        return h1_tag.string.strip()
    
    # Try to get from h2
    h2_tag = soup.find('h2')
    if h2_tag and h2_tag.string:
        return h2_tag.string.strip()
    
    # Default title
    return "Screening Tools Page"

def clean_html_content(soup):
    """Clean up HTML content for conversion."""
    # Remove script and style elements
    for element in soup.find_all(['script', 'style']):
        element.decompose()
    
    # Find the main content
    main_content = soup.find('main') or soup.find('body')
    
    if main_content:
        return main_content
    return soup

def html_to_markdown(html_content, url_path):
    """Convert HTML to Hugo markdown with front matter."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title = extract_title(soup)
    
    # Clean content
    main_content = clean_html_content(soup)
    
    # Create front matter
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    front_matter = f"""---
title: "{title}"
date: {date}
draft: false
url: "{url_path}"
---

"""
    
    # Convert to string and preserve HTML
    content = str(main_content)
    
    return front_matter + content

def process_html_files():
    """Process all HTML files in crawled_pages directory."""
    create_hugo_site()
    
    if not os.path.exists('crawled_pages'):
        print("Error: crawled_pages directory not found!")
        return
    
    for filename in os.listdir('crawled_pages'):
        if not filename.endswith('.html'):
            continue
        
        # Read HTML file
        with open(os.path.join('crawled_pages', filename), 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Determine URL path
        if filename == 'index.html':
            url_path = "/"
            output_path = os.path.join('hugo_site', 'content', '_index.md')
        else:
            # Remove .html extension
            page_name = filename.replace('.html', '')
            
            # Handle underscore-separated paths
            if '_' in page_name:
                # Convert underscores back to slashes for URL
                url_parts = page_name.split('_')
                url_path = '/' + '/'.join(url_parts) + '/'
                
                # Create directory structure
                dir_path = os.path.join('hugo_site', 'content')
                for part in url_parts[:-1]:
                    dir_path = os.path.join(dir_path, part)
                    os.makedirs(dir_path, exist_ok=True)
                
                # Create _index.md in each directory
                for i in range(len(url_parts)-1):
                    section_path = '/'.join(url_parts[:i+1])
                    index_path = os.path.join('hugo_site', 'content', *url_parts[:i+1], '_index.md')
                    if not os.path.exists(index_path):
                        with open(index_path, 'w', encoding='utf-8') as f:
                            f.write(f"""---
title: "{url_parts[i].replace('-', ' ').title()}"
date: {datetime.datetime.now().strftime("%Y-%m-%d")}
draft: false
url: "/{section_path}/"
---
""")
                
                output_path = os.path.join(dir_path, url_parts[-1] + '.md')
            else:
                url_path = '/' + page_name + '/'
                os.makedirs(os.path.join('hugo_site', 'content', page_name), exist_ok=True)
                output_path = os.path.join('hugo_site', 'content', page_name, 'index.md')
        
        # Convert to markdown
        markdown_content = html_to_markdown(html_content, url_path)
        
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Converted {filename} to {output_path}")

if __name__ == "__main__":
    process_html_files()
    print("Hugo site created in the 'hugo_site' directory")
    print("To preview the site, navigate to the hugo_site directory and run:")
    print("  hugo server -D")
