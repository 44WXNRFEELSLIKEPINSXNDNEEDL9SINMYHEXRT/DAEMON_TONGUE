from bs4 import BeautifulSoup
import json

def parse_fandom_quotes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    items = soup.find_all('li')
    with open("kayn.txt", "w", encoding="utf-8") as f:
        for item in items:
            quote_tag = item.find('i')
            if quote_tag:
                quote_text = quote_tag.get_text(strip=True)
                quote_text = quote_text.replace(",","")
                context = ""
                parent = item.find_parent()
                header = item.find_previous(['h2', 'h3'])
                if header:
                    context = header.get_text(strip=True).replace('[edit | edit source]', '')
                f.write(f'{quote_text},\n')
    return results

data = parse_fandom_quotes('kayn.html')