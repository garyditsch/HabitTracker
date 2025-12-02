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

        // Initialize yearly heatmap
        initializeHeatmap();

        // Initialize archived habits
        initializeArchivedHabits();

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

    // Format created date
    const createdDate = habit.created_at ? formatDisplayDate(habit.created_at.split(' ')[0]) : 'Unknown';

    header.innerHTML = `
        <h3 class="text-xl font-semibold text-gray-800">${escapeHtml(habit.name)}</h3>
        <div class="flex gap-4 mt-2 text-sm text-gray-600">
            <span>🔥 ${habit.current_streak} day streak</span>
            <span>✓ ${habit.completion_rate}% (${habit.completed_days}/${habit.total_days})</span>
        </div>
        <div class="mt-1 text-xs text-gray-500">
            Started: ${createdDate}
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

// ========================================
// YEARLY HEATMAP FUNCTIONALITY
// ========================================

// Global state for heatmap
let currentHeatmapYear = new Date().getFullYear();

/**
 * Initialize yearly heatmap
 * Called after loading dashboard habits
 */
function initializeHeatmap() {
    // Set up event listeners for year navigation
    const prevYearBtn = document.getElementById('prev-year');
    const nextYearBtn = document.getElementById('next-year');

    if (prevYearBtn) {
        prevYearBtn.addEventListener('click', () => {
            currentHeatmapYear--;
            loadHeatmap(currentHeatmapYear);
        });
    }

    if (nextYearBtn) {
        nextYearBtn.addEventListener('click', () => {
            currentHeatmapYear++;
            loadHeatmap(currentHeatmapYear);
        });
    }

    // Load initial heatmap for current year
    loadHeatmap(currentHeatmapYear);
}

/**
 * Load heatmap data for a specific year
 */
async function loadHeatmap(year) {
    const heatmapSection = document.getElementById('heatmap-section');
    const heatmapCalendar = document.getElementById('heatmap-calendar');
    const heatmapLoading = document.getElementById('heatmap-loading');
    const currentYearEl = document.getElementById('current-year');

    if (!heatmapSection || !heatmapCalendar) {
        console.error('Heatmap elements not found');
        return;
    }

    try {
        // Show loading state
        heatmapSection.classList.remove('hidden');
        heatmapLoading.classList.remove('hidden');
        heatmapCalendar.classList.add('hidden');

        // Update year display
        if (currentYearEl) {
            currentYearEl.textContent = year;
        }

        // Fetch heatmap data
        const response = await fetch(`/api/dashboard/heatmap?year=${year}`);

        if (!response.ok) {
            throw new Error('Failed to fetch heatmap data');
        }

        const data = await response.json();

        // Hide loading, show calendar
        heatmapLoading.classList.add('hidden');
        heatmapCalendar.classList.remove('hidden');

        // Update statistics
        updateHeatmapStats(data.overall_stats);

        // Render the calendar grid
        renderHeatmapGrid(data);

    } catch (error) {
        console.error('Error loading heatmap:', error);
        heatmapLoading.innerHTML = `
            <div class="text-red-600">
                <p class="font-semibold">Error Loading Heatmap</p>
                <p class="text-sm mt-2">${error.message}</p>
            </div>
        `;
    }
}

/**
 * Update heatmap statistics display
 */
function updateHeatmapStats(stats) {
    const statDays = document.getElementById('stat-days');
    const statAverage = document.getElementById('stat-average');
    const statBest = document.getElementById('stat-best');
    const statBestDate = document.getElementById('stat-best-date');
    const statWorst = document.getElementById('stat-worst');
    const statWorstDate = document.getElementById('stat-worst-date');

    if (statDays) {
        statDays.textContent = stats.total_days_tracked;
    }

    if (statAverage) {
        statAverage.textContent = `${stats.average_completion}%`;
    }

    if (stats.best_day) {
        if (statBest) {
            statBest.textContent = `${stats.best_day.percentage}%`;
        }
        if (statBestDate) {
            statBestDate.textContent = formatDisplayDate(stats.best_day.date);
        }
    } else {
        if (statBest) statBest.textContent = '--';
        if (statBestDate) statBestDate.textContent = '--';
    }

    if (stats.worst_day) {
        if (statWorst) {
            statWorst.textContent = `${stats.worst_day.percentage}%`;
        }
        if (statWorstDate) {
            statWorstDate.textContent = formatDisplayDate(stats.worst_day.date);
        }
    } else {
        if (statWorst) statWorst.textContent = '--';
        if (statWorstDate) statWorstDate.textContent = '--';
    }
}

/**
 * Render the entire yearly heatmap grid (12 months)
 */
function renderHeatmapGrid(data) {
    const heatmapCalendar = document.getElementById('heatmap-calendar');

    if (!heatmapCalendar) {
        return;
    }

    // Clear previous content
    heatmapCalendar.innerHTML = '';

    // Render each month
    data.months.forEach(monthData => {
        const monthContainer = createMonthCalendar(monthData);
        heatmapCalendar.appendChild(monthContainer);
    });
}

/**
 * Create a single month calendar
 */
function createMonthCalendar(monthData) {
    const container = document.createElement('div');
    container.className = 'bg-white rounded-lg border border-gray-200 p-4';

    // Month name header
    const header = document.createElement('h3');
    header.className = 'text-sm font-semibold text-gray-700 mb-3';
    header.textContent = monthData.month_name;
    container.appendChild(header);

    // Weekday headers
    const weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    const weekdayRow = document.createElement('div');
    weekdayRow.className = 'grid grid-cols-7 gap-1 mb-2';

    weekdays.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'text-xs text-gray-500 text-center font-medium';
        dayHeader.textContent = day;
        weekdayRow.appendChild(dayHeader);
    });
    container.appendChild(weekdayRow);

    // Calendar grid
    const calendarGrid = document.createElement('div');
    calendarGrid.className = 'grid grid-cols-7 gap-1';

    // Add empty cells for days before the month starts (0=Monday)
    for (let i = 0; i < monthData.first_day_weekday; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'aspect-square';
        calendarGrid.appendChild(emptyCell);
    }

    // Add day cells
    monthData.days.forEach(dayData => {
        const dayCell = createDayCell(dayData);
        calendarGrid.appendChild(dayCell);
    });

    container.appendChild(calendarGrid);

    return container;
}

/**
 * Create a single day cell with color coding
 */
function createDayCell(dayData) {
    const cell = document.createElement('div');
    cell.className = 'aspect-square rounded border cursor-pointer transition-transform hover:scale-110';

    // Get color based on completion percentage
    const colorClass = getColorForPercentage(dayData.completion_percentage);
    cell.className += ' ' + colorClass;

    // Add tooltip with details
    const tooltipText = `${formatDisplayDate(dayData.date)}\n${dayData.completion_percentage}% (${dayData.completed_count}/${dayData.total_count} habits)`;
    cell.title = tooltipText;
    cell.setAttribute('aria-label', tooltipText);

    // Add day number (small text in corner)
    const dayNumber = document.createElement('div');
    dayNumber.className = 'text-xs text-gray-700 p-0.5 select-none';
    dayNumber.textContent = dayData.day_of_month;
    cell.appendChild(dayNumber);

    return cell;
}

/**
 * Get Tailwind color classes based on completion percentage
 * Uses colorblind-friendly blue-to-orange gradient
 */
function getColorForPercentage(percentage) {
    if (percentage === 0) {
        return 'bg-gray-200 border-gray-300';
    } else if (percentage <= 25) {
        return 'bg-blue-200 border-blue-300';
    } else if (percentage <= 50) {
        return 'bg-blue-400 border-blue-500';
    } else if (percentage <= 75) {
        return 'bg-blue-600 border-blue-700';
    } else {
        return 'bg-orange-500 border-orange-600';
    }
}

/**
 * Format date for display (e.g., "Jan 15, 2025")
 */
function formatDisplayDate(dateStr) {
    const date = new Date(dateStr + 'T12:00:00'); // Add time to avoid timezone issues
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

// ========================================
// ARCHIVED HABITS FUNCTIONALITY
// ========================================

/**
 * Initialize and load archived habits
 * Called after loading dashboard habits
 */
function initializeArchivedHabits() {
    loadArchivedHabits();
}

/**
 * Load archived habits data and render cards
 */
async function loadArchivedHabits() {
    const archivedSection = document.getElementById('archived-section');
    const archivedGrid = document.getElementById('archived-grid');
    const archivedEmpty = document.getElementById('archived-empty');

    if (!archivedSection || !archivedGrid || !archivedEmpty) {
        return;
    }

    try {
        // Fetch archived habits data
        const response = await fetch('/api/dashboard/archived');

        if (!response.ok) {
            throw new Error('Failed to fetch archived habits');
        }

        const archived = await response.json();

        // Check if we have any archived habits
        if (!archived || archived.length === 0) {
            archivedEmpty.classList.remove('hidden');
            return;
        }

        // Show section
        archivedSection.classList.remove('hidden');
        archivedGrid.classList.remove('hidden');

        // Render each archived habit card
        archived.forEach(habit => {
            const card = createArchivedHabitCard(habit);
            archivedGrid.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading archived habits:', error);
    }
}

/**
 * Create an archived habit card
 */
function createArchivedHabitCard(habit) {
    // Create card container
    const card = document.createElement('div');
    card.className = 'bg-gray-50 rounded-lg border border-gray-200 p-4';

    // Format dates
    const createdDate = habit.created_at ? formatDisplayDate(habit.created_at.split(' ')[0]) : 'Unknown';
    const firstLog = habit.date_range ? formatDisplayDate(habit.date_range.first_log) : '--';
    const lastLog = habit.date_range ? formatDisplayDate(habit.date_range.last_log) : '--';

    card.innerHTML = `
        <div class="mb-3">
            <h3 class="text-lg font-semibold text-gray-700">${escapeHtml(habit.name)}</h3>
            <div class="text-xs text-gray-500 mt-1">
                Started: ${createdDate}
            </div>
        </div>

        <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="bg-white rounded p-2">
                <div class="text-gray-600 text-xs">Completion Rate</div>
                <div class="font-bold text-gray-900">${habit.completion_rate}%</div>
            </div>
            <div class="bg-white rounded p-2">
                <div class="text-gray-600 text-xs">Longest Streak</div>
                <div class="font-bold text-gray-900">${habit.longest_streak} days</div>
            </div>
            <div class="bg-white rounded p-2">
                <div class="text-gray-600 text-xs">Total Completions</div>
                <div class="font-bold text-gray-900">${habit.total_completions}</div>
            </div>
            <div class="bg-white rounded p-2">
                <div class="text-gray-600 text-xs">Days Tracked</div>
                <div class="font-bold text-gray-900">${habit.total_days_tracked}</div>
            </div>
        </div>

        <div class="mt-3 text-xs text-gray-500 border-t border-gray-200 pt-2">
            <div>Active: ${firstLog} - ${lastLog}</div>
        </div>
    `;

    return card;
}
