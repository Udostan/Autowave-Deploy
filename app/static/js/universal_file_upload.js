/**
 * Universal File Upload Handler
 * Provides file upload functionality for all input boxes across the application
 */

class UniversalFileUpload {
    constructor() {
        this.uploadedFiles = new Map(); // Store files by context (page/component)
        this.init();
    }

    init() {
        // Initialize file upload handlers for all pages
        this.initTaskFileUpload();
        this.initContext7FileUpload();
        this.initResearchFileUpload();
        this.initHomeFileUpload();
        this.initChatFileUpload();
    }

    // Task/Prime Agent file upload
    initTaskFileUpload() {
        const uploadBtn = document.getElementById('taskFileUploadBtn');
        const fileInput = document.getElementById('taskFileInput');
        const filePreview = document.getElementById('taskFilePreview');

        if (uploadBtn && fileInput && filePreview) {
            this.setupFileUpload('task', uploadBtn, fileInput, filePreview);
        }
    }

    // Context 7 Tools file upload
    initContext7FileUpload() {
        const uploadBtn = document.getElementById('context7FileUploadBtn');
        const fileInput = document.getElementById('context7FileInput');
        const filePreview = document.getElementById('context7FilePreview');

        if (uploadBtn && fileInput && filePreview) {
            this.setupFileUpload('context7', uploadBtn, fileInput, filePreview);
        }
    }

    // Research Lab file upload
    initResearchFileUpload() {
        const uploadBtn = document.getElementById('researchFileUploadBtn');
        const fileInput = document.getElementById('researchFileInput');
        const filePreview = document.getElementById('researchFilePreview');

        if (uploadBtn && fileInput && filePreview) {
            this.setupFileUpload('research', uploadBtn, fileInput, filePreview);
        }
    }

    // Home page file upload
    initHomeFileUpload() {
        const uploadBtn = document.getElementById('homeFileUploadBtn');
        const fileInput = document.getElementById('homeFileInput');
        const filePreview = document.getElementById('homeFilePreview');

        if (uploadBtn && fileInput && filePreview) {
            this.setupFileUpload('home', uploadBtn, fileInput, filePreview);
        }
    }

    // AutoWave Chat file upload
    initChatFileUpload() {
        const uploadBtn = document.getElementById('chatFileUploadBtn');
        const fileInput = document.getElementById('chatFileInput');
        const filePreview = document.getElementById('chatFilePreview');

        if (uploadBtn && fileInput && filePreview) {
            this.setupFileUpload('chat', uploadBtn, fileInput, filePreview);
        }
    }

    setupFileUpload(context, uploadBtn, fileInput, filePreview) {
        // Initialize file storage for this context
        if (!this.uploadedFiles.has(context)) {
            this.uploadedFiles.set(context, []);
        }

        // Upload button click handler
        uploadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });

        // File input change handler
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(context, e.target.files, filePreview);
        });

        // Drag and drop support
        const inputContainer = uploadBtn.closest('.relative') || uploadBtn.closest('.input-container') || uploadBtn.closest('form');
        if (inputContainer) {
            this.setupDragAndDrop(context, inputContainer, filePreview);
        }
    }

    handleFileSelection(context, files, filePreview) {
        const contextFiles = this.uploadedFiles.get(context);

        for (let file of files) {
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                continue;
            }

            const fileData = {
                file: file,
                name: file.name,
                type: file.type,
                size: file.size,
                id: Date.now() + Math.random(),
                content: null
            };

            contextFiles.push(fileData);

            // Read file content for text files and images
            if (this.isReadableFile(file)) {
                this.readFileContent(fileData);
            }
        }

        this.updateFilePreview(context, filePreview);
    }

    isReadableFile(file) {
        return file.type.startsWith('text/') || 
               file.type.startsWith('image/') ||
               file.name.endsWith('.py') || 
               file.name.endsWith('.js') ||
               file.name.endsWith('.html') || 
               file.name.endsWith('.css') ||
               file.name.endsWith('.json') || 
               file.name.endsWith('.md') ||
               file.name.endsWith('.txt');
    }

    readFileContent(fileData) {
        const reader = new FileReader();
        
        if (fileData.type.startsWith('image/')) {
            reader.onload = (e) => {
                fileData.content = e.target.result; // Base64 data URL
                fileData.isImage = true;
            };
            reader.readAsDataURL(fileData.file);
        } else {
            reader.onload = (e) => {
                fileData.content = e.target.result; // Text content
                fileData.isText = true;
            };
            reader.readAsText(fileData.file);
        }
    }

    updateFilePreview(context, filePreview) {
        const contextFiles = this.uploadedFiles.get(context);
        
        if (contextFiles.length === 0) {
            filePreview.style.display = 'none';
            return;
        }

        filePreview.style.display = 'block';
        filePreview.innerHTML = '';

        contextFiles.forEach((fileData, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';

            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';

            // Add image preview or file icon
            if (fileData.isImage && fileData.content) {
                const img = document.createElement('img');
                img.src = fileData.content;
                img.className = 'file-image-preview';
                img.alt = fileData.name;
                fileInfo.appendChild(img);
            } else {
                const icon = document.createElement('div');
                icon.className = 'file-icon';
                icon.innerHTML = this.getFileIcon(fileData.type);
                fileInfo.appendChild(icon);
            }

            const fileDetails = document.createElement('div');
            fileDetails.className = 'file-details';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = fileData.name;

            const fileSize = document.createElement('div');
            fileSize.className = 'file-size';
            fileSize.textContent = this.formatFileSize(fileData.size);

            fileDetails.appendChild(fileName);
            fileDetails.appendChild(fileSize);
            fileInfo.appendChild(fileDetails);

            const removeBtn = document.createElement('button');
            removeBtn.className = 'file-remove';
            removeBtn.innerHTML = '×';
            removeBtn.title = 'Remove file';
            removeBtn.addEventListener('click', () => {
                this.removeFile(context, index, filePreview);
            });

            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            filePreview.appendChild(fileItem);
        });
    }

    removeFile(context, index, filePreview) {
        const contextFiles = this.uploadedFiles.get(context);
        contextFiles.splice(index, 1);
        this.updateFilePreview(context, filePreview);
    }

    getFileIcon(fileType) {
        if (fileType.startsWith('image/')) {
            return '🖼️';
        } else if (fileType.includes('pdf')) {
            return '📄';
        } else if (fileType.includes('text') || fileType.includes('json')) {
            return '📝';
        } else if (fileType.includes('python') || fileType.includes('javascript')) {
            return '💻';
        } else {
            return '📎';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setupDragAndDrop(context, container, filePreview) {
        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            container.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
        });

        container.addEventListener('dragleave', (e) => {
            e.preventDefault();
            container.style.backgroundColor = '';
        });

        container.addEventListener('drop', (e) => {
            e.preventDefault();
            container.style.backgroundColor = '';
            
            const files = e.dataTransfer.files;
            this.handleFileSelection(context, files, filePreview);
        });
    }

    // Public method to get files for a specific context
    getFiles(context) {
        return this.uploadedFiles.get(context) || [];
    }

    // Public method to clear files for a specific context
    clearFiles(context) {
        this.uploadedFiles.set(context, []);
        const filePreview = document.getElementById(`${context}FilePreview`);
        if (filePreview) {
            filePreview.style.display = 'none';
            filePreview.innerHTML = '';
        }
    }

    // Public method to get file content as text for AI processing
    getFileContentForAI(context) {
        const files = this.getFiles(context);
        let content = '';

        files.forEach(fileData => {
            if (fileData.isText && fileData.content) {
                content += `\n\n--- File: ${fileData.name} ---\n${fileData.content}\n`;
            } else if (fileData.isImage && fileData.content) {
                content += `\n\n--- Image: ${fileData.name} (${fileData.type}) ---\n${fileData.content}\n`;
            } else if (fileData.isImage) {
                content += `\n\n--- Image: ${fileData.name} (${fileData.type}) ---\n[Image uploaded - can be analyzed by AI]\n`;
            }
        });

        return content;
    }
}

// Initialize the universal file upload system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.universalFileUpload = new UniversalFileUpload();
    console.log('Universal File Upload system initialized');
});
