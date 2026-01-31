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

        showError(message) {
            this.error = message;
            setTimeout(() => this.error = null, 4000);
        },

        init() {
            this.fetchCategories().then(() => {
                this.fetchTasks();
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
            return {
                ...t,
                due_date_str: t.due_date ? t.due_date.split('T')[0] : '',
                newSubtaskTitle: '',
                category_id: t.category_id !== null ? t.category_id.toString() : "",
                tags_array: t.hashtags ? t.hashtags.split(/[\s,]+/).filter(tag => tag.length > 0) : [],
                subtasks: (t.subtasks || []).map(sub => this.transformTask(sub))
            };
        },

        fetchTasks() {
            let url = '/api/tasks?';
            if (this.selectedCategory) {
                url += `category_id=${this.selectedCategory}&`;
            }
            if (this.searchQuery) {
                url += `q=${encodeURIComponent(this.searchQuery)}`;
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
                    
                    // 1. Save new order
                    fetch('/api/tasks/reorder', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task_ids: taskIds })
                    })
                    .then(res => {
                        if (!res.ok) throw new Error('Failed to reorder tasks');
                        // 2. If the group changed, update the priority of the moved task
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
            const data = {
                title: this.newTaskTitle,
                category_id: this.selectedCategory,
                priority: 1 // Default to Normal; position assigned by backend
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
                completed: task.completed,
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

        toggleExpand(task) {
            if (this.expandedTasks.includes(task.id)) {
                this.expandedTasks = this.expandedTasks.filter(id => id !== task.id);
            } else {
                this.expandedTasks.push(task.id);
            }
        },

        formatDate(dateStr) {
            if (!dateStr) return { text: '', status: '' };

            const d = new Date(dateStr);
            const now = new Date();

            // Normalize to start of day for comparison
            const dueDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

            const diffDays = Math.round((dueDate - today) / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                // Overdue
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
                return { text: 'Today', status: 'urgent' };
            } else if (diffDays === 1) {
                return { text: 'Tomorrow', status: 'urgent' };
            } else {
                return { text: d.toLocaleDateString(), status: '' };
            }
        }
    }
}
