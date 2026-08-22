from reportlab.lib.pagesizes import letter
from .pdf_tools import BaseForTools
from reportlab.pdfgen import canvas
import pandas as pd
import subprocess
import xmltodict
import markdown 
import chardet
import json
import uuid
import os


class DocTools(BaseForTools):
    def __init__(self, paths_dic, output_folder):
        super().__init__(paths_dic, output_folder)

    def _detect_encoding(self, file_path):
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(100000))  # Read first 100KB
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'  # Default fallback

    def json_to_csv(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path , original_filename in self.Input_paths.items():

            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.csv")
            try:
                # Try to detect encoding
                encoding = self._detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    first_char = f.read(1)
                    f.seek(0)
                    
                    # Check if it's a JSON array or JSONL
                    if first_char == '[':
                        # Standard JSON array
                        data = json.load(f)
                        df = pd.DataFrame(data)
                    else:
                        # Line-delimited JSON (JSONL)
                        data = [json.loads(line) for line in f if line.strip()]
                        df = pd.DataFrame(data)
                    
                df.to_csv(output_path, index=False, encoding='utf-8')
                
                print(f"JSON to CSV: {output_path}")
                print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                     
            except json.JSONDecodeError as e:
                print(f"Invalid JSON format in {file_path}: {e}")
                failed_files.append(original_filename)
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False, 
                'files': failed_files, 
                'output_files':output_files, 
                'error':'Failed to convert these/this file(s), please try again'
                }
        
        print(f"\nTotal files converted: {len(output_files)}")
        return {"status": True, "output_files": output_files,}

    def csv_to_json(self, orient='records', indent=2):
        if self.not_exists: return self.return_d

        """
        orient: 'records' (array of objects) or 'values' (array of arrays)
        indent: JSON indentation (None for compact, 2 for readable)
        """
        output_files = {}
        failed_files = []
 
        for file_path , original_filename in self.Input_paths.items():

            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.json")

            try:
                encoding = self._detect_encoding(file_path)
                df = pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
                
                # Convert to JSON
                json_data = df.to_json(orient=orient, force_ascii=False, indent=indent)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                print(f"CSV to JSON: {output_path}")
                print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                    "status": False,
                    "files": failed_files,
                    "output_files": output_files,
                    "error": 'Failed to convert these/this file(s), please try again'
                }
        
        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def csv_to_jsonl(self):
        if self.not_exists: return self.return_d

        """
        Convert CSV to line-delimited JSON (JSONL)
        Each row becomes a separate JSON object on its own line
        More efficient for large files
        """
        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
        
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.jsonl")

            try:
                encoding = self._detect_encoding(file_path)
                df = pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    for _, row in df.iterrows():
                        json.dump(row.to_dict(), f, ensure_ascii=False)
                        f.write('\n')
                
                print(f"CSV to JSONL: {output_path}")
                print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})
                    
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                "status": False,
                "files": failed_files,
                "output_files": output_files,
                "error": 'Failed to convert these/this file(s), please try again'
            }
                
        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}
    
    def text_to_pdf(self):
        if self.not_exists: return self.return_d

        """Convert text files to PDF with proper line wrapping and pagination"""
        output_files = {}
        failed_files = []

        for file_path , original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.pdf")

            try:
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                    
                # Margins and text area
                left_margin = 50
                right_margin = width - 50
                top_margin = height - 50
                bottom_margin = 50
                line_height = 15
                max_line_width = right_margin - left_margin

                y = top_margin

                with open(file_path, 'r', encoding="utf-8") as file:
                    for line in file:
                        line = line.rstrip('\n\r')
                        
                        # Handle empty lines
                        if not line:
                            y -= line_height
                            if y < bottom_margin:
                                c.showPage()
                                y = top_margin
                            continue
                        
                        # Word wrap long lines
                        words = line.split()
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + (" " if current_line else "") + word
                            
                            # Check if line fits
                            if c.stringWidth(test_line) <= max_line_width:
                                current_line = test_line
                            else:
                                # Draw current line and start new one
                                if current_line:
                                    c.drawString(left_margin, y, current_line)
                                    y -= line_height
                                    
                                    if y < bottom_margin:
                                        c.showPage()
                                        y = top_margin
                                
                                current_line = word
                        
                        # Draw remaining text
                        if current_line:
                            c.drawString(left_margin, y, current_line)
                            y -= line_height
                            
                            if y < bottom_margin:
                                c.showPage()
                                y = top_margin

                c.save()
                print(f"PDF created: {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                    
            except Exception as e:
                print(f"Error converting {original_filename}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                "status": False,
                "files": failed_files,
                "output_files": output_files,
                "error": 'Failed to convert these/this file(s), please try again'
            }
                
        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def markdown_to_html(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            try:
                # Read markdown text
                with open(file_path, "r", encoding="utf-8") as f:
                    md_text = f.read()

                # Convert to HTML
                html = markdown.markdown(md_text)

                # Output path
                base = os.path.splitext(os.path.basename(original_filename))[0]
                output_path = os.path.join(self.output_folder, f"{base}.html")

                # Save HTML
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)

                print(f"✅ Converted to HTML: {output_path}")
                
                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                
            except Exception as e:
                print(f"Error converting {original_filename}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                "status": False,
                "files": failed_files,
                "output_files": output_files,
                "error": 'Failed to convert these/this file(s), please try again'
            }
                
        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def excel_to_csv(self, sheet_name=0):
        """sheet_name: sheet index (0 = first sheet) or sheet name string"""
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.csv")

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                df.to_csv(output_path, index=False, encoding='utf-8')

                print(f"Excel to CSV: {output_path}")
                print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this file(s), please try again'
            }

        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def csv_to_excel(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.xlsx")

            try:
                encoding = self._detect_encoding(file_path)
                df = pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
                df.to_excel(output_path, index=False, engine='openpyxl')

                print(f"CSV to Excel: {output_path}")
                print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this file(s), please try again'
            }

        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def xml_to_json(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.json")

            try:
                encoding = self._detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    xml_content = f.read()

                data_dict = xmltodict.parse(xml_content)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data_dict, f, ensure_ascii=False, indent=2)

                print(f"XML to JSON: {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this file(s), please try again'
            }

        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

    def json_to_xml(self, root_tag="root"):
        """root_tag: element name to wrap the JSON under if it doesn't already have a single root key"""
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}.xml")

            try:
                encoding = self._detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)

                # xmltodict.unparse requires exactly one root key
                if isinstance(data, dict) and len(data) == 1:
                    payload = data
                else:
                    payload = {root_tag: data}

                xml_str = xmltodict.unparse(payload, pretty=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)

                print(f"JSON to XML: {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

            except json.JSONDecodeError as e:
                print(f"Invalid JSON format in {file_path}: {e}")
                failed_files.append(original_filename)
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this file(s), please try again'
            }

        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}

# ==========================================================================================================
# These functions will not work in production (Vercel)

    def docx_to_pdf(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path , original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            desired_output_path = os.path.join(self.output_folder, f"{filename}.pdf")
            actual_output_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(file_path))[0] + '.pdf')

            try:
                subprocess.run([
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", self.output_folder,
                    file_path
                ], check=True, capture_output=True, text=True)
                    
                 # Verify PDF was actually created
                if os.path.exists(actual_output_path):
                    os.replace(actual_output_path, desired_output_path)
                    print(f"{file_path} converted to PDF: {desired_output_path}")

                    id = uuid.uuid4().hex
                    output_files.update({id: desired_output_path})
                else:
                    print(f"Conversion failed (output not found): {file_path}")
                    failed_files.append(original_filename)
                        
            except subprocess.CalledProcessError as e:
                print(f"Error converting {file_path}: {e.stderr}")
                failed_files.append(original_filename)

            except Exception as e:
                print(f"Unexpected error converting {file_path}: {str(e)}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False, 
                'files': failed_files, 
                'output_files':output_files, 
                'error':'Failed to convert these/this file(s), please try again'
            }
        
        print(f"\n✅ Total files converted: {len(output_files)}")
        return {"status": True, "output_files": output_files,}

    def html_to_pdf(self):
        if self.not_exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            desired_output_path = os.path.join(self.output_folder, f"{filename}.pdf")
            actual_output_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(file_path))[0] + '.pdf')

            try:
                subprocess.run([
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", self.output_folder,
                    file_path
                ], check=True, capture_output=True, text=True)

                if os.path.exists(actual_output_path):
                    os.replace(actual_output_path, desired_output_path)
                    print(f"{original_filename} converted to PDF: {desired_output_path}")

                    id = uuid.uuid4().hex
                    output_files.update({id: desired_output_path})
                else:
                    print(f"Conversion failed (output not found): {file_path}")
                    failed_files.append(original_filename)

            except subprocess.CalledProcessError as e:
                print(f"Error converting {file_path}: {e.stderr}")
                failed_files.append(original_filename)
            except Exception as e:
                print(f"Unexpected error converting {file_path}: {str(e)}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False,
                'files': failed_files,
                'output_files': output_files,
                'error': 'Failed to convert these/this file(s), please try again'
            }

        print(f"\nTotal files converted: {len(output_files)}")
        return {'status': True, 'output_files': output_files}