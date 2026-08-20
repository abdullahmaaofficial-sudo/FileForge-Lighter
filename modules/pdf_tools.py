from pdf2docx import Converter
from PyPDF2 import PdfMerger
from PIL import Image
import pymupdf
import random
import shutil
import uuid
import os

class BaseForTools:
    def __init__(self,paths_dic: dict, output_folder : str):
        self.Input_paths = paths_dic
        self.output_folder = output_folder
        self.exists = self.validate_input_paths()
        self.return_d = {'status': False,'files': self.exists,'error': "file(s) not exists in server, try to re-upload"}

    def validate_input_paths(self):
        all_exists = all(os.path.exists(path) for path in self.Input_paths.keys())
        if not all_exists: return [self.Input_paths[path] for path in self.Input_paths.keys() if not os.path.exists(path)]
        return []


class PDFTools(BaseForTools):
    def __init__(self, paths_dic, output_folder):
        super().__init__(paths_dic, output_folder)
        
    def combine_pdf(self):
        if not self.exists: return self.return_d

        if not len(self.Input_paths) >= 2: 
            return {'status': False,'error': "Not enough pdf, pdf should be more than 1"}
        
        failed_files = []

        pdf_num = random.randint(100,1000)
        output_path = os.path.join(self.output_folder, f"combined pdf {pdf_num}.pdf")
        merger = PdfMerger()

        for file_path , original_filename in self.Input_paths.items():
            try:
                merger.append(file_path)
            except Exception as e:
                print(f"falied to append PDF {original_filename}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {'status': False, 'files': failed_files, 'error': 'Failed to append these pdf(s), please try again'}

        try:
            merger.write(output_path)
            print(f"PDF is Combined: {output_path}")
            id = uuid.uuid4().hex
            return {'status': True, 'output_files': {id:output_path}}
        except Exception as e:
            print(f"Falied to merged PDf: {e}")
            return {'status': False, 'error': 'Failed to combine pdf(s), please try again'}
        finally: merger.close()


    def pdf_to_docx(self):
        if not self.exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            basename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f'{basename}.docx')
            id = uuid.uuid4().hex

            try:
                converter_obj = Converter(file_path)
                converter_obj.convert(output_path, start = 0, end = None)
                converter_obj.close() 

                print(f"Pdf coverted to Docx: {original_filename}")
                output_files.update({id: output_path})
            except Exception as e:
                print(f"Failed converting to docx {original_filename}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False, 
                'files': failed_files, 
                'output_files': output_files,
                'error': 'Failed to convert these pdf(s), please try again'
            }

        return {'status': True, 'output_files': output_files}

    def pdf_to_images(self, dpi = 200):
        if not self.exists: return self.return_d

        output_folder_dic = {}
        failed_files = []

        zoom = dpi / 72  # 72 is the default PDF DPI
        matrix = pymupdf.Matrix(zoom, zoom)

        for file_path, original_filename in self.Input_paths.items():
            try:
                pdf = pymupdf.open(file_path)

                basename = os.path.splitext(original_filename)[0]
                output_folder = os.path.join(self.output_folder, basename)
                os.makedirs(output_folder, exist_ok=True)

                for page_num, page in enumerate(pdf):
                    try:
                        pix = page.get_pixmap(matrix=matrix)
                        img_path = os.path.join(output_folder,f"{basename}_page{page_num + 1}.png")

                        pix.save(img_path)
                        print(f"{img_path}")
                    except Exception as e:
                        print(f"Error saving page {page_num + 1}: {e}")

                pdf.close()

                if not os.listdir(output_folder):
                    print(f"No pages were rendered for {basename} — all pages failed")
                    failed_files.append(original_filename)
                    shutil.rmtree(output_folder)
                    continue

                try:
                    shutil.make_archive(base_name = output_folder, format = 'zip', root_dir = output_folder)
                    shutil.rmtree(output_folder)

                    id  = uuid.uuid4().hex
                    output_folder_dic.update({id: f"{output_folder}.zip"})
                except Exception as e:
                    print(f"Failed converting folder to zip {basename}: {e}")
                    failed_files.append(original_filename)

            except Exception as e:
                print(f"Error while converting PDF {original_filename}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False, 
                'files': failed_files, 
                'output_files': output_folder_dic,
                'error': 'Failed to convert these pdf(s), please try again'
            }

        return {'status': True, 'output_files': output_folder_dic}

    def images_to_pdf(self, filename = None):
        if not self.exists: return self.return_d

        failed_images = []
        loaded_images = []

        if not filename: filename = f"images-to-pdf-{random.randint(100,1000)}.pdf"
        output_path = os.path.join(self.output_folder, filename)

        for img_path , original_filename in self.Input_paths.items():
            try:
                image = Image.open(img_path).convert("RGB")
                loaded_images.append(image)
                print(f"✅ Loaded: {os.path.basename(img_path)}")
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                failed_images.append(original_filename)

        if not loaded_images:
            print("No valid images to convert!")
            return {"status": False,"output_files": {}, 'error': 'No image were loaded, please try again'}

        if failed_images:
            return {
                "status": False,
                "files": failed_images,
                "output_files": {}, 
                'error': 'Failed to add these image(s), please try again'
            }

        try:
            if len(loaded_images) == 1: loaded_images[0].save(output_path)
            else: loaded_images[0].save(output_path, save_all = True, append_images = loaded_images[1:])

            print(f"\nPDF created: {filename} ({len(loaded_images)} images)")

            id = uuid.uuid4().hex
            return {'status': True, 'output_files': {id: output_path}}
        except Exception as e:
            print(f"Failed to convert images into PDF: {e}")

            return {
                "status": False,
                "output_files": {},
                "error": 'Failed to make a pdf, please try again',
            }


    def pdf_to_text(self):
        if not self.exists: return self.return_d

        output_files = {}
        failed_files = []

        for file_path, original_filename in self.Input_paths.items():
            filename = os.path.splitext(original_filename)[0]
            output_path = os.path.join(self.output_folder, f"{filename}-extracted-Text.txt")
            ocr_used = False
            lines = []

            try:
                pdf = pymupdf.open(file_path)

                for page in pdf:
                    text = page.get_text()

                    if not text.strip():
                        try:
                            ocr_page = page.get_textpage_ocr(
                                flags=0,
                                language="eng+urdu",   # add more langs e.g. "eng+urdu" if needed
                                dpi=300,          # higher = more accurate, slower
                                full=False        # False = only OCR if no text layer found
                            )
                            text = page.get_text(textpage=ocr_page)

                            if text.strip():ocr_used = True
                        except Exception as ocr_err:
                            print(f"OCR failed on a page in {file_path}: {ocr_err}")

                    if text.strip():
                        lines.append(text + '\n')

                pdf.close()

                if not lines:
                    failed_files.append(original_filename)
                    continue

                with open(output_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)

                id = uuid.uuid4().hex
                output_files.update({id: output_path})

                tag = " (OCR)" if ocr_used else ""
                print(f"Text extracted from {file_path}{tag}: saved to {output_path}")

            except Exception as e:
                print(f"Error extracting from {file_path}: {e}")
                failed_files.append(original_filename)

        if failed_files:
            return {
                'status': False, 
                'files': failed_files, 
                'output_files': output_files, 
                'error': 'Failed to extract text from these/this pdf(s)'
            }

        print(f"\nTotal pdf from which text extracted: {len(output_files)}")
        return {"status": True,"output_files": output_files,}

    def split_pdf(self):
        ...
