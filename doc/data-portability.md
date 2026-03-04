# Data Portability & Backups

Sharpei is designed to keep your data safe and accessible. All your information is stored locally on your machine, and we provide several ways to back it up or move it between devices.

## Automated Backups

Sharpei automatically creates daily snapshots of your entire database.

- **Cadence**: A new backup is triggered automatically if the latest snapshot is older than **24 hours**.
- **Location**: Backups are stored in the `backups/` directory within your Sharpei installation folder.
- **Format**: Snapshots are full copies of your `sharpei.db` SQLite database file, timestamped for easy identification (e.g., `sharpei_backup_20250304_120000.db`).
- **Retention**: Sharpei keeps the **last 10 backups** and automatically cleans up older ones to save space.

## Manual Export/Import (JSON)

For migrating data between different Sharpei instances or for long-term archival in a human-readable format, you can use the JSON Export/Import feature.

### Exporting Data
1. Open the **Settings** panel (gear icon in the top right).
2. Click **Export to JSON**.
3. A file named `sharpei_export_YYYY-MM-DD.json` will be downloaded to your computer.

### Importing Data
1. Open the **Settings** panel.
2. Click **Import from JSON**.
3. Select a previously exported Sharpei JSON file.
4. **Warning**: Importing data will **completely replace** your current tasks and categories. A confirmation dialog will appear before the process begins.

## Advanced: Accessing the Database Directly

Since Sharpei uses SQLite, you can open your `sharpei.db` file with any SQLite browser or tool. This makes it easy to:
- Write custom scripts to process your tasks.
- Integrate Sharpei data with other local AI agents.
- Perform advanced bulk edits using SQL.
