// PDF Q&A Bot - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const pdfFileInput = document.getElementById('pdf-file');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadStatus = document.getElementById('upload-status');
    const questionsSection = document.getElementById('questions-section');
    const pdfInfoDisplay = document.getElementById('pdf-info');
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const loadingIndicator = document.getElementById('loading');
    const answerContainer = document.getElementById('answer-container');
    const answerContent = document.getElementById('answer-content');
    const sourcesContainer = document.getElementById('sources-container');

    // Store the PDF ID after upload
    let currentPdfId = null;
    let currentFilename = null;

    // Update file name display when file is selected
    pdfFileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const fileName = this.files[0].name;
            fileNameDisplay.innerHTML = `<i class="far fa-file-pdf text-red-500 mr-2"></i> ${fileName}`;
            fileNameDisplay.classList.remove('text-gray-500');
            fileNameDisplay.classList.add('text-gray-800');
        } else {
            fileNameDisplay.innerHTML = `<i class="fas fa-upload mr-2"></i> Drag & Drop or Click to browse`;
            fileNameDisplay.classList.remove('text-gray-800');
            fileNameDisplay.classList.add('text-gray-500');
        }
    });

    // Handle PDF upload
    uploadForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const fileInput = document.getElementById('pdf-file');
        const file = fileInput.files[0];

        if (!file) {
            showStatus('Please select a PDF file first.', 'error');
            return;
        }

        if (!file.type.includes('pdf')) {
            showStatus('Please upload a valid PDF file.', 'error');
            return;
        }

        // Show loading state
        showStatus('Uploading and processing PDF...', 'loading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }

            const data = await response.json();

            // Store the PDF ID for later use
            currentPdfId = data.pdf_id;
            currentFilename = data.filename;

            // Show success message
            showStatus(`PDF uploaded successfully! ${data.num_chunks} chunks extracted from ${data.num_pages} pages.`, 'success');

            // Show questions section
            showQuestionsSection(data);

        } catch (error) {
            console.error('Error uploading PDF:', error);
            showStatus(`Error uploading PDF: ${error.message}`, 'error');
        }
    });

    // Handle question submission
    questionForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const question = questionInput.value.trim();

        if (!question) {
            showAlert('Please enter a question.');
            return;
        }

        if (!currentPdfId) {
            showAlert('Please upload a PDF first.');
            return;
        }

        // Show loading state
        loadingIndicator.classList.remove('hidden');
        answerContainer.classList.add('hidden');

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    pdf_id: currentPdfId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }

            const data = await response.json();

            // Display the answer
            displayAnswer(data);

        } catch (error) {
            console.error('Error asking question:', error);
            loadingIndicator.classList.add('hidden');
            showAlert(`Error: ${error.message}`);
        }
    });

    // Function to show status messages
    function showStatus(message, type = 'info') {
        uploadStatus.innerHTML = message;
        uploadStatus.classList.remove('hidden', 'status-success', 'status-error');

        if (type === 'success') {
            uploadStatus.classList.add('status-success');
        } else if (type === 'error') {
            uploadStatus.classList.add('status-error');
        } else if (type === 'loading') {
            uploadStatus.innerHTML = `
                <div class="flex items-center">
                    <div class="loader mr-3" style="width: 20px; height: 20px;"></div>
                    <span>${message}</span>
                </div>
            `;
        }

        uploadStatus.classList.remove('hidden');
    }

    // Function to show the questions section
    function showQuestionsSection(data) {
        questionsSection.classList.remove('hidden');

        // Update PDF info
        pdfInfoDisplay.innerHTML = `
            <span class="font-medium">Current PDF:</span>
            <span class="tag">${data.filename}</span>
            <span class="text-gray-500">${data.num_pages} pages · ${data.num_chunks} chunks · ID: ${data.pdf_id}</span>
        `;

        // Scroll to questions section
        questionsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Function to display the answer
    function displayAnswer(data) {
        loadingIndicator.classList.add('hidden');
        answerContainer.classList.remove('hidden');

        // Display the answer content
        answerContent.innerHTML = formatText(data.answer);

        // Clear previous sources
        sourcesContainer.innerHTML = '';

        // Add source citations
        if (data.source_chunks && data.source_chunks.length > 0) {
            data.source_chunks.forEach(source => {
                const sourceElement = document.createElement('div');
                sourceElement.className = 'source-citation';
                sourceElement.innerHTML = `
                    <div class="source-page">Page ${source.page_number}</div>
                    <div class="source-text">${formatText(source.text)}</div>
                    <div class="source-score">
                        <i class="fas fa-star text-yellow-500 mr-1"></i>
                        Relevance: ${(source.score * 100).toFixed(2)}%
                    </div>
                `;
                sourcesContainer.appendChild(sourceElement);
            });
        } else {
            sourcesContainer.innerHTML = '<p class="text-gray-500">No source chunks available</p>';
        }

        // Scroll to answer
        answerContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Function to format text with simple markdown-like features
    function formatText(text) {
        if (!text) return '';

        // Replace **bold** with <strong>
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Replace *italic* with <em>
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Replace newlines with <br>
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    // Simple alert function
    function showAlert(message) {
        alert(message);
    }
});