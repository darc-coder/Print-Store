// Checkout page functionality
let copies = 1;

function changeCopies(delta) {
    copies = Math.max(1, Math.min(99, copies + delta));
    document.getElementById('copiesValue').textContent = copies;
    document.getElementById('copiesInput').value = copies;
    
    // Get base values from data attributes
    const form = document.getElementById('checkoutForm');
    const baseCost = parseFloat(form.dataset.baseCost);
    const basePages = parseInt(form.dataset.basePages);
    
    // Update totals
    const totalPages = basePages * copies;
    const totalCost = baseCost * copies;
    
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('totalCost').textContent = totalCost.toFixed(0);
    
    // Update button states
    document.getElementById('decreaseBtn').disabled = copies <= 1;
    document.getElementById('increaseBtn').disabled = copies >= 99;
}

function removeFile() {
    if (confirm('Are you sure you want to remove this file?')) {
        window.location.href = '/';
    }
}

function triggerFileUpload() {
    document.getElementById('additionalFileInput').click();
}

function handleAdditionalFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Create FormData and upload the file
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading indicator
    const addFileBtn = document.querySelector('.add-files-btn');
    const originalContent = addFileBtn.innerHTML;
    addFileBtn.innerHTML = '<span style="font-size: 0.9rem;">Uploading...</span>';
    addFileBtn.disabled = true;
    
    // Upload the file
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            // If successful, reload to show the new file
            window.location.href = response.url;
        } else {
            throw new Error('Upload failed');
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        alert('Failed to upload file. Please try again.');
        addFileBtn.innerHTML = originalContent;
        addFileBtn.disabled = false;
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize button states
    document.getElementById('decreaseBtn').disabled = true;
});
