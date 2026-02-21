// Data upload management

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (!files.length) return;
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (!data.success) {
            showAlert(data.error || `Failed to upload ${file.name}`, 'error');
            return;
        }
    }
    
    showAlert(`${files.length} file(s) uploaded successfully!`, 'success');
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
        const contentDiv = document.getElementById('fileModalContent');
        
        if (data.filename.endsWith('.pdf')) {
            // For PDF, use iframe viewer with the actual file path
            const userId = data.filepath.split('/').pop().split('_')[0];
            const fileUrl = `/uploads/${userId}_${data.filename}`;
            contentDiv.innerHTML = `<iframe src="${fileUrl}" style="width: 100%; height: 60vh; border: none; border-radius: 8px;"></iframe>`;
        } else if (data.filename.endsWith('.docx')) {
            // For DOCX, render with preserved formatting
            contentDiv.innerHTML = `<div style="white-space: pre-wrap; font-family: 'Georgia', serif; font-size: 14px; line-height: 1.8; color: #2d3748;">${escapeHtml(data.content)}</div>`;
        } else if (data.filename.endsWith('.txt')) {
            // For TXT, use monospace with better styling
            contentDiv.innerHTML = `<div style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.6; color: #2d3748;">${escapeHtml(data.content)}</div>`;
        } else {
            contentDiv.textContent = 'This file format cannot be displayed.';
        }
        
        modal.classList.remove('hidden');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
