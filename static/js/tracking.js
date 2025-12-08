/**
 * Habit Tracking Interface
 *
 * Handles daily habit tracking with date navigation and save functionality.
 */

let currentDate = initialDate; // From template
let habitsData = {};

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTracking();
    setupEventListeners();
});

/**
 * Initialize tracking interface
 */
function initializeTracking() {
    updateDateDisplay();
    loadTrackingData();
}

/**
 * Setup event listeners for navigation and save
 */
function setupEventListeners() {
    document.getElementById('prev-day').addEventListener('click', () => navigateDate(-1));
    document.getElementById('next-day').addEventListener('click', () => navigateDate(1));
    document.getElementById('today-btn').addEventListener('click', goToToday);
    document.getElementById('save-btn').addEventListener('click', saveDayLogs);
}

/**
 * Update date display
 */
function updateDateDisplay() {
    const date = new Date(currentDate + 'T12:00:00'); // Noon to avoid timezone issues
    const today = new Date();
    today.setHours(12, 0, 0, 0);

    // Format: "Monday, January 15, 2024"
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('current-date').textContent = date.toLocaleDateString('en-US', options);

    // Date label (Today, Yesterday, etc.)
    const diffDays = Math.floor((date - today) / (1000 * 60 * 60 * 24));
    let label = '';

    if (diffDays === 0) {
        label = 'Today';
    } else if (diffDays === -1) {
        label = 'Yesterday';
    } else if (diffDays === 1) {
        label = 'Tomorrow';
    } else if (diffDays > 1) {
        label = `${diffDays} days from now`;
    } else {
        label = `${Math.abs(diffDays)} days ago`;
    }

    document.getElementById('date-label').textContent = label;
}

/**
 * Navigate to a different date
 */
function navigateDate(dayOffset) {
    const date = new Date(currentDate + 'T12:00:00');
    date.setDate(date.getDate() + dayOffset);
    currentDate = formatDate(date);

    updateDateDisplay();
    loadTrackingData();
}

/**
 * Go to today
 */
function goToToday() {
    currentDate = formatDate(new Date());
    updateDateDisplay();
    loadTrackingData();
}

/**
 * Load tracking data for current date
 */
async function loadTrackingData() {
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const habitsContainerEl = document.getElementById('habits-container');
    const habitsListEl = document.getElementById('habits-list');

    // Show loading
    loadingEl.classList.remove('hidden');
    emptyStateEl.classList.add('hidden');
    habitsContainerEl.classList.add('hidden');

    try {
        const response = await fetch(`/api/track/data?date=${currentDate}`);

        if (!response.ok) {
            throw new Error('Failed to fetch tracking data');
        }

        const data = await response.json();
        habitsData = data;

        // Hide loading
        loadingEl.classList.add('hidden');

        // Check if we have any habits
        if (!data.habits || data.habits.length === 0) {
            emptyStateEl.classList.remove('hidden');
            return;
        }

        // Show habits container
        habitsContainerEl.classList.remove('hidden');

        // Clear existing habits
        habitsListEl.innerHTML = '';

        // Render habits
        data.habits.forEach(habit => {
            const habitEl = createHabitElement(habit);
            habitsListEl.appendChild(habitEl);
        });

    } catch (error) {
        console.error('Error loading tracking data:', error);
        loadingEl.innerHTML = `
            <div class="text-red-600">
                <p class="text-xl font-semibold">Error Loading Data</p>
                <p class="mt-2">${error.message}</p>
            </div>
        `;
    }
}

/**
 * Create habit element with toggle button and optional value input
 */
function createHabitElement(habit) {
    const div = document.createElement('div');
    div.className = 'bg-white rounded-lg shadow-sm p-4 transition hover:shadow-md';
    div.dataset.habitId = habit.id;

    // Wrapper for flexible layout
    const wrapper = document.createElement('div');
    wrapper.className = 'flex items-center justify-between gap-4';

    // Habit info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'flex-1';

    const nameSpan = document.createElement('span');
    nameSpan.className = 'text-lg font-medium text-gray-900';
    nameSpan.textContent = habit.name;

    infoDiv.appendChild(nameSpan);

    // Private badge
    if (!habit.is_public) {
        const badge = document.createElement('span');
        badge.className = 'ml-2 px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded';
        badge.textContent = 'Private';
        infoDiv.appendChild(badge);
    }

    // Value tracking badge
    if (habit.tracks_value) {
        const valueBadge = document.createElement('span');
        valueBadge.className = 'ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded';
        valueBadge.textContent = habit.value_unit ? `📊 ${habit.value_unit}` : '📊';
        infoDiv.appendChild(valueBadge);
    }

    wrapper.appendChild(infoDiv);

    // Controls div (value input + button)
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'flex items-center gap-3';

    // Value input for value-tracking habits
    if (habit.tracks_value) {
        const valueInput = document.createElement('input');
        valueInput.type = 'number';
        valueInput.step = 'any';
        valueInput.placeholder = habit.value_unit || 'Value';
        valueInput.className = 'w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent';
        valueInput.dataset.habitId = habit.id;
        valueInput.value = habit.value || '';
        valueInput.setAttribute('aria-label', `Value for ${habit.name}`);

        valueInput.addEventListener('input', (e) => {
            const habit = habitsData.habits.find(h => h.id === parseInt(e.target.dataset.habitId));
            if (habit) {
                habit.value = e.target.value ? parseFloat(e.target.value) : null;
            }
        });

        controlsDiv.appendChild(valueInput);
    }

    // Toggle button
    const button = document.createElement('button');
    button.className = 'px-6 py-3 rounded-lg font-semibold transition transform hover:scale-105 min-w-[120px]';
    button.dataset.habitId = habit.id;

    if (habit.status) {
        button.className += ' bg-green-600 hover:bg-green-700 text-white';
        button.textContent = '✓ Done';
        button.setAttribute('aria-label', `Mark ${habit.name} as not done`);
        button.setAttribute('aria-pressed', 'true');
    } else {
        button.className += ' bg-gray-200 hover:bg-gray-300 text-gray-700';
        button.textContent = 'Not Done';
        button.setAttribute('aria-label', `Mark ${habit.name} as done`);
        button.setAttribute('aria-pressed', 'false');
    }

    button.addEventListener('click', () => toggleHabit(habit.id));

    controlsDiv.appendChild(button);
    wrapper.appendChild(controlsDiv);

    div.appendChild(wrapper);

    return div;
}

/**
 * Toggle habit status
 */
function toggleHabit(habitId) {
    // Find habit in data
    const habit = habitsData.habits.find(h => h.id === habitId);
    if (!habit) return;

    // Toggle status
    habit.status = !habit.status;

    // Update UI
    const habitEl = document.querySelector(`[data-habit-id="${habitId}"]`);
    if (!habitEl) return;

    const button = habitEl.querySelector('button');

    if (habit.status) {
        button.className = 'px-6 py-3 rounded-lg font-semibold transition transform hover:scale-105 min-w-[120px] bg-green-600 hover:bg-green-700 text-white';
        button.textContent = '✓ Done';
        button.setAttribute('aria-label', `Mark ${habit.name} as not done`);
        button.setAttribute('aria-pressed', 'true');
    } else {
        button.className = 'px-6 py-3 rounded-lg font-semibold transition transform hover:scale-105 min-w-[120px] bg-gray-200 hover:bg-gray-300 text-gray-700';
        button.textContent = 'Not Done';
        button.setAttribute('aria-label', `Mark ${habit.name} as done`);
        button.setAttribute('aria-pressed', 'false');
    }
}

/**
 * Save day's logs
 */
async function saveDayLogs() {
    const saveBtn = document.getElementById('save-btn');
    const saveStatus = document.getElementById('save-status');

    // Disable button
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    // Prepare logs data
    const logs = habitsData.habits.map(habit => {
        const logEntry = {
            habit_id: habit.id,
            status: habit.status
        };

        // Include value if the habit tracks values
        if (habit.tracks_value && habit.value !== null && habit.value !== undefined && habit.value !== '') {
            logEntry.value = habit.value;
        }

        return logEntry;
    });

    try {
        const response = await fetch('/api/track/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: currentDate,
                logs: logs
            })
        });

        if (!response.ok) {
            throw new Error('Failed to save logs');
        }

        const result = await response.json();

        // Show success message
        saveStatus.className = 'mt-4 p-4 rounded-lg text-center bg-green-100 text-green-800';
        saveStatus.textContent = '✓ ' + result.message;
        saveStatus.classList.remove('hidden');

        // Hide after 3 seconds
        setTimeout(() => {
            saveStatus.classList.add('hidden');
        }, 3000);

    } catch (error) {
        console.error('Error saving logs:', error);

        // Show error message
        saveStatus.className = 'mt-4 p-4 rounded-lg text-center bg-red-100 text-red-800';
        saveStatus.textContent = '✗ Error: ' + error.message;
        saveStatus.classList.remove('hidden');

    } finally {
        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Day';
    }
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
