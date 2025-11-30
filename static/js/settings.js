/**
 * Settings Interface - Habit Management
 *
 * Handles creating, editing, deleting, and reordering habits.
 */

let habits = [];
let draggedElement = null;

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    loadHabits();
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    document.getElementById('add-habit-form').addEventListener('submit', handleAddHabit);
}

/**
 * Load all habits
 */
async function loadHabits() {
    const loadingEl = document.getElementById('loading');
    const emptyStateEl = document.getElementById('empty-state');
    const habitsListEl = document.getElementById('habits-list');

    // Show loading
    loadingEl.classList.remove('hidden');
    emptyStateEl.classList.add('hidden');
    habitsListEl.classList.add('hidden');

    try {
        const response = await fetch('/api/habits');

        if (!response.ok) {
            throw new Error('Failed to fetch habits');
        }

        const data = await response.json();
        habits = data.habits;

        // Hide loading
        loadingEl.classList.add('hidden');

        // Check if we have any habits
        if (habits.length === 0) {
            emptyStateEl.classList.remove('hidden');
            return;
        }

        // Show habits list
        habitsListEl.classList.remove('hidden');

        // Render habits
        renderHabits();

    } catch (error) {
        console.error('Error loading habits:', error);
        showStatus('Error loading habits: ' + error.message, 'error');
    }
}

/**
 * Render habits list
 */
function renderHabits() {
    const habitsListEl = document.getElementById('habits-list');
    habitsListEl.innerHTML = '';

    // Sort by order_index
    const sortedHabits = [...habits].sort((a, b) => a.order_index - b.order_index);

    sortedHabits.forEach(habit => {
        const habitEl = createHabitElement(habit);
        habitsListEl.appendChild(habitEl);
    });
}

/**
 * Create habit element with drag-and-drop
 */
function createHabitElement(habit) {
    const div = document.createElement('div');
    div.className = 'bg-gray-50 rounded-lg p-4 flex items-center gap-3 cursor-move hover:bg-gray-100 transition';
    div.draggable = true;
    div.dataset.habitId = habit.id;

    // Drag handle
    const dragHandle = document.createElement('span');
    dragHandle.className = 'text-gray-400 text-xl cursor-move';
    dragHandle.textContent = '⋮⋮';
    div.appendChild(dragHandle);

    // Habit name
    const nameSpan = document.createElement('span');
    nameSpan.className = 'flex-1 text-gray-900 font-medium';
    nameSpan.textContent = habit.name;
    div.appendChild(nameSpan);

    // Status badges
    const badgesDiv = document.createElement('div');
    badgesDiv.className = 'flex gap-2';

    // Public/Private badge
    const visibilityBadge = document.createElement('span');
    visibilityBadge.className = `px-2 py-1 text-xs rounded ${habit.is_public ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-700'}`;
    visibilityBadge.textContent = habit.is_public ? 'Public' : 'Private';
    badgesDiv.appendChild(visibilityBadge);

    // Active/Inactive badge
    if (!habit.is_active) {
        const activeBadge = document.createElement('span');
        activeBadge.className = 'px-2 py-1 text-xs bg-red-100 text-red-700 rounded';
        activeBadge.textContent = 'Inactive';
        badgesDiv.appendChild(activeBadge);
    }

    div.appendChild(badgesDiv);

    // Edit button
    const editBtn = document.createElement('button');
    editBtn.className = 'px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => editHabit(habit));
    div.appendChild(editBtn);

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'px-3 py-1 text-sm bg-red-500 hover:bg-red-600 text-white rounded transition';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteHabit(habit));
    div.appendChild(deleteBtn);

    // Drag and drop events
    div.addEventListener('dragstart', handleDragStart);
    div.addEventListener('dragover', handleDragOver);
    div.addEventListener('drop', handleDrop);
    div.addEventListener('dragend', handleDragEnd);

    return div;
}

/**
 * Handle adding a new habit
 */
async function handleAddHabit(e) {
    e.preventDefault();

    const nameInput = document.getElementById('habit-name');
    const isPublicCheckbox = document.getElementById('habit-is-public');

    const name = nameInput.value.trim();
    const isPublic = isPublicCheckbox.checked;

    if (!name) return;

    try {
        const response = await fetch('/api/habits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                is_public: isPublic
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create habit');
        }

        const result = await response.json();

        // Clear form
        nameInput.value = '';
        isPublicCheckbox.checked = true;

        // Show success
        showStatus('Habit created successfully!', 'success');

        // Reload habits
        await loadHabits();

    } catch (error) {
        console.error('Error creating habit:', error);
        showStatus('Error: ' + error.message, 'error');
    }
}

/**
 * Edit habit (simple prompt-based for now)
 */
async function editHabit(habit) {
    const newName = prompt('Edit habit name:', habit.name);
    if (!newName || newName === habit.name) return;

    try {
        const response = await fetch(`/api/habits/${habit.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: newName.trim()
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update habit');
        }

        showStatus('Habit updated successfully!', 'success');
        await loadHabits();

    } catch (error) {
        console.error('Error updating habit:', error);
        showStatus('Error: ' + error.message, 'error');
    }
}

/**
 * Delete habit (with confirmation)
 */
async function deleteHabit(habit) {
    if (!confirm(`Are you sure you want to delete "${habit.name}"? This will deactivate the habit.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/habits/${habit.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete habit');
        }

        showStatus('Habit deleted successfully!', 'success');
        await loadHabits();

    } catch (error) {
        console.error('Error deleting habit:', error);
        showStatus('Error: ' + error.message, 'error');
    }
}

/**
 * Drag and drop handlers
 */
function handleDragStart(e) {
    draggedElement = e.currentTarget;
    e.currentTarget.style.opacity = '0.5';
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }

    if (draggedElement !== e.currentTarget) {
        // Get the list
        const list = document.getElementById('habits-list');
        const allItems = [...list.children];

        // Get indices
        const draggedIndex = allItems.indexOf(draggedElement);
        const targetIndex = allItems.indexOf(e.currentTarget);

        // Reorder in DOM
        if (draggedIndex < targetIndex) {
            e.currentTarget.parentNode.insertBefore(draggedElement, e.currentTarget.nextSibling);
        } else {
            e.currentTarget.parentNode.insertBefore(draggedElement, e.currentTarget);
        }

        // Save new order
        saveHabitOrder();
    }

    return false;
}

function handleDragEnd(e) {
    e.currentTarget.style.opacity = '1';
}

/**
 * Save habit order to server
 */
async function saveHabitOrder() {
    const list = document.getElementById('habits-list');
    const habitIds = [...list.children].map(el => parseInt(el.dataset.habitId));

    try {
        const response = await fetch('/api/habits/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                habit_ids: habitIds
            })
        });

        if (!response.ok) {
            throw new Error('Failed to save order');
        }

        showStatus('Order saved successfully!', 'success');

        // Reload to sync order_index
        await loadHabits();

    } catch (error) {
        console.error('Error saving order:', error);
        showStatus('Error: ' + error.message, 'error');
    }
}

/**
 * Show status message
 */
function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');

    statusEl.className = `mt-4 p-4 rounded-lg text-center ${
        type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
    }`;
    statusEl.textContent = message;
    statusEl.classList.remove('hidden');

    // Hide after 3 seconds
    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 3000);
}
