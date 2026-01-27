
---
# Why a Web Frontend Cannot Show the Absolute Path of an Uploaded File

## Overview

Modern web browsers do not allow websites to access the absolute file paths of files selected or uploaded by a user. This limitation applies regardless of whether the application is running locally or over the internet.

## Reason

This restriction exists for security and privacy. If browsers exposed absolute file paths, websites could gain sensitive information about a user's system, such as:

- The user's operating system structure
    
- The username of the logged-in OS account
    
- Names of personal folders (e.g., “Documents”, “Medical”, “Taxes2025”)
    
- Internal drive structure
    

This information could be used for fingerprinting, profiling, or malicious targeting. To prevent this, browsers sanitize file inputs before sending them to JavaScript or to the backend.

## What the Browser Provides Instead

When a user selects a file, the browser gives the frontend only:

- The file name (e.g., `example.pdf`)
    
- The file size
    
- The file type
    
- The file contents
    

It does **not** provide the full local path. The original path is removed before the file is made available to frontend code.

## Backend Limitation

Because the frontend never receives the absolute path, it cannot send it to the backend. Therefore, the backend also cannot know the user's original file path.

## Summary

- Browsers intentionally hide absolute file paths for security.
    
- Web applications only receive file metadata and contents.
    
- The original filesystem path on the user's device is never exposed.
    
- This behavior cannot be bypassed or disabled.
    

---

# Additional Note: Using a Manually Typed Absolute Path (Local Backend Only)

In a scenario where the backend is running locally on the user's own machine, there is one exception:

If the user **manually types an absolute folder path** into a text field on the frontend (for example:  
`C:/Users/Me/Documents/MyAppFolder`), this value is treated simply as user-provided text.

Because the backend is running on the same computer, it can:

- Receive the typed folder path from the frontend  
- Combine that path with the filename of the uploaded file  
- Access and open files located in that folder  

This works **only because the user voluntarily specifies the path** and the backend is installed on the same machine with permission to read that location.

Importantly:

- The browser still does **not** reveal the original location where the file came from.  
- The user must explicitly provide a folder path.  
- This method allows the backend to **open files that are already stored in the folder the user specified**, but it does **not** grant access to the user’s private folders automatically.  
- This does **not** bypass any browser security rules, because the browser is not providing the path—**the user is**.

In short:  
**A local backend can open files from a folder path only if the user manually types that path and intentionally grants access to it.**

---

# How the Application Handles Uploaded Files (Current Implementation)

To allow the backend to open and work with uploaded files, the application copies each uploaded file into a temporary folder that the backend controls. This approach is **safe**, **reliable**, and follows standard patterns used in document-processing systems.

## What the Application Does

1. **When the user uploads files:**  
   - The backend saves copies of those files into a dedicated temporary directory created for that session.

2. **The backend opens and processes those temporary copies**  
   (not the original files on the user's computer).

3. **Once the use case is completed:**  
   - The application automatically deletes all temporary files created for that session.

4. **On application startup:**  
   - The system checks all temporary folders.
   - If a folder is **older than 48 hours**, it is automatically removed.

## Why This Approach Is Good

- ✔ **Prevents disk bloat** even if users upload many documents  
- ✔ **Ensures privacy**, since files are removed after use  
- ✔ **No leftover documents** remain on the user’s system  
- ✔ **Reliable fallback cleanup** if the session ends unexpectedly  
- ✔ **Industry-standard practice** in OCR apps, scanning tools, and document processors  
- ✔ **Safer than trying to access the user’s original folders**

This method ensures the backend only works with files it explicitly stores and controls, without needing to know or access the user's private file paths.

## What If the User Uploads Many Documents?

The cleanup system already addresses this:

- Session files are deleted immediately after processing.
- Old temporary folders are deleted automatically on startup.
- This prevents unlimited growth of storage usage.
- It ensures the application remains fast and lightweight.

---