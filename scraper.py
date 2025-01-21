import requests
from bs4 import BeautifulSoup
import os
import subprocess
import sys

LINKS_FILE = "known_links.txt"

def load_known_links(filename):
    """
    Load the set of known links from a file.
    If the file does not exist, return an empty set.
    """
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_new_links(links):
    """
    Append new links to the file.
    """
    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        f.write('\n' + '\n'.join(links))
    
    with open("new_links.txt", "a", encoding="utf-8") as f:
        f.write('\n'.join(links))

def get_article_links_from_page(page_html):
    """
    Given the HTML content of a White House News page,
    extract all article links found inside:
    
      <h2 class="wp-block-post-title has-heading-4-font-size">
        <a href="...">Title</a>
      </h2>
    """
    soup = BeautifulSoup(page_html, "html.parser")
    article_links = []
    
    # Find all <h2> tags with the class "wp-block-post-title has-heading-4-font-size"
    h2_tags = soup.find_all("h2", class_="wp-block-post-title has-heading-4-font-size")
    
    for h2 in h2_tags:
        a_tag = h2.find("a", href=True)
        if a_tag:
            link = a_tag["href"]
            article_links.append(link)
    
    # Deduplicate if needed
    return list(set(article_links))

def main():
    known_links = load_known_links(LINKS_FILE)
    page_number = 1
    open('new_links.txt', 'w').close()
    while True:
        url = f"https://www.whitehouse.gov/news/page/{page_number}/"
        print(f"Scraping: {url}")
        
        # Request the page
        response = requests.get(url)
        
        # If the page doesn't exist or request fails, break
        if response.status_code != 200:
            print("Reached a non-existent page or encountered an error. Stopping.")
            break
        
        # Extract article links on this page
        article_links = get_article_links_from_page(response.text)
        
        if not article_links:
            print("No article links found on this page. Stopping.")
            break
        
        # Determine which links are new
        new_links = [link for link in article_links if link not in known_links]
        
        # If all links on this page are new, store them and move on
        if len(new_links) > 0:
            print(f"Found {len(new_links)} new links on page {page_number}.")
            known_links.update(new_links)
            save_new_links(new_links)
            page_number += 1
        else:
            print("Encountered at least one link that's already known. Stopping.")
            break
        
    # Dispatch Changes
    subprocess.run([sys.executable, "dispatcher.py"])

if __name__ == "__main__":
    main()
