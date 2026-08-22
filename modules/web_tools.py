from markdownify import markdownify as md_convert
from urllib.parse import urljoin, urlparse
from .pdf_tools import BaseForTools
from bs4 import BeautifulSoup
import requests
import qrcode
import json
import uuid
import re
import os


class WebTools(BaseForTools):
    def __init__(self, paths_dic, output_folder):
        # paths_dic: {url_or_text: label}  — label is just a display name, same role as
        # original_filename in the other classes, used for naming output files
        super().__init__(paths_dic, output_folder)
        if self.not_exists:
            self.return_d['error'] = "Invalid or empty entry — please check and try again"

    def validate_input_paths(self):
        """Overrides the file-existence check from BaseForTools — here we just
        reject empty/blank entries. Individual methods that need a fetchable
        URL validate the scheme themselves, since not every tool (e.g. QR codes)
        requires a URL at all."""
        invalid = []
        for entry in self.Input_paths.keys():
            if not entry or not entry.strip():
                invalid.append(self.Input_paths[entry])
        return invalid

    def _safe_filename(self, text, max_length=50):
        """Turns a URL or arbitrary label into a filesystem-safe base name."""
        if text.startswith('http://') or text.startswith('https://'):
            parsed = urlparse(text)
            base = (parsed.netloc + parsed.path).strip('/')
        else:
            base = text

        safe = re.sub(r'[^a-zA-Z0-9]+', '_', base).strip('_')
        return safe[:max_length] or uuid.uuid4().hex[:8]

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)

    def url_to_text(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for url, label in self.Input_paths.items():
            if not self._is_valid_url(url):
                print(f"Not a valid http(s) URL: {url}")
                failed_files.append(label or url)
                continue

            try:
                response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(['script', 'style', 'noscript']):
                    tag.decompose()

                text = soup.get_text(separator='\n', strip=True)

                filename = self._safe_filename(label or url)
                output_path = os.path.join(self.output_folder, f"{filename}.txt")

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                print(f"Extracted text from {url}: saved to {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                failed_files.append(label or url)
            except Exception as e:
                print(f"Error extracting text from {url}: {e}")
                failed_files.append(label or url)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to extract text from these/this url(s)'
            }

        print(f"\nTotal urls processed: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def extract_metadata(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for url, label in self.Input_paths.items():
            if not self._is_valid_url(url):
                print(f"Not a valid http(s) URL: {url}")
                failed_files.append(label or url)
                continue

            try:
                response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                def get_meta(name=None, prop=None):
                    tag = soup.find('meta', attrs={'name': name}) if name else soup.find('meta', attrs={'property': prop})
                    return tag['content'].strip() if tag and tag.get('content') else None

                favicon_tag = soup.find('link', rel=lambda r: r and 'icon' in r.lower())
                favicon = urljoin(url, favicon_tag['href']) if favicon_tag and favicon_tag.get('href') else None

                metadata = {
                    'url': url,
                    'title': soup.title.string.strip() if soup.title and soup.title.string else None,
                    'description': get_meta(name='description') or get_meta(prop='og:description'),
                    'og_title': get_meta(prop='og:title'),
                    'og_image': get_meta(prop='og:image'),
                    'favicon': favicon
                }

                filename = self._safe_filename(label or url)
                output_path = os.path.join(self.output_folder, f"{filename}_metadata.json")

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                print(f"Extracted metadata from {url}: saved to {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                failed_files.append(label or url)
            except Exception as e:
                print(f"Error extracting metadata from {url}: {e}")
                failed_files.append(label or url)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to extract metadata from these/this url(s)'
            }

        print(f"\nTotal urls processed: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def extract_links(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for url, label in self.Input_paths.items():
            if not self._is_valid_url(url):
                print(f"Not a valid http(s) URL: {url}")
                failed_files.append(label or url)
                continue

            try:
                response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                base_domain = urlparse(url).netloc

                internal, external, seen = [], [], set()

                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    if not href or href.startswith(('#', 'mailto:', 'javascript:')):
                        continue

                    full_url = urljoin(url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    (internal if urlparse(full_url).netloc == base_domain else external).append(full_url)

                result = {
                    'url': url,
                    'internal_links': internal,
                    'external_links': external,
                    'total_links': len(internal) + len(external)
                }

                filename = self._safe_filename(label or url)
                output_path = os.path.join(self.output_folder, f"{filename}_links.json")

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print(f"Extracted {result['total_links']} links from {url}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                failed_files.append(label or url)
            except Exception as e:
                print(f"Error extracting links from {url}: {e}")
                failed_files.append(label or url)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to extract links from these/this url(s)'
            }

        print(f"\nTotal urls processed: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def generate_qr_code(self):
        """Input_paths here maps arbitrary text/data (not necessarily a URL) to a label."""
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for data, label in self.Input_paths.items():
            try:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=10,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                filename = self._safe_filename(label or data)
                output_path = os.path.join(self.output_folder, f"{filename}_qr.png")
                img.save(output_path)

                print(f"Generated QR code for '{data[:50]}': saved to {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except Exception as e:
                print(f"Error generating QR code for '{data[:50]}': {e}")
                failed_files.append(label or data)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to generate QR code(s) for these/this entry'
            }

        print(f"\nTotal QR codes generated: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def url_to_markdown(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for url, label in self.Input_paths.items():
            if not self._is_valid_url(url):
                print(f"Not a valid http(s) URL: {url}")
                failed_files.append(label or url)
                continue

            try:
                response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(['script', 'style', 'noscript']):
                    tag.decompose()

                # Prefer the main content area if the page has one, to avoid
                # pulling in nav bars/footers/sidebars as markdown noise
                main_content = soup.find('main') or soup.find('article') or soup.find('body') or soup

                markdown_text = md_convert(str(main_content), heading_style="ATX", strip=['script', 'style'])
                markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text).strip()  # collapse excess blank lines

                filename = self._safe_filename(label or url)
                output_path = os.path.join(self.output_folder, f"{filename}.md")

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)

                print(f"Converted {url} to markdown: saved to {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                failed_files.append(label or url)
            except Exception as e:
                print(f"Error converting {url} to markdown: {e}")
                failed_files.append(label or url)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this url(s) to markdown'
            }

        print(f"\nTotal urls converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}