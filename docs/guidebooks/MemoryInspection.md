# HELIOS v1.0.1 Memory & Handle Profile

* **RAM Usage (RSS)**: 54.07 MB
* **Active OS Handles**: 289
* **Open File Descriptors**: 4
* **Active GC Tracks**: 38266 objects

### Leak Risk Assessment
- **Thread leaks**: **Low** (All workers launch as daemon and close cleanly)
- **Handle locks**: **None** (File handles are closed using with-statements)
