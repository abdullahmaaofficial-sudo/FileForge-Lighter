from flask import Flask,session,render_template,send_file,request,jsonify
from werkzeug.utils import secure_filename
from modules.pdf_tools import PDFTools
from modules.doc_tools import DocTools
from modules.web_tools import WebTools
from io import BytesIO
import zipfile
import secrets
import time
import shutil
import random
import uuid
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

UPLOAD_FOLDER = os.path.join('temp', 'uploads')
os.makedirs(UPLOAD_FOLDER ,exist_ok=True)

#I will handle file extensions in fronted as well

ALLOWED_EXTENSIONS = {
    'video': {'mp4', 'mkv', 'mov', 'avi', 'webm', 'flv', 'mpeg', 'mpg', '3gp', 'wmv', 'm4v', 'ogv'},
    'audio': {'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac', 'wma', 'opus', 'oga'},
    'document': {'pdf', 'docx', 'doc', 'txt', 'md', 'csv', 'json', 'jsonl'},
    'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
}

def allowed_file(filename, file_type=None):
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())
    
    all_extensions = set()
    for extensions in ALLOWED_EXTENSIONS.values():
        all_extensions.update(extensions)
    
    return ext in all_extensions

def Cleanp_old_Folders():
    Delete_after = 60 * 30

    for folder in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER,folder)
        try:
            if time.time() - os.path.getmtime(folder_path) >  Delete_after:
                shutil.rmtree(folder_path)
                print(f"Deleted: {folder_path}")
        except Exception as e:
            print(f"Cleanup error: {e}")


def get_user_folders():
    Cleanp_old_Folders()

    if 'user-id' not in session:
        session['user-id'] = secrets.token_hex(16)

    user_folder = os.path.join(UPLOAD_FOLDER,session['user-id'])
    input_folder = os.path.join(user_folder,'input')
    output_folder = os.path.join(user_folder,'output')

    os.makedirs(user_folder,exist_ok=True)
    os.makedirs(input_folder,exist_ok=True)
    os.makedirs(output_folder,exist_ok=True)

    session['input-folder'] = input_folder
    session['output-folder'] = output_folder
    
    return {
        'user-folder' : user_folder,
        'input-folder' : input_folder,
        'output-folder' : output_folder
    }

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('index.html')

@app.route('/upload', methods = ['POST'])
@app.route('/upload/<exception>', methods = ['POST'])
def upload_files(exception = None):
    accepted_files = {}
    rejected_files = []

    files = request.files.getlist('user-files')
    if not files: return jsonify({'status': False,'error': 'No file uploaded.'})

    for file in files:
        original_filename = secure_filename(file.filename)
        extension = os.path.splitext(original_filename)[1]

        if not allowed_file(original_filename):
            rejected_files.append({original_filename: extension})
            continue
            
        unique_filename = f"{uuid.uuid4().hex}{extension}"
    
        folders = get_user_folders()
        if exception == 'e':
            images_folder = os.path.join(folders['input-folder'], f"images-folder-{random.randint(1000,5000)}")
            os.makedirs(images_folder, exist_ok=True)
            file_path = os.path.join(images_folder,unique_filename)
        else: file_path = os.path.join(folders['input-folder'],unique_filename) 
        
        file.save(file_path)
        accepted_files.update({file_path:original_filename})

    if rejected_files:
        return jsonify({
        'status': False,
        'error': 'File(s) are not allowed.',
        'files': rejected_files,
        'files_map': accepted_files
        })

    return jsonify({'status': True,'files_map': accepted_files})

@app.route('/process/<tool_name>',methods = ["POST"])
def process_files(tool_name):
    ToProcessDic = request.get_json(silent = True)

    if not ToProcessDic or not isinstance(ToProcessDic, dict):
        return jsonify({'status': False,'error':'Invalid JSON'})

    if not 'input-folder' in session: 
        return jsonify({'status': False,'error': 'Session Expired, try to re-upload the file(s)'})
    
    files_map = ToProcessDic.get('files_map')
    needed_arg = ToProcessDic.get('needed_arg')
    output_folder = session['output-folder']

    if tool_name == 'combine_pdf':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder) 
        result = tool.combine_pdf()

    elif tool_name == 'images_to_pdf':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.images_to_pdf()
    
    elif tool_name == 'pdf_to_images':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.pdf_to_images()

    elif tool_name == 'pdf_to_docx':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.pdf_to_docx()

    elif tool_name == 'compress_pdf':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.compress_pdf()

    elif tool_name == 'rotate_pdf':
        tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.rotate_pdf(angle = needed_arg)

    # elif tool_name == 'pdf_to_text':
    #     tool = PDFTools(paths_dic = files_map,output_folder = output_folder)
    #     result = tool.pdf_to_text()

    # Document Tools:=
    # elif tool_name == 'docx_to_pdf':
    #     tool = DocTools(paths_dic = files_map,output_folder = output_folder)
    #     result = tool.docx_to_pdf()

    elif tool_name == 'text_to_pdf':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.text_to_pdf()

    elif tool_name == 'markdown_to_html':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.markdown_to_html()

    elif tool_name == 'json_to_csv':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.json_to_csv()

    elif tool_name == 'csv_to_json':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.csv_to_json()

    elif tool_name == 'csv_to_jsonl':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.csv_to_jsonl()

    elif tool_name == 'csv_to_exel':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.csv_to_excel()

    elif tool_name == 'excel_to_csv':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.excel_to_csv()

    elif tool_name == 'json_to_xml':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.json_to_xml()

    elif tool_name == 'xml_to_json':
        tool = DocTools(paths_dic = files_map,output_folder = output_folder)
        result = tool.xml_to_json()
    else: jsonify({'status': False, 'error': 'Wrong tool name'})

    session["output-files"] = result.get('output_files')
    return jsonify(result)

@app.route('/process/web/tools/<tool_name>', methods = ["POST"])
def process_webTools(tool_name):
    url_filename_map = request.get_json(silent = True)

    if not url_filename_map or not isinstance(url_filename_map, dict):
            return jsonify({'status': False,'error':'Invalid JSON'})

    folders = get_user_folders()
    output_folder = folders['output-folder']

    if tool_name == 'url_to_text':
        tool = WebTools(paths_dic = url_filename_map, output_folder = output_folder)
        result = tool.url_to_text()

    elif tool_name == 'extract_metadata':
        tool = WebTools(paths_dic = url_filename_map, output_folder = output_folder)
        result = tool.extract_metadata()

    elif tool_name == 'extract_links':
        tool = WebTools(paths_dic = url_filename_map, output_folder = output_folder)
        result = tool.extract_links()

    elif tool_name == 'generate_qr_code':
        tool = WebTools(paths_dic = url_filename_map, output_folder = output_folder)
        result = tool.generate_qr_code()

    elif tool_name == 'url_to_markdown':
        tool = WebTools(paths_dic = url_filename_map, output_folder = output_folder)
        result = tool.url_to_markdown()
    else: return jsonify({'status': False, 'error': 'Wrong tool name'})

    session["output-files"] = result.get('output_files', {})
    return jsonify(result)

@app.route('/check/file/<file_id>')
def checkFile_ForDownload(file_id):
    if not 'output-folder' in session or not 'output-files' in session:
        return jsonify({'status': False, 'error': 'session expired, try again'})
    
    output_files = session['output-files']

    if file_id not in output_files:
        return jsonify({'status': False, 'error': 'wrong id, File ID not found'})
    
    file_path = output_files[file_id]
        
    if not os.path.exists(file_path):
        return jsonify({'status': False, 'error': "Path does not exists, try again"})

    output_folder = os.path.abspath(session['output-folder'])
    abs_file_path = os.path.abspath(file_path)
    
    if not abs_file_path.startswith(output_folder):
        return jsonify({'status': False,'error': 'Invalid file access'})

    session['abs_file_path'] = abs_file_path
    return jsonify({'status': True})

@app.route('/download/file')
def download_file():
    if not 'abs_file_path' in session:
        return jsonify({'download': False, 'error': "File does not exists in session."})
    
    abs_file_path = session.get('abs_file_path')
    filename = os.path.basename(abs_file_path)

    return send_file(
        abs_file_path,
        as_attachment=True,
        download_name=filename,
    )

@app.route('/check/files/forZip')
def checkFiles_forZipDownload():
    if not 'output-files'in session or not 'output-folder' in session:
        return jsonify({'status': False, 'error': 'Session expired, try again'})
    
    files = session.get('output-files')
    if not files:
        return jsonify({'status': False,'error': 'No file(s) are provided, try again'})
    return jsonify({'status': True})

    
@app.route('/download/all/files')
def download_all_files():
    files = session['output-files']
    if not files:
        return jsonify({'status': False,'error': 'No file(s) provided, try again'})

    zip_in_memory = BytesIO()

    with zipfile.ZipFile(zip_in_memory, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files.values():
            if os.path.exists(file):
                zip_file.write(file, arcname=os.path.basename(file))

    zip_in_memory.seek(0) 

    return send_file(
        zip_in_memory,
        mimetype='application/zip',
        as_attachment=True,
        download_name='processed_files.zip'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)