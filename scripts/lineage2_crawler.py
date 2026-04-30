import os
import requests
from bs4 import BeautifulSoup

def crawl_bahamut_wiki():
    url = "https://wiki.gamer.com.tw/wiki.php?n=925:%E5%A4%A9%E5%A0%82II"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Attempt to find the main wiki content container
        content_div = soup.find('div', id='wiki-main') or soup.find('div', class_='wiki-text') or soup.find('div', class_='wiki-content') or soup.find('div', class_='BH-lbox')
        
        if content_div:
            text = content_div.get_text(separator='\n', strip=True)
        else:
            # Fallback to extracting all p and h tags
            print("Warning: Specific container not found. Falling back to tag extraction.")
            tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li'])
            text = '\n'.join([tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)])
            
        output_dir = os.path.join('working', 'Lineage_II', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'bahamut_wiki_crawled.txt')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print(f"Success! Data saved to {output_path}")
            
    except Exception as e:
        print(f"An error occurred during crawling: {e}")

if __name__ == "__main__":
    crawl_bahamut_wiki()