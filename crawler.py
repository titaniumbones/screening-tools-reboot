import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import argparse
import logging
import json
import re
from urllib.robotparser import RobotFileParser
from tqdm import tqdm

class WebCrawler:
    def __init__(self, start_url, output_dir='crawled_pages', delay=1, respect_robots=True, extract_menu=False):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.urls_to_visit = [start_url]
        self.page_content = {}
        self.delay = delay
        self.respect_robots = respect_robots
        self.output_dir = output_dir
        self.extract_menu = extract_menu
        self.menu_items = []
        self.visited_base_urls = set()  # Track base URLs without fragments
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WebCrawler')
        
        # Create a directory to save the pages
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up robots.txt parser
        if self.respect_robots:
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(f"https://{self.domain}/robots.txt")
            try:
                self.robots_parser.read()
                self.logger.info(f"Loaded robots.txt for {self.domain}")
            except Exception as e:
                self.logger.warning(f"Could not read robots.txt: {e}")
    
    def is_valid_url(self, url):
        """Check if the URL belongs to the target domain and is allowed by robots.txt."""
        parsed_url = urlparse(url)
        
        # Check if URL is in the same domain
        if not (parsed_url.netloc == self.domain or not parsed_url.netloc):
            return False
        
        # Skip URLs with fragments that are just page markers
        if parsed_url.fragment == 'page' and url.split('#')[0] in self.visited_urls:
            return False
            
        # Check robots.txt if enabled
        if self.respect_robots:
            return self.robots_parser.can_fetch("*", url)
            
        return True
    
    def get_links(self, url, html):
        """Extract all links from the HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Only follow links within the same domain
            if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                self.urls_to_visit.append(absolute_url)
        
        # Extract menu items if this is the homepage and extraction is enabled
        if self.extract_menu and url == self.start_url:
            self.extract_menu_items(soup, url)
    
    def extract_menu_items(self, soup, base_url):
        """Extract menu items from the homepage."""
        self.logger.info("Extracting menu items from homepage")
        
        # First try to find main navigation links
        # Look for links in the header or navigation section
        header = soup.find('header')
        if header:
            links = header.find_all('a')
            if len(links) >= 3:  # Assume it's a menu if it has at least 3 links
                for i, link in enumerate(links):
                    if link.get('href') and not link['href'].startswith('#'):
                        menu_item = {
                            'name': link.get_text().strip(),
                            'url': urljoin(base_url, link['href']),
                            'weight': i + 1
                        }
                        if menu_item['name'] and not any(item['url'] == menu_item['url'] for item in self.menu_items):
                            self.menu_items.append(menu_item)
                
                if len(self.menu_items) >= 3:
                    self.save_menu_items()
                    self.logger.info(f"Found {len(self.menu_items)} menu items in header")
                    return
        
        # Common menu container selectors
        menu_selectors = [
            'nav', '.nav', '.menu', '.main-menu', '#menu', '#main-menu',
            'header ul', '.navigation', '.navbar', '.header-menu'
        ]
        
        # Try to find menu containers
        for selector in menu_selectors:
            menu_containers = soup.select(selector)
            for container in menu_containers:
                links = container.find_all('a')
                if len(links) >= 3:  # Assume it's a menu if it has at least 3 links
                    for i, link in enumerate(links):
                        if link.get('href') and not link['href'].startswith('#'):
                            menu_item = {
                                'name': link.get_text().strip(),
                                'url': urljoin(base_url, link['href']),
                                'weight': i + 1
                            }
                            if menu_item['name'] and not any(item['url'] == menu_item['url'] for item in self.menu_items):
                                self.menu_items.append(menu_item)
                    
                    # If we found menu items, save them and stop looking
                    if len(self.menu_items) >= 3:
                        self.save_menu_items()
                        self.logger.info(f"Found {len(self.menu_items)} menu items")
                        return
        
        # Fallback: Look for update links in the content (specific to screening-tools.com)
        update_links = []
        update_section = soup.find(string=lambda text: text and "Updates" in text)
        if update_section:
            # Find the parent element and look for links in the following list
            parent = update_section.parent
            if parent:
                # Look for list items with links after the "Updates" heading
                list_items = parent.find_all_next('li')
                for i, li in enumerate(list_items):
                    link = li.find('a')
                    if link and link.get('href'):
                        # Extract the tool name from the text
                        text = link.get_text().strip()
                        # Try to extract a cleaner name from the text
                        name = text
                        if "Access to" in text:
                            name = text.split("Access to")[1].strip()
                        elif "[" in text and "]" in text:
                            # Extract text between brackets if present
                            match = re.search(r'\[(.*?)\]', text)
                            if match:
                                name = match.group(1).strip()
                        
                        # Clean up the name
                        name = re.sub(r'\'s\s+', ' ', name)  # Remove possessives
                        name = re.sub(r'[^\w\s\-]', '', name)  # Remove special chars except hyphens
                        name = name.strip()
                        
                        menu_item = {
                            'name': name,
                            'url': urljoin(base_url, link['href']),
                            'weight': i + 1
                        }
                        if menu_item['name'] and not any(item['url'] == menu_item['url'] for item in self.menu_items):
                            update_links.append(menu_item)
                
                if update_links:
                    # Add "Home" as the first item
                    self.menu_items.append({
                        'name': 'Home',
                        'url': base_url,
                        'weight': 1
                    })
                    
                    # Add all the update links
                    for item in update_links:
                        item['weight'] += 1  # Adjust weight to account for Home
                        self.menu_items.append(item)
                    
                    # Add additional common pages if they exist
                    common_pages = [
                        {'path': '/about', 'name': 'About'},
                        {'path': '/contact', 'name': 'Contact'},
                        {'path': '/get-involved', 'name': 'Get Involved'},
                        {'path': '/donate', 'name': 'Donate'}
                    ]
                    
                    for i, page in enumerate(common_pages):
                        test_url = urljoin(base_url, page['path'])
                        try:
                            # Make a HEAD request to check if the page exists
                            response = requests.head(test_url, timeout=5)
                            if response.status_code == 200:
                                self.menu_items.append({
                                    'name': page['name'],
                                    'url': test_url,
                                    'weight': len(self.menu_items) + 1
                                })
                        except:
                            # Skip if request fails
                            pass
                    
                    self.save_menu_items()
                    self.logger.info(f"Found {len(self.menu_items)} menu items from updates section")
                    return
        
        self.logger.warning("No menu items found on the homepage")
    
    def save_menu_items(self):
        """Save extracted menu items to a JSON file."""
        try:
            with open(f'{self.output_dir}/menu_items.json', 'w', encoding='utf-8') as f:
                json.dump(self.menu_items, f, indent=2)
            
            # Also generate a Hugo-compatible menu config
            self.generate_hugo_menu_config()
            
            self.logger.info(f"Saved menu items to {self.output_dir}/menu_items.json")
        except Exception as e:
            self.logger.error(f"Failed to save menu items: {e}")
    
    def generate_hugo_menu_config(self):
        """Generate Hugo-compatible menu configuration."""
        try:
            hugo_config = "# Main menu\n[menu]\n"
            
            for item in self.menu_items:
                # Convert absolute URLs to relative for Hugo
                url = item['url']
                parsed_url = urlparse(url)
                relative_url = parsed_url.path
                if not relative_url:
                    relative_url = "/"
                
                # Clean up the name for better display
                name = item['name']
                # Remove any trailing punctuation
                name = re.sub(r'[^\w\s]+$', '', name)
                # Replace multiple spaces with a single space
                name = re.sub(r'\s+', ' ', name)
                # Capitalize first letter of each word for consistency
                name = ' '.join(word.capitalize() for word in name.split())
                
                hugo_config += f"  [[menu.main]]\n"
                hugo_config += f"    name = \"{name}\"\n"
                hugo_config += f"    url = \"{relative_url}\"\n"
                hugo_config += f"    weight = {item['weight']}\n"
            
            with open(f'{self.output_dir}/hugo_menu_config.toml', 'w', encoding='utf-8') as f:
                f.write(hugo_config)
            
            # Also generate a Jekyll-compatible menu config
            self.generate_jekyll_menu_config()
                
            self.logger.info(f"Generated Hugo menu config at {self.output_dir}/hugo_menu_config.toml")
        except Exception as e:
            self.logger.error(f"Failed to generate Hugo menu config: {e}")
    
    def generate_jekyll_menu_config(self):
        """Generate Jekyll-compatible menu configuration."""
        try:
            jekyll_config = "# Jekyll navigation\nnav_items:\n"
            
            for item in self.menu_items:
                # Convert absolute URLs to relative for Jekyll
                url = item['url']
                parsed_url = urlparse(url)
                relative_url = parsed_url.path
                if not relative_url:
                    relative_url = "/"
                
                # Clean up the name
                name = item['name']
                name = re.sub(r'[^\w\s]+$', '', name)
                name = re.sub(r'\s+', ' ', name)
                name = ' '.join(word.capitalize() for word in name.split())
                
                jekyll_config += f"  - name: \"{name}\"\n"
                jekyll_config += f"    url: \"{relative_url}\"\n"
                jekyll_config += f"    weight: {item['weight']}\n"
            
            with open(f'{self.output_dir}/jekyll_menu_config.yml', 'w', encoding='utf-8') as f:
                f.write(jekyll_config)
                
            self.logger.info(f"Generated Jekyll menu config at {self.output_dir}/jekyll_menu_config.yml")
        except Exception as e:
            self.logger.error(f"Failed to generate Jekyll menu config: {e}")
    
    def save_page(self, url, html):
        """Save the page content to a file."""
        parsed_url = urlparse(url)
        path = parsed_url.path
        fragment = parsed_url.fragment
        
        # Skip saving if this is just a fragment variation of an already saved URL
        if fragment and fragment == 'page' and url.split('#')[0] in self.visited_urls:
            self.logger.debug(f"Skipping duplicate with fragment: {url}")
            return
        
        # Handle the root URL
        if path == '':
            filename = 'index.html'
        else:
            # Remove leading slash and replace remaining slashes with underscores
            filename = path.lstrip('/').replace('/', '_')
            if filename == '':
                filename = 'index.html'
            if not filename.endswith('.html'):
                filename += '.html'
        
        try:
            with open(f'{self.output_dir}/{filename}', 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.info(f"Saved: {url} as {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save {url}: {e}")
    
    def crawl(self, max_pages=None):
        """Start crawling from the initial URL."""
        visited_count = 0
        
        # Create progress bar
        pbar = tqdm(total=max_pages if max_pages else float('inf'), 
                    desc="Crawling", unit="page")
        
        while self.urls_to_visit and (max_pages is None or visited_count < max_pages):
            url = self.urls_to_visit.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Skip fragment variations of already visited URLs
            base_url = url.split('#')[0]
            if '#' in url and base_url in self.visited_base_urls:
                continue
                
            self.logger.info(f"Crawling: {url}")
            self.visited_urls.add(url)
            self.visited_base_urls.add(base_url)
            visited_count += 1
            pbar.update(1)
            
            try:
                headers = {
                    'User-Agent': 'PythonWebCrawler/1.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                # Only process HTML content
                if 'text/html' in response.headers.get('Content-Type', ''):
                    html = response.text
                    self.page_content[url] = html
                    self.save_page(url, html)
                    self.get_links(url, html)
                
                # Be nice to the server
                time.sleep(self.delay)
                
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP Error for {url}: {e}")
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"Connection Error for {url}: {e}")
            except requests.exceptions.Timeout as e:
                self.logger.error(f"Timeout Error for {url}: {e}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request Error for {url}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error crawling {url}: {e}")
        
        pbar.close()
        self.logger.info(f"Crawling complete. Visited {len(self.visited_urls)} pages.")
        
        # Final report on menu items if extraction was enabled
        if self.extract_menu and self.menu_items:
            self.logger.info(f"Extracted {len(self.menu_items)} menu items")
        
        return self.page_content

def parse_arguments():
    parser = argparse.ArgumentParser(description='Web Crawler')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('--output', '-o', default='crawled_pages', 
                        help='Directory to save crawled pages')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                        help='Delay between requests in seconds')
    parser.add_argument('--max-pages', '-m', type=int, default=None,
                        help='Maximum number of pages to crawl')
    parser.add_argument('--ignore-robots', action='store_true',
                        help='Ignore robots.txt restrictions')
    parser.add_argument('--extract-menu', action='store_true',
                        help='Extract menu items from the homepage')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    crawler = WebCrawler(
        args.url,
        output_dir=args.output,
        delay=args.delay,
        respect_robots=not args.ignore_robots,
        extract_menu=args.extract_menu
    )
    crawler.crawl(max_pages=args.max_pages)
