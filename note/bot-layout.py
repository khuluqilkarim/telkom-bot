import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

def scaping(target_url):
    cookies = {
        'ci_session': 'p58ejhlu4ibjlb3nva1itcs5lv3fsmsi'
    }

    session = requests.Session()
    session.cookies.update(cookies)

    response = session.get(target_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    div = soup.find('div', class_='fixTableHead')

    if div:
        tbody = div.find('tbody')

        if tbody:
            rows = tbody.find_all('tr')
            i = 1
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 5:
                    fifth_td = tds[4]
                    a_tag = fifth_td.find('a')
                    if a_tag:
                        href = a_tag.get('href')
                        if href:
                            print(f"{i}. {href}")
                            # downloadFile(href)
                    else:
                        print(f"{i}. {fifth_td.get_text(strip=True)}")
                    i += 1
                else:
                    print(f"Baris {i} tidak memiliki cukup <td> elements")
                    i += 1
        else:
            print('Tag <tbody> tidak ditemukan')
    else:
        print('Tag <div> dengan kelas "fixTableHead" tidak ditemukan')

def downloadFile(target_url):
    local_filename = target_url.split('/')[-1]
    file_path = f"./Layout/{local_filename}"
    
    response = requests.get(target_url, stream=True)


    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File berhasil didownload dan disimpan sebagai {local_filename}")
    else:
        print(f"Terjadi kesalahan: {response.status_code}")

def main():
    data = [
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20INNER&sto=BWG',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20INNER&sto=KET',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20INNER&sto=WSO',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20OUTER&sto=BCK',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20OUTER&sto=MCR',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BANYUWANGI%20-%20OUTER&sto=RGJ',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BONDOWOSO&sto=BOW',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BONDOWOSO&sto=PRJ',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20BONDOWOSO&sto=SKS',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20GENTENG&sto=GEN',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20GENTENG&sto=GLM',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20GENTENG&sto=KBR',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20GENTENG&sto=PSG',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20JEMBER%20INNER&sto=JER',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20JEMBER%20OUTER&sto=AJS',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20JEMBER%20OUTER&sto=KLT',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20JEMBER%20OUTER&sto=SKW',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20JEMBER%20OUTER&sto=SPO',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20KEBONSARI&sto=KBS',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20SITUBONDO&sto=ASB',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20SITUBONDO&sto=BKI',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20SITUBONDO&sto=MLD',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20SITUBONDO&sto=SIT',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20TANGGUL%20INNER&sto=BUG',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20TANGGUL%20INNER&sto=KNO',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20TANGGUL%20INNER&sto=PUG',
        'https://ixsa.telkom.co.id/3.0/index.php/index_odc?reg=5&witel=JEMBER&sektor=SEKTOR%20-%20JEMBER%20-%20TANGGUL%20INNER&sto=TGU'
    ]

    for x in data:
        scaping(x)
    

if __name__ == '__main__':
    main()
