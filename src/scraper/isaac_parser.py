from bs4 import BeautifulSoup
import os
print(os.listdir())
def parse_local_file():
    with open("Items.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    rows = soup.find_all('tr')
    with open("isaac_manual.txt", "w", encoding="utf-8") as f:
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                flavor = cols[3].get_text(strip=True)
                if(len(list(name.split())) > 2):
                    f.write(f'"{name}",\n')
                if(len(list(flavor.split())) > 2):
                    f.write(f'"{flavor}",\n')
    print("Local file parsed successfully!")

parse_local_file()