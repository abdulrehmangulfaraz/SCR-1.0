/**
 * SCR Platform - Scan Process Controller
 * Handles real-time scan progress, result visualization, and animation controls
 */

// Global scan variables
let scanEventSource = null;
let currentScanDomain = null;
let scanType = null;
let scanInProgress = false;

/**
 * Initializes and starts a new security scan
 * @param {string} domain - Target domain to scan
 * @param {string} type - Type of scan (full, quick, headers)
 */
function startScan(domain, type) {
    // Validate inputs
    if (!domain) {
        showError("Please enter a valid domain");
        return;
    }

    // Store scan parameters
    currentScanDomain = domain;
    scanType = type || "full";
    scanInProgress = true;

    // Update UI
    updateScanStatus("Initializing scan...", 0);
    activateStage("stage-recon");
    
    // Clear any previous scan results
    const resultContainer = document.getElementById("scan-result-container");
    if (resultContainer) {
        resultContainer.classList.add("d-none");
    }

    // Start scan animation
    const radar = document.querySelector(".radar-animation");
    if (radar) {
        radar.classList.add("active");
    }

    // Create EventSource for streaming scan results
    const scanUrl = `/api/scan`;
    
    // Use fetch with streaming response
    fetch(scanUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            domain: domain,
            scan_type: scanType
        })
    })
    .then(response => {
        // Get reader from response body stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Read chunks of data as they arrive
        function readStream() {
            return reader.read().then(({ done, value }) => {
                if (done) {
                    console.log("Stream complete");
                    return;
                }
                
                // Decode and process the chunk
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                lines.forEach(line => {
                    if (line.trim()) {
                        try {
                            const message = JSON.parse(line);
                            processScanMessage(message);
                        } catch (e) {
                            console.error("Error parsing scan message:", e);
                        }
                    }
                });
                
                // Continue reading
                return readStream();
            });
        }
        
        // Start reading the stream
        return readStream();
    })
    .catch(error => {
        console.error("Scan error:", error);
        scanComplete({
            status: 'error',
            message: 'An error occurred during the scan. Please try again.'
        });
    });
}

/**
 * Process a scan message from the server
 * @param {Object} message - Scan progress message
 */
function processScanMessage(message) {
    console.log("Scan message:", message);
    
    if (message.status === 'progress') {
        // Update progress bar and status message
        updateScanStatus(message.message, message.progress);
        
        // Update stage indicators
        if (message.stage === 'reconnaissance') {
            completeStage('stage-recon');
            activateStage('stage-vuln');
        } else if (message.stage === 'vulnerability_scan') {
            completeStage('stage-vuln');
            activateStage('stage-report');
        }
    } else if (message.status === 'complete') {
        // Scan is complete
        updateScanStatus(message.message, 100);
        completeStage('stage-report');
        scanComplete(message);
    } else if (message.status === 'error') {
        // Scan error
        showError(message.message);
        resetScanAnimation();
    }
}

/**
 * Update the scan status display
 * @param {string} message - Status message
 * @param {number} progress - Progress percentage (0-100)
 */
function updateScanStatus(message, progress) {
    const statusElement = document.getElementById("scan-status");
    const progressBar = document.getElementById("scan-progress-bar");
    
    if (statusElement) {
        statusElement.innerHTML = `<p>${message}</p>`;
    }
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute("aria-valuenow", progress);
        
        // Add success class when complete
        if (progress === 100) {
            progressBar.classList.remove("bg-primary");
            progressBar.classList.add("bg-success");
        }
    }
}

/**
 * Activate a specific stage in the scan process
 * @param {string} stageId - HTML ID of the stage element
 */
function activateStage(stageId) {
    const stage = document.getElementById(stageId);
    if (!stage) return;
    
    // Add active class to stage
    stage.classList.add("active");
    
    // Show spinner
    const spinner = stage.querySelector(".spinner-border");
    if (spinner) {
        spinner.classList.remove("d-none");
    }
}

/**
 * Mark a scan stage as completed
 * @param {string} stageId - HTML ID of the stage element
 */
function completeStage(stageId) {
    const stage = document.getElementById(stageId);
    if (!stage) return;
    
    // Replace spinner with check icon
    const statusContainer = stage.querySelector(".stage-status");
    if (statusContainer) {
        statusContainer.innerHTML = '<i class="fas fa-check-circle text-success"></i>';
    }
    
    // Add completed class
    stage.classList.add("completed");
}

/**
 * Handle scan completion
 * @param {Object} result - Scan result data
 */
function scanComplete(result) {
    scanInProgress = false;
    
    // Stop the radar animation
    const radar = document.querySelector(".radar-animation");
    if (radar) {
        radar.classList.remove("active");
    }
    
    // Show the completed message
    updateScanStatus("Scan completed successfully!", 100);
    
    // Show the view report button
    const resultContainer = document.getElementById("scan-result-container");
    const viewReportBtn = document.getElementById("view-report-btn");
    
    if (resultContainer && viewReportBtn) {
        resultContainer.classList.remove("d-none");
        viewReportBtn.href = `/scan_result/${result.scan_id}`;
    }
    
    // Add success pulse to progress container
    const progressContainer = document.querySelector(".scan-progress-container");
    if (progressContainer) {
        progressContainer.classList.add("scan-complete-pulse");
    }
}

/**
 * Reset scan animation and progress indicators
 */
function resetScanAnimation() {
    scanInProgress = false;
    
    // Reset radar animation
    const radar = document.querySelector(".radar-animation");
    if (radar) {
        radar.classList.remove("active");
    }
    
    // Reset progress bar
    const progressBar = document.getElementById("scan-progress-bar");
    if (progressBar) {
        progressBar.style.width = "0%";
        progressBar.setAttribute("aria-valuenow", 0);
        progressBar.classList.remove("bg-success");
        progressBar.classList.add("bg-primary");
    }
    
    // Reset stages
    const stages = document.querySelectorAll(".stage-item");
    stages.forEach(stage => {
        stage.classList.remove("active", "completed");
        const spinner = stage.querySelector(".spinner-border");
        if (spinner) {
            spinner.classList.add("d-none");
        }
        const checkIcon = stage.querySelector(".fa-check-circle");
        if (checkIcon) {
            checkIcon.parentNode.innerHTML = '<div class="spinner-border spinner-border-sm text-primary d-none" role="status"></div>';
        }
    });
}

/**
 * Display an error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const statusElement = document.getElementById("scan-status");
    if (statusElement) {
        statusElement.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
            <button class="btn btn-primary mt-3" onclick="window.location.href='/scan'">
                <i class="fas fa-redo me-2"></i> Try Again
            </button>
        `;
    }
    
    resetScanAnimation();
}

// Initialize scan process on page load if scan parameter is present
document.addEventListener("DOMContentLoaded", function() {
    // Check if we're on a scan page with target domain
    const scanningElement = document.querySelector(".scan-process-container");
    if (scanningElement) {
        const urlParams = new URLSearchParams(window.location.search);
        const domain = urlParams.get("domain");
        const type = urlParams.get("scan_type") || "full";
        
        if (domain) {
            // Slight delay to allow animations to initialize
            setTimeout(() => {
                startScan(domain, type);
            }, 500);
        }
    }
    
    // Initialize scan form event listeners
    const scanForm = document.getElementById("scan-form");
    if (scanForm) {
        scanForm.addEventListener("submit", function(e) {
            // Form submission is handled by the server
            // but we can add client-side validation here
            const domainInput = document.getElementById("domain");
            if (!domainInput || !domainInput.value) {
                e.preventDefault();
                alert("Please enter a valid domain");
                return false;
            }
            
            // Add loading state to submit button
            const submitButton = scanForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Starting Scan...';
                submitButton.disabled = true;
            }
            
            return true;
        });
    }
});
