# JavaScript Stack Overflow Prevention

## Rule 1: React useEffect Infinite Loop Prevention
When using `useEffect` with state variables that change during the effect execution, be careful with dependency arrays to avoid infinite loops.

### Problem
Including state variables that are modified within the effect in the dependency array can cause infinite re-renders:

```typescript
// ❌ BAD - causes infinite loop
useEffect(() => {
  if (targetValue !== currentValue) {
    // Animation logic that updates currentValue
    setCurrentValue(newValue);
  }
}, [targetValue, currentValue]); // currentValue changes trigger new effect
```

### Solution
Only include external dependencies that should trigger the effect, not internal state that changes during execution:

```typescript
// ✅ GOOD - only external trigger
useEffect(() => {
  if (targetValue !== currentValue) {
    // Animation logic that updates currentValue
    setCurrentValue(newValue);
  }
}, [targetValue]); // only external changes trigger effect
```

## Rule 2: Large File Processing Stack Overflow Prevention
When processing large files (images, videos, etc.), avoid using spread operator with large arrays in function calls.

### Problem
Using spread operator with large Uint8Array can cause stack overflow:

```typescript
// ❌ BAD - causes stack overflow with large files
const uint8Array = new Uint8Array(content);
const binaryString = String.fromCharCode(...uint8Array); // Stack overflow!
```

### Solution
Process large arrays in chunks to avoid stack overflow:

```typescript
// ✅ GOOD - process in chunks
const uint8Array = new Uint8Array(content);
let binaryString = '';
const chunkSize = 8192; // 8KB chunks
for (let i = 0; i < uint8Array.length; i += chunkSize) {
  const chunk = uint8Array.slice(i, i + chunkSize);
  binaryString += String.fromCharCode(...chunk);
}
```

## Rule 3: Browser Storage Quota Management
Avoid storing large amounts of data in sessionStorage/localStorage to prevent QuotaExceededError.

### Problem
Storing large files as base64 in browser storage can exceed quota limits:

```typescript
// ❌ BAD - can exceed storage quota
const base64Content = btoa(binaryString);
sessionStorage.setItem("files", JSON.stringify({content: base64Content}));
```

### Solution
Use in-memory storage for large data and only store metadata in browser storage:

```typescript
// ✅ GOOD - use singleton pattern for in-memory storage
class FileStorage {
  private static instance: FileStorage;
  private fileList: FileList | null = null;

  public setFiles(files: FileList): void {
    this.fileList = files;
  }

  public getFiles(): FileList | null {
    return this.fileList;
  }
}

// Only store metadata
sessionStorage.setItem("fileInfo", JSON.stringify(metadata));
```

## When to Apply
- Animation effects that update state over time
- Effects that modify state variables included in their dependencies
- Any effect where internal state changes should not retrigger the effect
- File processing operations with potentially large files
- Any operation using spread operator with large arrays
- When storing large amounts of data between page navigations
- File upload/processing applications with large files
