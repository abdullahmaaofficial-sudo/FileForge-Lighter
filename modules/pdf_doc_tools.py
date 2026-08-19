from PyPDF2 import PdfMerger,PdfReader,PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pdf2image import convert_from_path
from pdf2docx import Converter
from PIL import Image
import pandas as pd
import subprocess
import markdown
import chardet
import json
import fitz
import uuid
import os


# import platform
# def get_poppler_path():
#     """
#     Intelligently detect Poppler path for cross-platform compatibility.
#     Priority: Environment variable > System detection > None (system PATH)
#     """
#     # 1. Check environment variable (best for deployment)
#     env_path = os.environ.get('POPPLER_PATH')
#     if env_path and os.path.exists(env_path):
#         return env_path
    
#     # 2. Platform-specific detection
#     if platform.system() == 'Windows':
#         # Common Windows installation paths
#         possible_paths = [
#             r'C:\poppler\Library\bin',
#             r'C:\Program Files\poppler\bin',
#             r'C:\poppler-utils\bin',
#         ]
#         for path in possible_paths:
#             if os.path.exists(path):
#                 return path
    
#     # 3. For Linux/Mac, assume poppler is in system PATH
#     return None

# POPPLER_PATH = get_poppler_path()


POPPLER_PATH = r'C:\poppler\Library\bin' # When i am deploying the website i will chnage this.

def get_user_friendly_error(exception):
    """Convert technical exceptions to user-friendly messages"""
    error_str = str(exception).lower()
    
    # Permission errors
    if 'permission' in error_str or 'access' in error_str:
        return "File access denied. Please check file permissions."
    
    # File format errors
    elif 'decode' in error_str or 'invalid' in error_str or 'corrupt' in error_str:
        return "Invalid or corrupted file format."
    
    # Memory errors
    elif 'memory' in error_str or 'size' in error_str:
        return "File is too large to process."
    
    # File not found
    elif 'not found' in error_str or 'no such file' in error_str:
        return "File not found on server."
    
    # PDF specific errors
    elif 'pdf' in error_str and ('encrypted' in error_str or 'password' in error_str):
        return "PDF is password protected."
    
    # Generic fallback with limited technical details
    else:
        # Limit error message length and remove sensitive paths
        clean_error = str(exception).split('\n')[0][:100]
        return f"Processing failed: {clean_error}"

class pdf_tools:
    def __init__(self,paths,output_folder):
        self.multiple_paths = paths
        self.temp_folder = output_folder
        os.makedirs(self.temp_folder, exist_ok=True)

    def merged_pdf(self):
        failed_files = []
        error = []

        pdf_num = uuid.uuid4().hex
        output_path = os.path.join(self.temp_folder, f"merged_pdf_{pdf_num}.pdf")

        if len(self.multiple_paths) >= 2:
            merger = PdfMerger()
            valid_count = 0

            for path , original_filename in self.multiple_paths.items():
                if not os.path.exists(path):
                    print(f"Path doesn't exist: {path}")
                    error.append(f"File path does not exist: {original_filename}")
                    continue
                try:
                    merger.append(path)
                    valid_count += 1
                except Exception as e:
                    print(f"Failed to add PDF '{path}': {e}")
                    failed_files.append({
                        'file': original_filename, 
                        'error': get_user_friendly_error(e)
                    })

            if valid_count >= 2:
                try:
                    merger.write(output_path)
                    print("PDFs merged successfully ✅")
                    id = uuid.uuid4().hex
                    return {
                        'status': 'success',
                        'successful_files': {id:output_path},
                        "failed_files": failed_files,
                        "error": error
                    }
                except Exception as e:
                    print(f"Error: Failed to write merged PDF: {e}")
                    error.append(f"Failed to save merged PDF: {get_user_friendly_error(e)}")
                    return {
                        'status': 'failed',
                        'successful_files': {},
                        "failed_files": failed_files,
                        "error": error
                    }
                finally:
                    merger.close()
            else:
                print("Error: Need at least 2 valid PDF paths to merge!")
                merger.close()
                error.append("At least 2 valid PDF files are required to merge.")
                return {
                        'status': 'failed',
                        'successful_files': {},
                        "failed_files": failed_files,
                        "error": error
                }
        else:
            print("Error: Need at least 2 PDF paths to merge!")
            error.append("At least 2 PDF files are required to merge.")
            return {
                    "status": "failed",
                    "successful_files": {},
                    "failed_files": failed_files,
                    "error": error
                }
             
    def pdf_to_docx(self):
        output_files = {}
        failed_files = []
        error = []

        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"Path doesn't exists! {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            base = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder,f"{base}.docx")
            try:
                obj = Converter(full_path)
                obj.convert(output_path , start = 0, end = None)
                obj.close()
                print("PDF converted to DOCX successfully!")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
            except Exception as e:
                print(f"Error while converting pdf to docx! {full_path}: {e}")
                failed_files.append({
                    'file': original_filename, 
                    'error': get_user_friendly_error(e)
                })          

        if output_files:
            print(f"\n{len(output_files)} file(s) converted successfully!")
            return {
                "status": 'success',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print("Error: No files were converted.")
            error.append("No files were converted.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
    
    def remove_pdfPages(self,pages_to_remove): # Not fixed yet. i will fixed later 
        if os.path.exists(self.multiple_paths[0]):
            filename = os.path.splitext(os.path.basename(self.multiple_paths[0]))[0]
            output_path = os.path.join(self.temp_folder,f"{filename}_modified.pdf")

            try:
                reader = PdfReader(self.multiple_paths[0])
                writer = PdfWriter()
            except Exception as e:
                print(f"Error while making objects: {e}")
                return None

            for i in range(len(reader.pages)):
                if i not in pages_to_remove:
                    try:
                        writer.add_page(reader.pages[i])
                    except Exception as e:
                        print(f"Error while adding page to writer object: {e}")

            with open(output_path, "wb") as f:
                writer.write(f)

            print(f"✅ PDF updated: {output_path}")
            return output_path
        else:
            print(f"Path doesn't exists: {self.multiple_paths[0]}")
            return None

    def pdf_to_images(self ,dpi=200):
        output_imgsFolder  = {}
        failed_files = []
        error = []

        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"Path doesn't exists: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            try:
                pages = convert_from_path(full_path , dpi = dpi , poppler_path= POPPLER_PATH)

                base = os.path.splitext(os.path.basename(original_filename))[0]
                final_folder = os.path.join(self.temp_folder , base)
                os.makedirs(final_folder , exist_ok=True)

                for x , page in enumerate(pages):
                    try:
                        img_path = os.path.join(final_folder, f"{base}_page{x+1}.png")
                        page.save(img_path,"PNG")
                        print(f"✅ {img_path}")
                    except Exception as e:
                        print(f"Error saving page {x + 1}: {e}")

                print(f"✅ Converted {len(pages)} pages from {base} to images")

                id = uuid.uuid4().hex
                output_imgsFolder.update({id:final_folder})
            except Exception as e:
                    print(f"Error while converting pdf {full_path}: {e}")
                    failed_files.append({
                        'file': original_filename,
                        'error': get_user_friendly_error(e)
                    })
        
        if output_imgsFolder:
            print(f"\n✅ Total PDFs converted: {len(output_imgsFolder)}")
            return {
                "status": 'success',
                "indicator": "tool-exception",
                "successful_files": output_imgsFolder,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print("Error: No PDF converted!")
            error.append("No PDFs were converted.")
            return {
                "status": 'failed',
                "successful_files": output_imgsFolder,
                "failed_files": failed_files,
                "error": error
            }

    def images_to_pdf(self):
        output_files = {}
        failed_files = []
        images = []
        error = []

        pdf_num = uuid.uuid4().hex
        filename = f"images_to_pdf_{pdf_num}.pdf"
        output_path = os.path.join(self.temp_folder, filename)

        for img_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(img_path):
                print(f"❌ Path doesn't exist: {img_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            try:
                image = Image.open(img_path).convert("RGB")
                images.append(image)
                print(f"✅ Loaded: {os.path.basename(img_path)}")
            except Exception as e:
                print(f"❌ Error loading {img_path}: {e}")
                failed_files.append({
                    'file': original_filename, 
                    'error': get_user_friendly_error(e)
                })
        
        # Check if we have any valid images
        if not images:
            print("❌ No valid images to convert!")
            error.append("No valid images to convert.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        
        try:
            if len(images) == 1:
                # Single image - no need for append_images
                images[0].save(output_path)
            else:
                # Multiple images
                images[0].save(output_path, save_all=True, append_images=images[1:])

            id = uuid.uuid4().hex
            output_files.update({id:output_path})
            print(f"\n✅ PDF created: {filename} ({len(images)} images)")
        except Exception as e:
            print(f"❌ Error creating PDF: {e}")
            error.append(f"Failed to create PDF: {get_user_friendly_error(e)}")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        

        return {
            "status": 'success',
            "successful_files": output_files,
            "failed_files": failed_files,
            "error": error
        }

    def PDF_TO_TXT(self):
        output_files = {}
        failed_files = []
        error = []

        for full_path ,original_filename in self.multiple_paths.items(): 
            if not os.path.exists(full_path):
                print(f"Path doesn't exists: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue
                
            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder , f"{filename}_extractedText.txt")
            lines = []
            
            try:
                pdf = fitz.open(full_path)

                for page in pdf:
                    text = page.get_text()
                    if text.strip():
                        lines.append(text + '\n')
                pdf.close()

                with open(output_path , 'w' ,encoding='utf-8') as file:
                    file.writelines(lines)
                        
                id = uuid.uuid4().hex
                output_files.update({id:output_path})

                print(f"Text extracted from {full_path}: saved to {output_path} ✅")
            except Exception as e:
                print(f"Error extracting from {full_path}: {e}")
                failed_files.append({
                    'file': original_filename, 
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\nTotal pdf from which text extracted: {len(output_files)}")
            return {
                "status": 'success',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print(f"\nNO text are extarcted!")
            error.append("No text was extracted.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }

    def split_pdf(self, pages_per_pdf): # Not fixed yet. i will fixed later
        output_files = {}

        for path in self.multiple_paths:
            if os.path.exists(path):

                filename = os.path.splitext(os.path.basename(path))[0]
                folder = os.path.join(self.temp_folder, f"{filename}_splitted")
                os.makedirs(folder, exist_ok=True)

                try:
                    reader = PdfReader(path)
                    total_pages = len(reader.pages)
                except Exception as e:
                    print(f"❌ Error loading PDF: {path} — {e}")
                    continue

                counter = 0
                part = 1

                while counter < total_pages:

                    writer = PdfWriter()

                    for i in range(counter, min(counter + pages_per_pdf, total_pages)):
                        writer.add_page(reader.pages[i])

                    output_path = os.path.join(folder, f"{filename}_part{part}.pdf")

                    try:
                        with open(output_path, "wb") as f:
                            writer.write(f)

                        print(f"✅ PDF part created: {output_path}")

                        id = uuid.uuid4().hex
                        output_files.update({id:output_path})

                    except Exception as e:
                        print(f"❌ Error writing part {part}: {e}")

                    counter += pages_per_pdf
                    part += 1

            else:
                print(f"❌ Path doesn't exist: {path}")

        if output_files:
            print(f"\n✅ Total split PDFs: {len(output_files)}")
            return output_files
        else:
            print("\n⚠️ No PDFs were split!")
            return None


class document_tools:
    def __init__(self, paths,output_folder):
        self.multiple_paths = paths
        self.temp_folder = output_folder
        os.makedirs(self.temp_folder, exist_ok=True)

    def docx_to_pdf(self):
        output_files = {}
        failed_files = []
        error = []

        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder, f"{filename}.pdf")

            try:
                result = subprocess.run([
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", self.temp_folder,
                    full_path
                ], check=True, capture_output=True, text=True)
                    
                 # Verify PDF was actually created
                if os.path.exists(output_path):
                    print(f"✓ {full_path} converted to PDF: {output_path}")

                    id = uuid.uuid4().hex
                    output_files.update({id:output_path})
                else:
                    print(f"✗ Conversion failed (output not found): {full_path}")
                    failed_files.append({
                        'file': original_filename,  
                        'error': "Conversion failed - output file not found"
                    })
                        
            except subprocess.CalledProcessError as e:
                print(f"✗ Error converting {full_path}: {e.stderr}")
                failed_files.append({
                    'file': original_filename,  
                    'error': "Document conversion failed. Please ensure the file is not corrupted."
                })
            except Exception as e:
                print(f"✗ Unexpected error converting {full_path}: {str(e)}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\nTotal files converted: {len(output_files)}")
            return {
                "status": 'success',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print("\nNo files converted!")
            error.append("No files were converted.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }

    def TXT_to_PDF(self):
        """Convert text files to PDF with proper line wrapping and pagination"""
        output_files = {}
        failed_files = []
        error = []

        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder, f"{filename}.pdf")

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

                with open(full_path, 'r', encoding="utf-8") as file:
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
                print(f"✅ PDF created: {output_path}")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                    
            except Exception as e:
                print(f"❌ Error converting {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\n✅ Total file(s) converted: {len(output_files)}")
            return {
                "status": 'success',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print("❌ No files converted")
            error.append("No files were converted.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }

    def markdown_to_html(self):
        output_files = {}
        failed_files = []
        error = []
        
        for full_path, original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            try:
                # Read markdown text
                with open(full_path, "r", encoding="utf-8") as f:
                    md_text = f.read()

                # Convert to HTML
                html = markdown.markdown(md_text)

                # Output path
                base = os.path.splitext(os.path.basename(original_filename))[0]
                output_path = os.path.join(self.temp_folder, f"{base}.html")

                # Save HTML
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)

                print(f"✅ Converted to HTML: {output_path}")
                
                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                
            except Exception as e:
                print(f"❌ Error converting {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\nTotal HTML files created: {len(output_files)}")
            return {
                    "status": 'success',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
                }
        else:
            print("\nNo HTML file created!")
            error.append("No HTML files were created.")
            return {
                    "status": 'failed',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
                }
        
    def JSON_to_CSV(self):
        """
        Convert JSON files to CSV
        Handles both JSON arrays and line-delimited JSON (JSONL)
        """
        output_files = {}
        failed_files = []
        error = []

        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"❌ Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder, f"{filename}.csv")

            try:
                # Try to detect encoding
                encoding = self._detect_encoding(full_path)
                    
                with open(full_path, 'r', encoding=encoding) as f:
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
                
                print(f"✅ JSON → CSV: {output_path}")
                print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON format in {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': "Invalid JSON format in file."
                })
            except Exception as e:
                print(f"❌ Error converting {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\n✅ Total files converted: {len(output_files)}")
            return {
                    "status": 'success',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
                }
        else:
            print("\n❌ No files converted!")
            error.append("No files were converted.")
            return {
                    "status": 'failed',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
            }

    def CSV_to_JSON(self, orient='records', indent=2):
        """
        Convert CSV files to JSON
        orient: 'records' (array of objects) or 'values' (array of arrays)
        indent: JSON indentation (None for compact, 2 for readable)
        """
        output_files = {}
        failed_files = []
        error = []

        
        for full_path , original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"❌ Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder, f"{filename}.json")

            try:
                encoding = self._detect_encoding(full_path)
                df = pd.read_csv(full_path, encoding=encoding, sep=None, engine='python')
                
                # Convert to JSON
                json_data = df.to_json(orient=orient, force_ascii=False, indent=indent)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                print(f"✅ CSV → JSON: {output_path}")
                print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id:output_path})
                
            except Exception as e:
                print(f"❌ Error converting {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\n✅ Total files converted: {len(output_files)}")
            return {
                    "status": 'success',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
                }
        else:
            print("\n❌ No files converted!")
            error.append("No files were converted.")
            return {
                    "status": 'failed',
                    "successful_files": output_files,
                    "failed_files": failed_files,
                    "error": error
                }

    def CSV_to_JSONL(self):
        """
        Convert CSV to line-delimited JSON (JSONL)
        Each row becomes a separate JSON object on its own line
        More efficient for large files
        """
        output_files = {}
        failed_files = []
        error = []

        for full_path, original_filename in self.multiple_paths.items():
            if not os.path.exists(full_path):
                print(f"❌ Path doesn't exist: {full_path}")
                error.append(f"File path does not exist: {original_filename}")
                continue

            filename = os.path.splitext(os.path.basename(original_filename))[0]
            output_path = os.path.join(self.temp_folder, f"{filename}.jsonl")

            try:
                encoding = self._detect_encoding(full_path)
                df = pd.read_csv(full_path, encoding=encoding, sep=None, engine='python')
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    for _, row in df.iterrows():
                        json.dump(row.to_dict(), f, ensure_ascii=False)
                        f.write('\n')
                
                print(f"✅ CSV → JSONL: {output_path}")
                print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")

                id = uuid.uuid4().hex
                output_files.update({id: output_path})
                    
            except Exception as e:
                print(f"❌ Error converting {full_path}: {e}")
                failed_files.append({
                    'file': original_filename,  
                    'error': get_user_friendly_error(e)
                })

        if output_files:
            print(f"\n✅ Total files converted: {len(output_files)}")
            return {
                "status": 'success',  # Fixed: was 'failed'
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }
        else:
            print("\n❌ No files converted!")
            error.append("No files were converted.")
            return {
                "status": 'failed',
                "successful_files": output_files,
                "failed_files": failed_files,
                "error": error
            }

    def _detect_encoding(self, file_path):
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(100000))  # Read first 100KB
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'  # Default fallback
