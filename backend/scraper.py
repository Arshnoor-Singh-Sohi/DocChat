import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import List, Set, Optional, Callable
import re
from langchain.docstore.document import Document

class DocumentationScraper:
    """
    Intelligent documentation scraper that crawls documentation websites
    and extracts clean, relevant content while filtering out navigation,
    footers, and other non-documentation elements.
    """
    
    def __init__(self, base_url: str, max_pages: int = 50):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Progress callback
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def is_documentation_url(self, url: str) -> bool:
        """
        Filter to only include documentation URLs.
        Excludes login pages, downloads, community pages, etc.
        """
        parsed = urlparse(url)
        
        # Patterns to exclude
        exclude_patterns = [
            '/search', '/login', '/register', '/download', '/community',
            '/news', '/events', '/jobs', '/blog', '/forum', '/support',
            '.pdf', '.zip', '.tar.gz', '.exe', '.dmg',
            'javascript:', 'mailto:', '#',
            '/privacy', '/terms', '/cookies', '/legal'
        ]
        
        # Check if URL contains excluded patterns
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Include only URLs from the same domain
        base_domain = urlparse(self.base_url).netloc
        return parsed.netloc == base_domain
    
    def extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract main content from HTML, filtering out navigation,
        footers, sidebars, and other non-content elements.
        """
        
        # Clone soup to avoid modifying original
        soup = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove script and style elements first
        for element in soup(['script', 'style', 'link', 'meta']):
            element.decompose()
        
        # Remove common non-content elements
        non_content_tags = ['nav', 'header', 'footer', 'aside']
        for tag in non_content_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with navigation/footer classes and IDs
        unwanted_selectors = [
            # Navigation
            '.navigation', '.nav', '.navbar', '.menu', '.sidebar',
            '#navigation', '#nav', '#navbar', '#menu', '#sidebar',
            '[class*="nav-"]', '[id*="nav-"]',
            
            # Footer
            '.footer', '#footer', '[class*="footer"]', '[id*="footer"]',
            
            # Headers (but keep article headers)
            '.header:not(article .header)', '#header:not(article #header)',
            
            # Other common patterns
            '.breadcrumb', '.toc', '.table-of-contents',
            '.social-links', '.social', '.share',
            '.advertisement', '.ads', '.ad',
            '.comments', '.comment-section',
            '.related-posts', '.related-articles',
            '.newsletter', '.subscribe',
            '.copyright', '.legal'
        ]
        
        for selector in unwanted_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except:
                continue
        
        # Try to find main content area
        main_content = None
        
        # Common main content selectors for documentation sites
        content_selectors = [
            # Generic content areas
            'main', '.main', '#main', '.main-content', '#main-content',
            '.content', '#content', '.page-content', '#page-content',
            
            # Documentation-specific
            '.documentation', '.docs', '#documentation', '#docs',
            '.doc-content', '#doc-content', '.docs-content', '#docs-content',
            'article', '.article', '#article',
            
            # Framework-specific patterns
            '.rst-content',  # Sphinx/Read the Docs
            '.markdown-body',  # GitHub-style
            '.prose',  # Tailwind/modern docs
            '.md-content',  # Material-style docs
            '[role="main"]',  # Accessibility-aware sites
            
            # API documentation
            '.api-content', '.reference-content',
            
            # Tutorial/guide content
            '.tutorial-content', '.guide-content'
        ]
        
        # Try each selector
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text(strip=True)) > 100:
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Clean up the text
            text = main_content.get_text(separator=' ', strip=True)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common documentation artifacts
            text = re.sub(r'Previous\s+Next', '', text)
            text = re.sub(r'Table of Contents', '', text)
            text = re.sub(r'Edit on GitHub', '', text)
            text = re.sub(r'Copy to clipboard', '', text)
            
            return text.strip()
        
        return ""
    
    def extract_code_examples(self, soup: BeautifulSoup) -> List[str]:
        """Extract code examples from the page"""
        code_examples = []
        
        # Common code block selectors
        code_selectors = [
            'pre code', 'pre', '.highlight pre',
            '.codehilite', '.code-block',
            '[class*="language-"]', '[class*="highlight-"]'
        ]
        
        for selector in code_selectors:
            for code_element in soup.select(selector):
                code_text = code_element.get_text(strip=True)
                if code_text and len(code_text) > 20:
                    code_examples.append(code_text)
        
        return code_examples
    
    def scrape_page(self, url: str) -> Optional[Document]:
        """Scrape a single page and return a Document"""
        try:
            # Make request with timeout
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_element = soup.find('title')
            title = title_element.get_text(strip=True) if title_element else "No Title"
            
            # Clean up title
            title = re.sub(r'\s*[\|·\-–—]\s*.*$', '', title)  # Remove site name
            title = title.strip()
            
            # Extract main content
            content = self.extract_main_content(soup, url)
            
            # Skip pages with very little content
            if len(content) < 100:
                return None
            
            # Extract code examples
            code_examples = self.extract_code_examples(soup)
            
            # Create metadata
            metadata = {
                'source': url,
                'title': title,
                'length': len(content),
                'has_code': len(code_examples) > 0,
                'code_count': len(code_examples)
            }
            
            # Add code examples to content if found
            if code_examples:
                content += "\n\nCode Examples:\n" + "\n---\n".join(code_examples[:3])
            
            return Document(page_content=content, metadata=metadata)
            
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {str(e)}")
            return None
    
    def find_documentation_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Find links to other documentation pages"""
        links = []
        found_urls = set()
        
        # Look for links in content area first
        content_areas = soup.select('main, article, .content, .documentation')
        if not content_areas:
            content_areas = [soup]
        
        for area in content_areas:
            for link in area.find_all('a', href=True):
                href = link['href']
                
                # Skip anchors and special links
                if href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # Convert to absolute URL
                full_url = urljoin(current_url, href)
                
                # Normalize URL (remove fragments and query parameters for docs)
                parsed = urlparse(full_url)
                normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                
                # Check if it's a valid documentation URL
                if (self.is_documentation_url(normalized_url) and 
                    normalized_url not in self.visited_urls and
                    normalized_url not in found_urls and
                    len(self.visited_urls) < self.max_pages):
                    
                    found_urls.add(normalized_url)
                    links.append(normalized_url)
        
        return links
    
    def scrape_documentation(self) -> List[Document]:
        """
        Scrape multiple pages from documentation site.
        Returns a list of Document objects containing the scraped content.
        """
        documents = []
        urls_to_visit = [self.base_url]
        
        print(f"Starting documentation scrape from: {self.base_url}")
        print(f"Max pages to crawl: {self.max_pages}")
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_visit.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            print(f"[{len(self.visited_urls) + 1}/{self.max_pages}] Scraping: {current_url}")
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(
                    len(self.visited_urls) + 1,
                    self.max_pages,
                    f"Scraping: {urlparse(current_url).path}"
                )
            
            self.visited_urls.add(current_url)
            
            # Scrape the current page
            doc = self.scrape_page(current_url)
            if doc:
                documents.append(doc)
                print(f"  ✓ Extracted {doc.metadata['length']} characters")
                
                # Find more links to scrape
                try:
                    response = self.session.get(current_url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    new_links = self.find_documentation_links(soup, current_url)
                    
                    # Add new links to visit
                    for link in new_links:
                        if link not in urls_to_visit and link not in self.visited_urls:
                            urls_to_visit.append(link)
                    
                    print(f"  → Found {len(new_links)} new documentation links")
                    
                except Exception as e:
                    print(f"  ✗ Error finding links: {str(e)}")
            else:
                print(f"  ✗ No content extracted")
            
            # Be polite - don't hammer the server
            time.sleep(0.5)
        
        print(f"\n✅ Scraping complete!")
        print(f"  - Pages visited: {len(self.visited_urls)}")
        print(f"  - Documents extracted: {len(documents)}")
        print(f"  - Total content: {sum(doc.metadata['length'] for doc in documents):,} characters")
        
        return documents