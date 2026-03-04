function sharpei() {
    return {
        categories: [],
        tasks: [],
        selectedCategory: null,
        selectedCategoryName: 'All Tasks',
        newCategoryName: '',
        newTaskTitle: '',
        expandedTasks: [],
        searchQuery: '',
        loading: false,
        error: null,
        showArchived: false,
        showDetails: false,
        showSettings: false,
        darkMode: localStorage.getItem('darkMode') === 'true' || 
                 (localStorage.getItem('darkMode') === null && window.matchMedia('(prefers-color-scheme: dark)').matches),
        today: new Date().setHours(0, 0, 0, 0),
        taskSnapshots: {},

        showError(message) {
            this.error = message;
            setTimeout(() => this.error = null, 4000);
        },

        toggleDarkMode() {
            localStorage.setItem('darkMode', this.darkMode);
        },

        openSettings() {
            this.showSettings = true;
        },

        closeSettings() {
            this.showSettings = false;
        },

        parseQuickAdd(input) {
            let title = input;
            let priority = 1; 
            let hashtags = [];
            let dueDate = null;
            let categoryName = null;

            const priorityMatch = title.match(/\s*!(high|h|low|l)\b/i);
            if (priorityMatch) {
                const p = priorityMatch[1].toLowerCase();
                priority = (p === 'high' || p === 'h') ? 0 : 2;
                title = title.replace(priorityMatch[0], '');
            }

            const tagMatches = title.match(/#\w+/g);
            if (tagMatches) {
                hashtags = tagMatches;
                title = title.replace(/#\w+/g, '');
            }

            const categoryMatch = title.match(/\s*>(\w+)/);
            if (categoryMatch) {
                categoryName = categoryMatch[1];
                title = title.replace(categoryMatch[0], '');
            }

            const dateMatch = title.match(/\s*@(\S+)/);
            if (dateMatch) {
                dueDate = this.parseDueDate(dateMatch[1]);
                title = title.replace(dateMatch[0], '');
            }

            const recurrenceMatch = title.match(/\s*\*(\S+)/);
            let recurrence = null;
            if (recurrenceMatch) {
                recurrence = recurrenceMatch[1];
                title = title.replace(recurrenceMatch[0], '');
            }

            return {
                title: title.trim(),
                priority,
                hashtags: hashtags.join(' '),
                dueDate,
                recurrence,
                categoryName
            };
        },

        parseDueDate(dateStr) {
            const today = new Date();
            today.setHours(12, 0, 0, 0); 

            const lower = dateStr.toLowerCase();

            if (lower === 'today') {
                return today.toISOString();
            }

            if (lower === 'tomorrow') {
                const d = new Date(today);
                d.setDate(d.getDate() + 1);
                return d.toISOString();
            }

            const relativeMatch = lower.match(/^\+(\d+)([dw])$/);
            if (relativeMatch) {
                const num = parseInt(relativeMatch[1]);
                const unit = relativeMatch[2];
                const d = new Date(today);
                if (unit === 'd') {
                    d.setDate(d.getDate() + num);
                } else if (unit === 'w') {
                    d.setDate(d.getDate() + num * 7);
                }
                return d.toISOString();
            }

            const weekdays = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
            const dayIndex = weekdays.indexOf(lower);
            if (dayIndex !== -1) {
                const d = new Date(today);
                const currentDay = d.getDay();
                let daysUntil = dayIndex - currentDay;
                if (daysUntil <= 0) {
                    daysUntil += 7; 
                }
                d.setDate(d.getDate() + daysUntil);
                return d.toISOString();
            }

            if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                const d = new Date(dateStr + 'T12:00:00');
                return d.toISOString();
            }

            return null;
        },

        init() {
            this.fetchCategories().then(() => {
                this.fetchTasks();
            });

            // Timer to notice when the day has flipped
            setInterval(() => {
                const now = new Date().setHours(0, 0, 0, 0);
                if (now !== this.today) {
                    this.today = now;
                }
            }, 60000);

            document.addEventListener('keydown', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                    e.preventDefault();
                    this.archiveCompleted();
                }
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'H') {
                    e.preventDefault();
                    this.toggleShowArchived();
                }
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                    e.preventDefault();
                    this.toggleShowDetails();
                }
            });
        },

        fetchCategories() {
            return fetch('/api/categories')
                .then(res => res.json())
                .then(data => {
                    this.categories = data;
                });
        },

        transformTask(t) {
            const tags = [];
            if (t.hashtags) {
                const matches = t.hashtags.match(/#\w+/g);
                if (matches) {
                    matches.forEach(m => tags.push(m));
                }
            }
            return {
                ...t,
                due_date_str: t.due_date ? t.due_date.split('T')[0] : '',
                priority: String(t.priority),
                newSubtaskTitle: '',
                category_id: t.category_id !== null ? t.category_id.toString() : "",
                tags_array: tags,
                recurrence: t.recurrence || '',
                subtasks: (t.subtasks || []).map(sub => this.transformTask(sub))
            };
        },

        fetchTasks() {
            let url = '/api/tasks?';
            if (this.selectedCategory) {
                url += `category_id=${this.selectedCategory}&`;
            }
            if (this.searchQuery) {
                url += `q=${encodeURIComponent(this.searchQuery)}&`;
            }
            if (this.showArchived) {
                url += `show_archived=true`;
            }
            this.loading = true;
            fetch(url)
                .then(res => {
                    if (!res.ok) throw new Error('Failed to load tasks');
                    return res.json();
                })
                .then(data => {
                    this.tasks = data.map(t => this.transformTask(t));
                })
                .catch(err => this.showError(err.message))
                .finally(() => this.loading = false);
        },

        searchTasks() {
            this.fetchTasks();
        },
        
        clearSearch() {
            this.searchQuery = '';
            this.fetchTasks();
        },

        filterByTag(tag) {
            this.searchQuery = tag;
            this.fetchTasks();
        },

        initSortable(el, priority) {
            new Sortable(el, {
                group: 'tasks',
                animation: 150,
                handle: '.drag-handle',
                onEnd: (evt) => {
                    const taskId = evt.item.getAttribute('data-id');
                    const fromList = evt.from;
                    const toList = evt.to;
                    
                    const newPriority = parseInt(toList.id.replace('list-p', ''));
                    const taskIds = Array.from(toList.querySelectorAll('.task-item-container')).map(item => item.getAttribute('data-id'));
                    
                    fetch('/api/tasks/reorder', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task_ids: taskIds })
                    })
                    .then(res => {
                        if (!res.ok) throw new Error('Failed to reorder tasks');
                        if (fromList !== toList) {
                            const task = this.tasks.find(t => t.id == taskId);
                            if (task) {
                                task.priority = newPriority;
                                this.saveTask(task);
                            }
                        } else {
                            this.fetchTasks();
                        }
                    })
                    .catch(err => this.showError(err.message));
                }
            });
        },

        selectCategory(id) {
            this.selectedCategory = id;
            if (id === null) {
                this.selectedCategoryName = 'All Tasks';
            } else {
                const cat = this.categories.find(c => c.id === id);
                this.selectedCategoryName = cat ? cat.name : 'All Tasks';
            }
            this.fetchTasks();
        },

        addCategory() {
            if (!this.newCategoryName.trim()) return;
            fetch('/api/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: this.newCategoryName })
            })
            .then(res => {
                if (!res.ok) throw new Error('Failed to add category');
                this.newCategoryName = '';
                this.fetchCategories();
            })
            .catch(err => this.showError(err.message));
        },

        deleteCategory(id) {
            if (!confirm('Delete this category? Tasks will be moved to "No Category".')) return;
            fetch(`/api/categories/${id}`, { method: 'DELETE' })
                .then(res => {
                    if (!res.ok) throw new Error('Failed to delete category');
                    if (this.selectedCategory === id) {
                        this.selectedCategory = null;
                        this.selectedCategoryName = 'All Tasks';
                    }
                    this.fetchCategories();
                    this.fetchTasks();
                })
                .catch(err => this.showError(err.message));
        },

        addTask() {
            if (!this.newTaskTitle.trim()) return;

            const parsed = this.parseQuickAdd(this.newTaskTitle);

            let categoryId = this.selectedCategory;
            if (parsed.categoryName) {
                const cat = this.categories.find(
                    c => c.name.toLowerCase() === parsed.categoryName.toLowerCase()
                );
                if (cat) {
                    categoryId = cat.id;
                }
            }

            const data = {
                title: parsed.title,
                category_id: categoryId,
                priority: parsed.priority,
                hashtags: parsed.hashtags || null,
                due_date: parsed.dueDate,
                recurrence: parsed.recurrence
            };

            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(res => {
                if (!res.ok) throw new Error('Failed to add task');
                this.newTaskTitle = '';
                this.fetchTasks();
            })
            .catch(err => this.showError(err.message));
        },

        addSubtask(parentTask) {
            if (!parentTask.newSubtaskTitle.trim()) return;
            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: parentTask.newSubtaskTitle,
                    category_id: this.selectedCategory,
                    parent_id: parentTask.id,
                    priority: parentTask.priority
                })
            })
            .then(res => {
                if (!res.ok) throw new Error('Failed to add subtask');
                parentTask.newSubtaskTitle = '';
                this.fetchTasks();
            })
            .catch(err => this.showError(err.message));
        },

        toggleTask(task) {
            task.completed = !task.completed;
            if (!task.completed) {
                task.archived = false;
            }
            this.saveTask(task);
        },

        saveTask(task) {
            const data = {
                title: task.title,
                description: task.description,
                due_date: task.due_date_str ? new Date(task.due_date_str + 'T12:00:00').toISOString() : null,
                priority: parseInt(task.priority),
                position: task.position || 0,
                hashtags: task.hashtags,
                recurrence: task.recurrence,
                completed: task.completed,
                archived: task.archived || false,
                category_id: (task.category_id && task.category_id !== "") ? parseInt(task.category_id) : null,
                parent_id: task.parent_id
            };

            fetch(`/api/tasks/${task.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(res => {
                if (!res.ok) throw new Error('Failed to save task');
                if (this.taskSnapshots[task.id]) {
                    this.taskSnapshots[task.id] = this._snapshotFields(task);
                }
                this.fetchTasks();
            })
            .catch(err => this.showError(err.message));
        },

        deleteTask(id) {
            if (confirm('Delete this task?')) {
                fetch(`/api/tasks/${id}`, { method: 'DELETE' })
                    .then(res => {
                        if (!res.ok) throw new Error('Failed to delete task');
                        this.fetchTasks();
                    })
                    .catch(err => this.showError(err.message));
            }
        },

        archiveCompleted() {
            let url = '/api/tasks/archive-completed';
            if (this.selectedCategory) {
                url += `?category_id=${this.selectedCategory}`;
            }
            fetch(url, { method: 'POST' })
                .then(res => {
                    if (!res.ok) throw new Error('Failed to archive tasks');
                    return res.json();
                })
                .then(data => {
                    this.fetchTasks();
                })
                .catch(err => this.showError(err.message));
        },

        toggleShowArchived() {
            this.showArchived = !this.showArchived;
            this.fetchTasks();
        },

        toggleShowDetails() {
            this.showDetails = !this.showDetails;
        },

        toggleExpand(task) {
            if (this.expandedTasks.includes(task.id)) {
                this.expandedTasks = this.expandedTasks.filter(id => id !== task.id);
                delete this.taskSnapshots[task.id];
            } else {
                this.expandedTasks.push(task.id);
                this.taskSnapshots[task.id] = this._snapshotFields(task);
            }
        },

        _snapshotFields(task) {
            return {
                description: task.description ?? '',
                due_date_str: task.due_date_str,
                priority: String(task.priority),  
                category_id: task.category_id,
                hashtags: task.hashtags ?? '',
                recurrence: task.recurrence ?? '',
            };
        },

        isDirty(task) {
            const snap = this.taskSnapshots[task.id];
            if (!snap) return false;
            const norm = v => (v == null ? '' : String(v));
            return norm(snap.description) !== norm(task.description)
                || snap.due_date_str !== task.due_date_str
                || snap.priority !== task.priority
                || snap.category_id !== task.category_id
                || norm(snap.hashtags) !== norm(task.hashtags)
                || norm(snap.recurrence) !== norm(task.recurrence);
        },

        formatDate(dateStr, isCompleted = false) {
            if (!dateStr) return { text: '', status: '' };

            const d = new Date(dateStr);
            const todayDate = new Date(this.today);

            const dueDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            const today = new Date(todayDate.getFullYear(), todayDate.getMonth(), todayDate.getDate());

            const diffDays = Math.round((dueDate - today) / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                if (isCompleted) {
                    return { text: d.toLocaleDateString(), status: '' };
                }
                const absDays = Math.abs(diffDays);
                let timeStr;
                if (absDays >= 7) {
                    const weeks = Math.floor(absDays / 7);
                    timeStr = weeks + 'w';
                } else {
                    timeStr = absDays + 'd';
                }
                return { text: `Overdue: ${timeStr}`, status: 'overdue' };
            } else if (diffDays === 0) {
                return { text: 'Today', status: isCompleted ? '' : 'urgent' };
            } else if (diffDays === 1) {
                return { text: 'Tomorrow', status: isCompleted ? '' : 'urgent' };
            } else {
                return { text: d.toLocaleDateString(), status: '' };
            }
        }
    };
}

document.addEventListener('alpine:init', () => {
    Alpine.data('sharpei', sharpei);
});
