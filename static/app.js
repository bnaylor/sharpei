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

        fetchTasks() {
            let url = '/api/tasks?';
            if (this.selectedCategory) {
                url += `category_id=${this.selectedCategory}&`;
            }
            if (this.searchQuery) {
                url += `q=${encodeURIComponent(this.searchQuery)}`;
            }
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    this.tasks = data.map(t => ({
                        ...t,
                        due_date_str: t.due_date ? t.due_date.split('T')[0] : '',
                        newSubtaskTitle: '',
                        category_id: t.category_id !== null ? t.category_id.toString() : ""
                    }));
                });
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
            }).then(() => {
                this.newCategoryName = '';
                this.fetchCategories();
            });
        },

        addTask() {
            if (!this.newTaskTitle.trim()) return;
            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: this.newTaskTitle,
                    category_id: this.selectedCategory
                })
            }).then(() => {
                this.newTaskTitle = '';
                this.fetchTasks();
            });
        },

        addSubtask(parentTask) {
            if (!parentTask.newSubtaskTitle.trim()) return;
            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: parentTask.newSubtaskTitle,
                    category_id: this.selectedCategory,
                    parent_id: parentTask.id
                })
            }).then(() => {
                parentTask.newSubtaskTitle = '';
                this.fetchTasks();
            });
        },

        toggleTask(task) {
            task.completed = !task.completed;
            this.saveTask(task);
        },

        saveTask(task) {
            const data = {
                title: task.title,
                description: task.description,
                due_date: task.due_date_str ? new Date(task.due_date_str).toISOString() : null,
                priority: parseInt(task.priority),
                hashtags: task.hashtags,
                completed: task.completed,
                category_id: (task.category_id && task.category_id !== "") ? parseInt(task.category_id) : null,
                parent_id: task.parent_id
            };

            fetch(`/api/tasks/${task.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(() => {
                this.fetchTasks();
            });
        },

        deleteTask(id) {
            if (confirm('Delete this task?')) {
                fetch(`/api/tasks/${id}`, { method: 'DELETE' })
                    .then(() => this.fetchTasks());
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
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return d.toLocaleDateString();
        }
    }
}
