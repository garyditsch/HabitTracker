/**
 * Public Dashboard - Chart.js Visualization
 *
 * Fetches public habit data and renders charts for each habit.
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

/**
 * Load dashboard data and render habit cards
 */
async function loadDashboard() {
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const habitsGridEl = document.getElementById('habits-grid');

    try {
        // Fetch dashboard data from API
        const response = await fetch('/api/dashboard/data');

        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data');
        }

        const data = await response.json();

        // Hide loading
        loadingEl.classList.add('hidden');

        // Check if we have any habits
        if (!data.habits || data.habits.length === 0) {
            emptyStateEl.classList.remove('hidden');
            return;
        }

        // Show habits grid
        habitsGridEl.classList.remove('hidden');

        // Render each habit card
        data.habits.forEach(habit => {
            const card = createHabitCard(habit);
            habitsGridEl.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading dashboard:', error);
        loadingEl.innerHTML = `
            <div class="text-red-600">
                <p class="text-xl font-semibold">Error Loading Dashboard</p>
                <p class="mt-2">${error.message}</p>
            </div>
        `;
    }
}

/**
 * Create a habit card with chart
 */
function createHabitCard(habit) {
    // Create card container
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md p-6';

    // Create card header
    const header = document.createElement('div');
    header.className = 'mb-4';
    header.innerHTML = `
        <h3 class="text-xl font-semibold text-gray-800">${escapeHtml(habit.name)}</h3>
        <div class="flex gap-4 mt-2 text-sm text-gray-600">
            <span>🔥 ${habit.current_streak} day streak</span>
            <span>✓ ${habit.completion_rate}% (${habit.completed_days}/${habit.total_days})</span>
        </div>
    `;
    card.appendChild(header);

    // Create canvas for chart
    const canvas = document.createElement('canvas');
    canvas.id = `chart-${habit.id}`;
    canvas.style.maxHeight = '200px';
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', `30-day completion chart for ${habit.name}. Current streak: ${habit.current_streak} days. Completion rate: ${habit.completion_rate}%`);
    card.appendChild(canvas);

    // Render chart after a brief delay to ensure DOM is ready
    setTimeout(() => {
        renderHabitChart(canvas.id, habit);
    }, 100);

    return card;
}

/**
 * Render Chart.js chart for a habit
 */
function renderHabitChart(canvasId, habit) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas ${canvasId} not found`);
        return;
    }

    // Prepare data for Chart.js
    const labels = [];
    const data = [];

    // Create a map of dates to status
    const logsMap = {};
    habit.logs.forEach(log => {
        logsMap[log.date] = log.status;
    });

    // Get last 30 days
    const today = new Date();
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = formatDate(date);

        labels.push(formatShortDate(date));
        data.push(logsMap[dateStr] ? 1 : 0);
    }

    // Create chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completed',
                data: data,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: data.map(val => val === 1 ? '#4CAF50' : '#E0E0E0'),
                pointBorderColor: data.map(val => val === 1 ? '#4CAF50' : '#E0E0E0'),
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y === 1 ? 'Completed ✓' : 'Not completed';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return value === 1 ? '✓' : '';
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                }
            }
        }
    });
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Format date as short string (e.g., "Jan 15")
 */
function formatShortDate(date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
