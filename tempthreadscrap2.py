import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import argparse
from tqdm import tqdm


class PdfDownload:

    def __init__(self, folder_location, extention_to_find, depth_level):

        self.folder_location = folder_location
        self.downloaded_files = set()
        self.extention_to_find = extention_to_find
        self.depth_level = depth_level


# Download PDFs using url and filename

    def download_pdf(self, url):

        filename = os.path.join(self.folder_location, url.split('/')[-1])
        if os.path.exists(filename):
            print(f'{filename} already exists, skipping download...')
            return
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open(filename, 'wb') as f, tqdm(
            total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=filename,
                ncols=100,

        ) as progress_bar:

            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                progress_bar.update(len(data))

        print(f'{filename} was downloaded...')
        self.downloaded_files.add(url)
        self.saved_links(self.downloaded_files)


# Get Links From Mainlinks And SubLinks


    def get_pdfs(self, http_urls):

        pdf_links = []
        for url in http_urls:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser',
                                     from_encoding="iso-8859-1")

                main_links = soup.find_all('a', href=True)
                for link in main_links:

                    href = link['href']

                    if self.get_extention(href):

                        pdf_links.append(urljoin(url, href))

            except Exception as e:
                print(f"pdf error occur:{e}")
                continue
        return pdf_links

    def get_links(self, urls, depth=0):

        http_links = []

        for url in urls:
            print(url)

            if depth == self.depth_level:
                return
            else:
                try:

                    response = requests.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser',
                                         from_encoding="iso-8859-1")

                    sub_links = soup.find_all('a', href=True)
                    for sub_link in sub_links:

                        sub_href = sub_link['href']
                        try:

                            if sub_href.startswith('http'):

                                http_links.append(sub_href)

                            elif sub_href.startswith('/'):
                                http_links.append(
                                    urljoin(url, sub_href))
                            self.get_links((sub_href), depth+1)

                        except Exception as e:
                            print(f"error occur:{e}")
                            continue

                except Exception as e:
                    print(f"ssl error occur:{e}")
                    return

        return http_links

    def get_extention(self, url):
        return url.lower().endswith(self.extention_to_find.lower())


# execute program with thread pool using urls


    def start_program(self, urls):
        with ThreadPoolExecutor(max_workers=5) as executor:

            executor.map(self.download_pdf, urls)


# validation for folder_location and Urls
def validation(folder_location, urls_file):

    if os.path.exists(folder_location):
        print(f"{folder_location} already exists\n")
    else:
        os.mkdir(folder_location)

    if os.path.exists(urls_file) and urls_file.endswith('.txt'):
        print(f"{urls_file} already exists\n")

    else:
        print(f"{urls_file} doesn't exists or give txt file")
        return False
    return True


def read_file(urls_file):

    try:
        with open(urls_file, 'r') as f:
            urls = f.readlines()
            urls = [url.strip() for url in urls]

            return urls

    except FileNotFoundError:
        print(
            f"File {urls_file} doesn't exist")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Get Folder Location To Download PDFs after given URL")
    parser.add_argument("--f", required=True,
                        help="Give Your Folder Location.")
    parser.add_argument("--u", required=True,
                        help="File containing list of URLs.")
    parser.add_argument("--ext", required=True,
                        help="Give extention to find URLs.")
    parser.add_argument("--lvl", required=True,
                        help="Add levels for recursion")
    args = parser.parse_args()

    isvalidate = validation(args.f, args.u)
    if isvalidate:
        urls_file = args.u
        read_url = read_file(urls_file)

        try:
            if args.lvl == int(args.lvl):
                return
        except ValueError:
            print("level only accept integer value")

        pdf_downloader = PdfDownload(args.f, args.ext, args.lvl)

        # pdf_downloader = PdfDownload(args.f, read_url)
        http_links = pdf_downloader.get_links(read_url)
        pdf_links = pdf_downloader.get_pdfs(http_links)
        # pdf_downloader.start_program(pdf_links)


if __name__ == "__main__":
    main()
