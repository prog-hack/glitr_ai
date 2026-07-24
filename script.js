// Configuration
const API_BASE_URL = 'https://glitr-ai.onrender.com'; 

// DOM Elements
const generateForm = document.getElementById('generate-form');
const lookupForm = document.getElementById('lookup-form');
const resultSection = document.getElementById('result-section');
const errorDisplay = document.getElementById('error-message');

// Result DOM Elements
const jobIdDisplay = document.getElementById('job-id-display');
const jobStatus = document.getElementById('job-status');
const jobPrompt = document.getElementById('job-prompt');
const jobImage = document.getElementById('job-image');
const generateBtn = document.getElementById('generate-btn');

// Helper function to show errors
function showError(message) {
    errorDisplay.textContent = message;
    errorDisplay.style.display = 'block';
    resultSection.style.display = 'none';
}

// Helper function to display job data
function displayJobData(jobData) {
    errorDisplay.style.display = 'none';
    resultSection.style.display = 'block';
    
    jobIdDisplay.textContent = `(Job #${jobData.job_id || jobData.id})`;
    jobStatus.textContent = jobData.status.toUpperCase();
    jobPrompt.textContent = jobData.prompt || "No prompt generated yet.";
    
    if (jobData.result_url) {
        jobImage.src = jobData.result_url;
        jobImage.style.display = 'block';
    } else {
        jobImage.style.display = 'none';
    }
}

// Handle Generation Form Submission
generateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    generateBtn.textContent = "Generating...";
    generateBtn.disabled = true;

    const formData = new FormData();
    formData.append('product_name', document.getElementById('product-name').value);
    formData.append('product_description', document.getElementById('product-description').value);
    formData.append('product_image', document.getElementById('product-image').files[0]);

    try {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Failed to generate content.");
        }
        
        const data = await response.json();
        displayJobData(data);

    } catch (error) {
        showError(`Error: ${error.message}`);
        console.error(error);
    } finally {
        generateBtn.textContent = "Generate Content";
        generateBtn.disabled = false;
    }
});

// Handle Job Lookup Form Submission
lookupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const jobId = document.getElementById('job-id-input').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
        
        if (response.status === 404) {
            showError("Job not found.");
            return;
        }
        if (!response.ok) throw new Error("Failed to fetch job.");
        
        const data = await response.json();
        displayJobData(data);

    } catch (error) {
        showError("Error connecting to the server.");
        console.error(error);
    }
});