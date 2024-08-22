from time import sleep
import requests
import urllib.parse
from bs4 import BeautifulSoup
from io import BytesIO
import mysql.connector
from mysql.connector import Error

db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'odc_keys_witel_jember'
}

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
    except Error as e:
        print(f"\033[91mError \033[96mcreate_connection\033[0m func :: {e}")
    return connection

def close_connection(connection):
    if connection.is_connected():
        connection.close()

def scaping(target_url, cookie , token):
    

    cookies = {
        'ci_session': '1tn70iu7v4eo5o5a5gumufvp780m3im7'
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
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 5:
                    fifth_td = tds[4]
                    a_tag = fifth_td.find('a')
                    if a_tag:
                        href = a_tag.get('href')
                        if href:
                            try:
                                parts = href.split('/')
                                if len(parts) > 6:
                                    odc_name = parts[6].split('_')[0]
                                    nama = getNama(odc_name)
                                    
                                    if nama is not None:
                                        pdf_data = download_pdf(href)
                                        if pdf_data:
                                            link = upload_file(cookie, token, pdf_data, href.split('/')[6])
                                            insertLink(odc_name, link)
                                    else:
                                        print(f"\033[91mError \033[0m {href}")
                                else:
                                    print(f"Invalid href format: {href}")
                            except (IndexError, ValueError) as e:
                                print(f"Skipping href: {href}, Error: {e}")
                        else:
                            print(f"No href attribute found in {fifth_td}")
                    else:
                        print(f"No <a> tag found in {fifth_td}")
                else:
                    print(f"Baris tidak memiliki cukup <td> elements")
        else:
            print('Tag <tbody> tidak ditemukan')
    else:
        print('Tag <div> dengan kelas "fixTableHead" tidak ditemukan')

def download_pdf(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        print(f"Failed to download PDF: {response.status_code}")
        return None

def upload_file(cookie, token, file_data, file_name):
    file_size = len(file_data.getvalue())
    upload_url = 'https://telkom.dropup.id/ServicesPortal/upload/folders/79128'

    headers = {
        'Cookie': f"JSESSIONID={str(cookie)}",
    }

    files = {
        'file': (file_name, file_data, 'application/pdf'),
    }

    data = {
        'name': file_name,
        'Filename': file_name,
        'fullpath': f'https://telkom.dropup.id/ServicesPortal/webdav/Layout-odc/{urllib.parse.quote(file_name)}',
        'fileSize': str(file_size),
        'X-CTERA-TOKEN': str(token)
    }

    response = requests.post(upload_url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        print(f"{file_name} berhasil di-upload")
        publink = get_link(cookie, token, file_name)
        return publink
    else:
        print(f"Failed to upload file: {response.status_code}")
        print(f"Response Text: {response.text}")

def get_link(cookie, token, file_name):
    url = 'https://telkom.dropup.id/ServicesPortal/api?format=jsonext'

    headers = {
        'Cookie': f"JSESSIONID={str(cookie)}",
        'X-Ctera-Token': str(token),
        'Content-Type': 'application/xml;charset=UTF-8',
    }

    xml_data = f"""<obj>
        <att id="type"><val>user-defined</val></att>
        <att id="name"><val>createShare</val></att>
        <att id="param">
            <obj class="CreateShareParam">
                <att id="url"><val>/ServicesPortal/webdav/Layout-odc/{file_name}</val></att>
                <att id="share">
                    <obj class="ShareConfig">
                        <att id="accessMode"><val>ReadOnly</val></att>
                        <att id="protectionLevel"><val>publicLink</val></att>
                        <att id="expiration"><val>2024-09-20</val></att>
                        <att id="invitee">
                            <obj class="Collaborator">
                                <att id="type"><val>external</val></att>
                            </obj>
                        </att>
                    </obj>
                </att>
            </obj>
        </att>
    </obj>"""

    response = requests.post(url, headers=headers, data=xml_data)

    if response.status_code == 200:
        try:
            data = response.json()
            public_link = data.get('publicLink')
            return public_link
        except ValueError:
            print("Response bukan dalam format JSON.")
    else:
        print(f"Request gagal dengan status kode: {response.status_code}")
        print(f"Response Text: {response.text}")

def login_database():
    login_url = 'https://telkom.dropup.id/ServicesPortal/j_security_check'

    login_data = {
        'j_username': '940454',
        'j_password': 'Bismillah24',
        'language': ''
    }

    login_response = requests.post(login_url, data=login_data)

    if login_response.status_code == 200:
        cookies = login_response.cookies
        for cookie in cookies:
            print(f'Cookie Name: {cookie.name}, Cookie Value: {cookie.value}')
        
        get_url = 'https://telkom.dropup.id/ServicesPortal/api/currentTime?format=jsonext'

        get_response = requests.get(get_url, cookies=cookies)
        x_ctera_token = get_response.headers.get('X-CTERA-TOKEN')

        return cookies.get('JSESSIONID'), x_ctera_token
    else:
        print(f"Login failed: {login_response.status_code}")
        return None, None

def getNama(nama):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Perbaiki query SQL dengan parameterized query
        query = "SELECT * FROM odc_info WHERE Nama = %s;"
        cursor.execute(query, (f'ODC-{nama}',))
        print(f"ODC-{nama}")
        user = cursor.fetchone()
        return user
    except Error as e:
        return None
    finally:
        close_connection(connection)

def insertLink(nama, link):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None

    cursor = connection.cursor()
    try:
        query = "UPDATE odc_info SET link_layout = %s WHERE Nama = %s"
        cursor.execute(query, (link, f'ODC-{nama}'))
        connection.commit()
        print(f"{cursor.rowcount} row(s) affected ODC-{nama}")
    except Error as e:
        print(f"Error: {e}")
    finally:
        close_connection(connection)

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

    i = 1
    cookie, token = login_database()

    for x in data:

        if i % 50 == 0:
            cookie, token = login_database()
            i = 1
        else:
            i += 1

        scaping(x, cookie, token)
        sleep(0.2)

if __name__ == '__main__':
    main()
