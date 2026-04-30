import os
import requests
from bs4 import BeautifulSoup
import time

def crawl_bahamut_wiki(game_name, wiki_id, output_filename):
    url = f"https://wiki.gamer.com.tw/wiki.php?n={wiki_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching {url} for {game_name}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main wiki content
        content_div = soup.find('div', id='wiki-main') or soup.find('div', class_='wiki-content') or soup.find('div', class_='BH-lbox')
        
        if content_div:
            # Remove scripts and styles
            for script in content_div(["script", "style"]):
                script.decompose()
            text = content_div.get_text(separator='\n', strip=True)
        else:
            print("Warning: Specific container not found. Falling back to tag extraction.")
            tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td'])
            text = '\n'.join([tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)])
            
        output_dir = os.path.join('working', game_name, 'raw')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print(f"Success! Data saved to {output_path}")
        return True
            
    except Exception as e:
        print(f"An error occurred during crawling: {e}")
        return False

if __name__ == "__main__":
    # Aion ID: 11815 (永恆紀元)
    # We can also try to crawl sub-pages if we have links, but let's start with the main page.
    crawl_bahamut_wiki("Aion", "11815:%E6%B0%B8%E6%81%86%E7%B4%80%E5%85%83", "bahamut_wiki_main.txt")
    
    # Adding a small delay to be polite
    time.sleep(1)
    
    # Optional: Crawl specific lore pages if URLs are known
    # Example: Story/Lore page
    # crawl_bahamut_wiki("Aion", "11815:%E4%B8%96%E7%95%8C%E8%A7%80", "bahamut_wiki_worldview.txt")
