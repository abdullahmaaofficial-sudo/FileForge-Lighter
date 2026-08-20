const InputTag = document.getElementById('input-tag');
const ShowFilesbox = document.getElementById('selected-files-box');
const handleToolSection = document.getElementById('handle-tool-section');
const handleToolName = document.getElementById('handle-tool-name');
const DragDropArea = document.getElementById('drag-drop-area');
const closebtn = document.getElementById('close-btn');
const ProcessNeedsBox = document.getElementById('process-needs-box');
const DownloadSection = document.getElementById('download-section');
const DisplayFilenameBox = document.getElementById('filename-box');
const DownloadAllButton = document.getElementById('download-all-btn')
const main = document.querySelector('main');
const header = document.querySelector('header');


const TOOL_CONFIG = {
    "Video to Audio": {
        route: "video_to_audio",
        optionType: "extension"
    },
    "Change Video Format": {
        route: "change_video_format",
        optionType: "video-extension"
    },
    "Change Video Resolution": {
        route: "change_video_resolution",
        optionType: "resolution"
    },
    "Combine Video Clips": {
        route: "combine_video_clips",
        optionType: "resolution"
    },

    // Audio Tools
    "Change Audio Format": {
        route: "change_audio_format",
        optionType: "extension"
    },
    "Change Audio Volume": {
        route: "change_audio_volume",
        optionType: "factor"
    },
    "Combine Audio": {
        route: "combine_audio",
        optionType: "factor"
    },

    // PDF Tools
    "Combine PDFs": {
        route:"combine_pdf",
        optionType: null,
    },
    "Images to PDF": {
        route:"images_to_pdf",
        optionType: null,
    },
    "Pdf to Images": {
        route:"pdf_to_images",
        optionType: null,
    },
    "Pdf to Docx": {
        route:"pdf_to_docx",
        optionType: null,
    },
    "Pdf to Text": {
        route:"pdf_to_text",
        optionType: null,
    },

    // Document Tools
    "Docx to PDF": {
        route:"docx_to_pdf",
        optionType: null,
    },
    "Text to PDF": {
        route:"text_to_pdf",
        optionType: null,
    },
    "Markdown to HTML": {
        route:"markdown_to_html",
        optionType: null,
    },
    "JSON to CSV": {
        route:"json_to_csv",
        optionType: null,
    },
    "CSV to JSON": {
        route:"csv_to_json",
        optionType: null,
    },
    "CSV to JSONL": {
        route:"csv_to_jsonl",
        optionType: null,
    },
};

const SpecificTools = [
    "Video to Audio",
    "Change Video Format",
    "Change Video Resolution",
    "Change Audio Format",
    "Change Audio Volume"
]

const ErrorBox = document.createElement('div');
ErrorBox.className = 'error-box';
ErrorBox.innerHTML = "";

let formData = new FormData();
let filesArray = [];
let toolToProcess = "";
let ProcessedFiles;

main.addEventListener('click', (event) => {
    const ClickedTool = event.target.closest('.open-tool-btn');

    if (ClickedTool){
        const toolname = ClickedTool.dataset.toolname;
        toolToProcess = toolname;

        header.style.display = 'none';
        main.style.position = 'fixed';
        handleToolName.textContent = toolname;
        handleToolSection.style.display = 'flex';

        if (SpecificTools.includes(toolname)){
            handleExtraElements(TOOL_CONFIG[toolname].optionType);
        }
        else{
            ProcessNeedsBox.innerHTML = `<p>No extra things need.</p>`;
        }

    };
})

closebtn.onclick = function(){
    handleToolSection.style.display = 'none';
    header.style.display = 'flex';
    main.style.position = 'relative';
};

function handleExtraElements(optiontype){
    ProcessNeedsBox.innerHTML = '';

    if (optiontype === 'extension'){
        ProcessNeedsBox.innerHTML = `
            <h1 id="selection-heading">Audio Extension</h1>
            <div class="options-box" id="option-box">
                <input type="radio" name="extension" id="ext-mp3" value="mp3">
                <label for="ext-mp3">mp3</label>
                <input type="radio" name="extension" id="ext-wav" value="wav">
                <label for="ext-wav">wav</label>
                <input type="radio" name="extension" id="ext-aac" value="aac">
                <label for="ext-aac">aac</label>
                <input type="radio" name="extension" id="ext-m4a" value="m4a">
                <label for="ext-m4a">m4a</label>
                <input type="radio" name="extension" id="ext-ogg" value="ogg">
                <label for="ext-ogg">ogg</label>
                <input type="radio" name="extension" id="ext-flac" value="flac">
                <label for="ext-flac">flac</label>
            </div>
        `;
    }

    else if (optiontype === 'video-extension'){
        ProcessNeedsBox.innerHTML = `
        <h1 id="selection-heading">Video Extension</h1>
        <div class="options-box" id="option-box">
                <input type="radio" name="extension" id="ext-mp4" value="mp4">
                <label for="ext-mp4">mp4</label>
                <input type="radio" name="extension" id="ext-avi" value="avi">
                <label for="ext-avi">avi</label>
                <input type="radio" name="extension" id="ext-webm" value="webm">
                <label for="ext-webm">webm</label>
                <input type="radio" name="extension" id="ext-mov" value="mov">
                <label for="ext-mov">mov</label>
                <input type="radio" name="extension" id="ext-mkv" value="mkv">
                <label for="ext-mkv">mkv</label>
            </div>
        `;
    }

    else if (optiontype === 'resolution'){
        ProcessNeedsBox.innerHTML = `
        <h1 id="selection-heading">Resolution</h1>
        <div class="options-box" id="option-box">
                <input type="radio" name="resolution" id="res-480p" value="480p">
                <label for="res-480p">480p</label>
                <input type="radio" name="resolution" id="res-720p" value="720p">
                <label for="res-720p">720p</label>
                <input type="radio" name="resolution" id="res-1080p" value="1080p">
                <label for="res-1080p">1080p</label>
                <input type="radio" name="resolution" id="res-4k" value="4k">
                <label for="res-4k">4k</label>
            </div>
        `;
    }

    else if (optiontype === 'factor'){
        ProcessNeedsBox.innerHTML = `
        <h1 id="selection-heading">Volume Amount</h1>
        <div class="options-box" id="option-box">
                <input type="radio" name="factor" id="dpi-0.5" value="0.5">
                <label for="dpi-0.5">Half - 0.5</label>
                <input type="radio" name="factor" id="dpi-1" value="1">
                <label for="dpi-1">Original - 1</label>
                <input type="radio" name="factor" id="dpi-2" value="2">
                <label for="dpi-2">Double - 2</label>
                <input type="radio" name="factor" id="dpi-3" value="3">
                <label for="dpi-3">Triple - 3</label>
                <input type="radio" name="factor" id="dpi-4" value="4">
                <label for="dpi-4">Quadruple - 4</label>
                <input type="radio" name="factor" id="dpi-5" value="5">
                <label for="dpi-5">Quintuple - 5</label>
            </div>
        `;
    }

    else {
        console.error(`Error: Tool does not exits: ${tool}`)
    }
    
};

function GetSelectedRadio(){
    const SelectedRadio = ProcessNeedsBox.querySelector("input[type='radio']:checked")
    return SelectedRadio ? SelectedRadio.value: null;
};


InputTag.addEventListener( 'change', () => {
    const SelectedFiles = InputTag.files;
    handleFiles(SelectedFiles);
});

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
    }, false);
});

DragDropArea.addEventListener('dragover', (e) => {
    e.preventDefault()
    DragDropArea.classList.add('highlight');
});

DragDropArea.addEventListener('drop', (e) => {
    e.preventDefault()
    DragDropArea.classList.remove('highlight')
    const files = e.dataTransfer.files;
    handleFiles(files);
});

DragDropArea.addEventListener('dragleave', () => {
    DragDropArea.classList.remove('highlight')
})

DragDropArea.addEventListener('click', () =>{
    InputTag.click();
});


ShowFilesbox.addEventListener('click', (e) => {
    const clickedbutton = e.target.closest('.del-btn');
    
    if (clickedbutton){
        const fileNum = parseInt(clickedbutton.dataset.fileNum);
        
        removefile(fileNum);
    };
});

function handleFiles(files){
    for (let i = 0; i < files.length; i++){
        filesArray.push(files[i]);     
    };

    formData = new FormData();
    filesArray.forEach(file => {
        formData.append('user-files', file);
    });

    ShowFilesbox.innerHTML = ``;
    filesArray.forEach((file, ind) => {
        displayFiles(file,ind);
    })
};

function removefile(index){
    filesArray.splice(index,1);

    formData = new FormData();
    filesArray.forEach(file =>{
        formData.append('user-files', file);
    })

    ShowFilesbox.innerHTML = ``;
    filesArray.forEach((file, i) => {
        displayFiles(file,i);
    }) 
};

function displayFiles(file , index){
    const filebox = document.createElement('div');
    filebox.className = 'file-box';

    filebox.innerHTML = `
            <p class="file-name">${file.name}</p>
            <div class = "size-btn-box"> 
                <span class="file-size">${(file.size / 1024).toFixed(0)} KB</span>
                <span class="del-btn" id="del" data-fileNum="${index}")">+</span>
            </div>
    `
    ShowFilesbox.appendChild(filebox);
};

document.getElementById('proceed-btn').onclick = () => {
    if (SpecificTools.includes(toolToProcess)){
        if(ProcessNeedsBox.querySelector("input[type='radio']:checked")){
            SendAndProcessFiles();
        }else{
            ErrorBox.innerHTML = `<p id="error-message">Please Select an option to process.</p>`;
            ProcessNeedsBox.appendChild(ErrorBox)
        }
    }else{
        SendAndProcessFiles();
    }
};


async function SendAndProcessFiles(){
    
    const response = await fetch('/upload', {method: 'POST',body: formData})
    const data = await response.json();
   
    if (data.status === 'success'){
        const required_data = {
            'files_mapping': data.files_mapping, 
            'needed_arg': GetSelectedRadio()
        };     
        console.log(required_data)
        ProcessFiles(required_data)         
    }else {
        console.error(data.error);
        ErrorBox.innerHTML = `<p id="error-message">${data.error}</p>`;
        ProcessNeedsBox.appendChild(ErrorBox);
    }
}

async function ProcessFiles(req_data) {
    console.log('down',req_data)
    const response = await fetch(`/process/${TOOL_CONFIG[toolToProcess].route}`,{
                method: 'POST',
                headers:{
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(req_data) 
        })

    const process_data = await response.json();

    if (process_data.status === 'success'){
            console.log(process_data);      
            handleDownload(process_data.successful_files)
            ProcessedFiles = process_data.successful_files;
    }else{
        console.error(process_data.error);
        ErrorBox.innerHTML = `<p id="error-message">${process_data.error}</p>`;
        ProcessNeedsBox.appendChild(ErrorBox);}   
}

function handleDownload(data){
    DownloadSection.style.display = 'flex';
    handleToolSection.style.display = 'none';

    if (toolToProcess === "Images to PDF"){DownloadAllButton.style.display = 'none'};

    let i = 1
    for (const key of Object.keys(data)){
        const filename = document.createElement("div");
        filename.className = "filename";

        filename.innerHTML = `
            <span id="name${i}">${data[key].split(/[/\\]/).pop()}</span>
            <button class="download-button" data-id=${key}>Download</button>
        `;
            
        DisplayFilenameBox.appendChild(filename);
        i++
    };
};

document.getElementById('go-back-btn').onclick = function(){
    DisplayFilenameBox.innerHTML = '';
    DownloadSection.style.display = 'none';
    handleToolSection.style.display = 'flex';
};

DownloadSection.addEventListener('click', (e) =>{
    const ClickedBtn = e.target.closest('.download-button');

    if (ClickedBtn){
        const id = ClickedBtn.dataset.id;

        if (toolToProcess === "Pdf to Images"){
            CheckFilesForZipDownload();
        }else{
            CheckFileForDownload(id);
        }
    };

})

DownloadAllButton.addEventListener('click', () => {
    CheckFilesForZipDownload();
});

async function CheckFileForDownload(id) {
    try{
        const response = await fetch(`/check/file/${id}`);
        const result = await response.json();

        if (response.ok){  
            if (result.status) DownloadTheFile();
            else console.log(result.error)

        }else console.log('Failed to ready a file for download.')
    }catch(e){console.error(e)}
}

function DownloadTheFile() {
    try {
        const anchor_tag = document.createElement('a');
        anchor_tag.href = '/download/file';
        anchor_tag.click()
    } catch(e){console.error(e)}
}

async function CheckFilesForZipDownload() {
    try{
        const response = await fetch(`/check/files/forZip`);
        const result = await response.json();

        if (response.ok){  
            if (result.status) DownloadFilesAsZip();
            else console.log(result.error)

        }else console.log('Failed to ready the files for download.')
    }catch(e){console.error(e)}
}

function DownloadFilesAsZip() {
    try {
        const anchor_tag = document.createElement('a');
        anchor_tag.href = '/download/all/files';
        anchor_tag.click()
    } catch(e){console.error(e)}
}