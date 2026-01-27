
---

# Why Automatic Phone PDF Scanning Is Not Possible or Reliable

## 1. Phones Do Not Expose Real Filesystems

### Android (MTP)

- Android devices use MTP (Media Transfer Protocol) when connected by USB.
    
- MTP is not a filesystem and does not provide real file paths.
    
- Paths shown in Windows Explorer (e.g., `This PC\Phone\Internal Storage`) are virtual shell locations, not directories on disk.
    
- There is no mount point and no drive letter (such as `D:\` or `E:\`) that applications can access.
    

### iOS (iPhone)

- iPhones do not expose any filesystem to a computer.
    
- Only photos and videos are available via the Windows "Apple Mobile Device" interface.
    
- No app data, PDFs, Downloads, Files App content, or document storage is accessible.
    
- iPhones cannot be browsed like a drive under any circumstance.
    

## 2. File Pickers Cannot Select Phone Storage

- Windows file/folder dialogs, Electron file pickers, TK/Qt dialogs, and browser file inputs cannot return MTP or iOS storage paths.
    
- “Internal shared storage” appears in Explorer only as a visual abstraction.
    
- Selecting it in the UI does not correspond to a real filesystem path that code can use.
    

## 3. Python Cannot Traverse Phone Storage

- Standard Python filesystem functions (`os.walk`, `pathlib`, `glob`, etc.) do not work because MTP does not support real directory structures.
    
- iOS devices do not support these operations at all.
    
- Traversal would require low-level MTP protocol access, not filesystem access.
    

## 4. MTP Directories and Files Are Virtual Objects

- MTP exposes objects with IDs, not actual files or folders.
    
- Directory structures are emulated by Explorer and do not reflect real paths.
    
- Many internal folders cannot be read, listed, or traversed through programmatic APIs.
    
- Phone object IDs may change each time the device reconnects.
    

## 5. Unstable and Inconsistent Across Devices

- Different vendors (Samsung, Xiaomi, Oppo, OnePlus, etc.) implement MTP differently.
    
- Some devices block access to certain folders or file types.
    
- Screen locking often breaks the MTP session.
    
- Transfer operations are slow and prone to timeouts.
    
- iOS has no cross-device differences because storage access is not permitted at all.
    

## 6. No Cross-Platform Reliability

- Windows uses a shell namespace extension for MTP.
    
- macOS requires Android File Transfer or MTP clients, which behave differently and often break.
    
- Linux uses GVFS-MTP with non-standard paths and limited API support.
    
- No consistent method exists that works the same way across all platforms.
    

## 7. Impossible to Build a General, User-Friendly Solution

- Users cannot provide a usable path because phone storage is not exposed as one.
    
- Code cannot perform recursive scanning because no real directory tree exists.
    
- Any attempt would require custom MTP protocol handling, vendor-specific logic, and extremely brittle code.
    
- iOS cannot be scanned under any circumstances.
    
- Android can only be scanned unreliably, slowly, and with inconsistent results.
    

---