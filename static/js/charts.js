/**
 * SCR Platform - Charts and Data Visualization
 * Handles Chart.js implementation for visualizing scan data and statistics
 */

/**
 * Initialize risk distribution chart
 * @param {string} elementId - HTML Canvas element ID
 * @param {Object} data - Risk data for high, medium, low risks
 */
function initRiskDistributionChart(elementId, data = null) {
    const ctx = document.getElementById(elementId)?.getContext('2d');
    if (!ctx) return null;
    
    // Default data if not provided
    const chartData = data || {
        high: 0,
        medium: 0,
        low: 0
    };
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High Risk', 'Medium Risk', 'Low Risk'],
            datasets: [{
                data: [chartData.high, chartData.medium, chartData.low],
                backgroundColor: [
                    'rgba(220, 53, 69, 0.8)', // Red
                    'rgba(255, 193, 7, 0.8)', // Yellow
                    'rgba(40, 167, 69, 0.8)'  // Green
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(40, 167, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    bodyFont: {
                        size: 14
                    },
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '70%',
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
}

/**
 * Initialize scan history timeline chart
 * @param {string} elementId - HTML Canvas element ID
 * @param {Object} data - Scan history data with dates and counts
 */
function initScanTimelineChart(elementId, data = null) {
    const ctx = document.getElementById(elementId)?.getContext('2d');
    if (!ctx) return null;
    
    // Default data if not provided
    const defaultDates = [];
    const defaultCounts = [];
    
    // Generate default dates (last 7 days)
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        defaultDates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        defaultCounts.push(Math.floor(Math.random() * 10) + 1); // Random sample data
    }
    
    const chartData = data || {
        labels: defaultDates,
        data: defaultCounts
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Scans',
                data: chartData.data,
                fill: {
                    target: 'origin',
                    above: 'rgba(13, 110, 253, 0.1)'
                },
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 2,
                tension: 0.3,
                pointBackgroundColor: 'rgba(13, 110, 253, 1)',
                pointBorderColor: 'rgba(255, 255, 255, 1)',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        precision: 0
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    bodyFont: {
                        size: 14
                    },
                    padding: 12,
                    displayColors: false
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            animations: {
                tension: {
                    duration: 1000,
                    easing: 'linear'
                }
            }
        }
    });
}

/**
 * Initialize vulnerabilities breakdown chart
 * @param {string} elementId - HTML Canvas element ID
 * @param {Object} data - Vulnerability data with categories and counts
 */
function initVulnerabilityChart(elementId, data = null) {
    const ctx = document.getElementById(elementId)?.getContext('2d');
    if (!ctx) return null;
    
    // Default data if not provided
    const chartData = data || {
        labels: ['SQL Injection', 'XSS', 'Missing Headers', 'Open Ports', 'CSRF'],
        data: [4, 7, 12, 5, 3]
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Vulnerabilities',
                data: chartData.data,
                backgroundColor: [
                    'rgba(220, 53, 69, 0.8)',   // Red (SQL Injection)
                    'rgba(255, 102, 0, 0.8)',   // Orange (XSS)
                    'rgba(255, 193, 7, 0.8)',   // Yellow (Headers)
                    'rgba(13, 110, 253, 0.8)',  // Blue (Ports)
                    'rgba(111, 66, 193, 0.8)'   // Purple (CSRF)
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 102, 0, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(13, 110, 253, 1)',
                    'rgba(111, 66, 193, 1)'
                ],
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        precision: 0
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    bodyFont: {
                        size: 14
                    },
                    padding: 12
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Initialize admin dashboard statistics chart
 * @param {string} elementId - HTML Canvas element ID
 * @param {Object} data - Admin statistics data
 */
function initAdminStatsChart(elementId, data = null) {
    const ctx = document.getElementById(elementId)?.getContext('2d');
    if (!ctx) return null;
    
    // Generate last 30 days for default data
    const defaultDates = [];
    const defaultData = {
        scans: [],
        users: []
    };
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        defaultDates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate random sample data
        defaultData.scans.push(Math.floor(Math.random() * 15) + 5);
        defaultData.users.push(Math.floor(Math.random() * 5) + 1);
    }
    
    const chartData = data || {
        labels: defaultDates,
        datasets: defaultData
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Scans',
                    data: chartData.datasets.scans,
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(13, 110, 253, 1)',
                    pointBorderColor: '#fff',
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y'
                },
                {
                    label: 'Active Users',
                    data: chartData.datasets.users,
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'rgba(40, 167, 69, 0.0)',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(40, 167, 69, 1)',
                    pointBorderColor: '#fff',
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Scans',
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Users',
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 10
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    bodyFont: {
                        size: 14
                    },
                    padding: 12
                }
            }
        }
    });
}

/**
 * Update chart data
 * @param {Chart} chart - Chart.js instance to update
 * @param {Object} newData - New data for the chart
 */
function updateChartData(chart, newData) {
    if (!chart) return;
    
    // Update labels if provided
    if (newData.labels) {
        chart.data.labels = newData.labels;
    }
    
    // Update dataset data if provided
    if (newData.data && chart.data.datasets.length > 0) {
        // If it's a single dataset chart
        if (!Array.isArray(newData.data[0])) {
            chart.data.datasets[0].data = newData.data;
        } 
        // If it has multiple datasets
        else {
            newData.data.forEach((dataSet, index) => {
                if (chart.data.datasets[index]) {
                    chart.data.datasets[index].data = dataSet;
                }
            });
        }
    }
    
    // Update chart
    chart.update();
}

// Initialize charts when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Risk distribution chart (dashboard)
    if (document.getElementById('riskChart')) {
        window.riskChart = initRiskDistributionChart('riskChart');
    }
    
    // Admin dashboard charts
    if (document.getElementById('scanActivityChart')) {
        window.scanActivityChart = initScanTimelineChart('scanActivityChart');
    }
    
    if (document.getElementById('riskDistributionChart')) {
        window.riskDistributionChart = initRiskDistributionChart('riskDistributionChart');
    }
    
    // Admin scan stats charts
    if (document.getElementById('scanTrendsChart')) {
        window.scanTrendsChart = initScanTimelineChart('scanTrendsChart');
    }
    
    // Load real data from API if available
    if (window.riskChart || window.scanActivityChart || window.riskDistributionChart) {
        // You might load data from an API here
        // Example:
        // fetch('/api/stats')
        //   .then(response => response.json())
        //   .then(data => {
        //     if (window.riskChart) {
        //       updateChartData(window.riskChart, {
        //         data: [data.high_risk, data.medium_risk, data.low_risk]
        //       });
        //     }
        //   });
    }
});
