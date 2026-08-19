from flask import Flask,session,render_template,send_file,request,jsonify
from modules.pdf_doc_tools import pdf_tools,document_tools
from werkzeug.utils import secure_filename
from io import BytesIO
import zipfile
import secrets
import shutil
import uuid
import os

app = Flask(__name__)
app.secret_key = 'secret-key-for-now'

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

def get_user_folders():

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
def index_file():
    return render_template('index.html')

@app.route('/upload', methods = ['POST'])
def upload_files():
    uploaded_files = {}
    rejected_files = []

    files = request.files.getlist('user-files')

    if not files:
        return jsonify({
            'status': 'failed',
            'error': 'No file uploaded.'
        })

    for file in files:
        original_filename = secure_filename(file.filename)
        extension = os.path.splitext(original_filename)[1]

        if not allowed_file(original_filename):
            rejected_files.append({'file': original_filename, 'ext': extension})
            continue
            
        unique_filename = f"{uuid.uuid4().hex}{extension}"
    
        folders = get_user_folders()
        file_path = os.path.join(folders['input-folder'],unique_filename)

        file.save(file_path)
        uploaded_files.update({unique_filename:original_filename})

    if not uploaded_files:
        return jsonify({
        'status': 'failed',
        'error': 'Files are not allowed.',
        'invalid_files': rejected_files
        })

    return jsonify({
        'status': 'success',
        'files_mapping': uploaded_files,
        'invalid_files': rejected_files
        })

@app.route('/process/<tool_name>',methods = ["POST"])
def process_files(tool_name):
    notExists_files = []
    valid_files = {}

    ToProcessDic = request.get_json(silent=True)

    if not ToProcessDic or not isinstance(ToProcessDic, dict):
        return jsonify({'status':'failed','error':'Invalid JSON'})

    if not 'input-folder' in session: return jsonify({'status':'failed','error': 'Session Expired'})
    
    files = ToProcessDic.get('files_mapping')
    needed_arg = ToProcessDic.get('needed_arg')


    for unique_filename ,original_filename in files.items():
        path_Inserver = os.path.join(session['input-folder'],unique_filename)

        if not os.path.exists(path_Inserver):
            notExists_files.append(original_filename)
            continue

        valid_files.update({path_Inserver:original_filename})
        
    if not valid_files: return jsonify({
        'status':'failed',
        'error': ['No file exists in server,Try to upload files again!'],
        'files': notExists_files
        })
    
    output_folder = session['output-folder']

    # PDF Tools:=
    if tool_name == 'combine_pdf':
        tool = pdf_tools(paths = valid_files,output_folder = output_folder) 
        results = tool.merged_pdf()

    elif tool_name == 'images_to_pdf':
        tool = pdf_tools(paths = valid_files,output_folder = output_folder)
        results = tool.images_to_pdf()
    
    elif tool_name == 'pdf_to_images':
        tool = pdf_tools(paths = valid_files,output_folder = output_folder)
        results = tool.pdf_to_images()

    elif tool_name == 'pdf_to_docx':
        tool = pdf_tools(paths = valid_files,output_folder = output_folder)
        results = tool.pdf_to_docx()

    elif tool_name == 'pdf_to_text':
        tool = pdf_tools(paths = valid_files,output_folder = output_folder)
        results = tool.PDF_TO_TXT()

    # Document Tools:=
    elif tool_name == 'docx_to_pdf':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.docx_to_pdf()

    elif tool_name == 'text_to_pdf':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.TXT_to_PDF()

    elif tool_name == 'markdown_to_html':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.markdown_to_html()

    elif tool_name == 'json_to_csv':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.JSON_to_CSV()

    elif tool_name == 'csv_to_json':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.CSV_to_JSON()

    elif tool_name == 'csv_to_jsonl':
        tool = document_tools(paths = valid_files,output_folder = output_folder)
        results = tool.CSV_to_JSONL()
    
    else: 
        jsonify({'status': 'failed', 'error': ['Tool does not exits']})

    #I will add more tool


    session['indicator'] = results.get('indicator')
    session["processed-files"] = results['successful_files']
    return jsonify(results)

@app.route('/download-file/<file_id>')
def download_file(file_id):
    if not 'output-folder' in session or not 'processed-files' in session:
        return jsonify({'status': 'failed', 'error': 'session expired.'}), 401

    processed_files = session['processed-files']

    if file_id not in processed_files:
        return jsonify({'status': 'failed', 'error': 'File ID not found.'}), 404

    file_path = processed_files[file_id]
    
    if not os.path.exists(file_path):
        return jsonify({'status': 'failed',
                        'file': {'id':file_id,'path':file_path}, 
                        'error': "Path does not exist."}), 404

    output_folder = os.path.abspath(session['output-folder'])
    file_path_abs = os.path.abspath(file_path)
    
    if not file_path_abs.startswith(output_folder):
        return jsonify({'error': 'Invalid file access'}), 403

    filename = os.path.basename(file_path)

    return send_file(
        file_path_abs,
        as_attachment=True,
        download_name=filename,
    )
    
# Working but still need some changes.
@app.route('/download-all')
def download_all_files():
    if not 'processed-files'in session or not 'output-folder' in session:
        return jsonify({'status':'failed','error': 'Session expired'})

    if session.get('indicator') == "tool-exception":
        folder_dic = session.get('processed-files')

        for folder_id , folder in folder_dic.items():
            if not os.path.exists(folder):
                print(f"Folder doesn't exist: {folder}")
                continue

            files = os.listdir(folder)

            if not files:
                return jsonify({'status':'failed','error': 'No files provided'})

            zip_in_memory = BytesIO()

            with zipfile.ZipFile(zip_in_memory, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename in files:
                    file = os.path.join(folder,filename)
                    if os.path.exists(file):
                        print(f"img-file: {file}")
                        zip_file.write(file, arcname=os.path.basename(filename))

            zip_in_memory.seek(0)

            # shutil.rmtree(folder)

            return send_file(
                zip_in_memory,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'{folder}.zip'
            )

    
    files = session['processed-files']
    
    if not files:
        return jsonify({'status':'failed','error': 'No files provided'})

    zip_in_memory = BytesIO()

    with zipfile.ZipFile(zip_in_memory, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_id , file in files.items():
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