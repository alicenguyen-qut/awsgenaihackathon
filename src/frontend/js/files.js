async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (!files.length) return;
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        await fetch('/upload', { method: 'POST', body: formData });
    }
    
    await loadFiles();
    fileInput.value = '';
}

async function loadFiles() {
    const response = await fetch('/api/files');
    const data = await response.json();
    renderFileList(data.files || []);
}

function renderFileList(files) {
    const fileList = document.getElementById('fileList');
    if (!fileList) return;
    
    if (files.length === 0) {
        fileList.innerHTML = '<div style="padding: 12px; color: #718096; font-size: 13px;">No files uploaded</div>';
        return;
    }
    
    fileList.innerHTML = files.map(file => `
        <div class="file-item" onclick="viewFile('${file.id}')">
            <div class="file-icon">📄</div>
            <div class="file-name">${file.filename}</div>
            <button class="delete-file" onclick="event.stopPropagation(); deleteFile('${file.id}')">×</button>
        </div>
    `).join('');
}

async function viewFile(fileId) {
    const response = await fetch(`/api/files/${fileId}`);
    const data = await response.json();
    
    if (data.filename) {
        const modal = document.getElementById('fileModal');
        document.getElementById('fileModalTitle').textContent = data.filename;
        
        if (data.filename.endsWith('.txt') || data.filename.endsWith('.docx')) {
            document.getElementById('fileModalContent').textContent = data.content;
        } else {
            document.getElementById('fileModalContent').textContent = 'This file format cannot be displayed. Only .txt files are supported.';
        }
        
        modal.classList.remove('hidden');
    }
}

function closeFileModal() {
    document.getElementById('fileModal').classList.add('hidden');
}

async function deleteFile(fileId) {
    if (confirm('Delete this file?')) {
        await fetch(`/api/files/${fileId}`, { method: 'DELETE' });
        await loadFiles();
    }
}
