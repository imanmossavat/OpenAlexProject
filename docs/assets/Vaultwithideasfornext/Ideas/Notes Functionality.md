	 
---

# Notes Full Functionality

## Overview

Notes should be tightly integrated into the crawler output so each paper automatically includes a link to its associated notes file. Users should be able to browse the papers inside a vault and create or edit notes directly in the web app. Notes should be stored as simple, flexible markdown files. This document outlines the structure, behavior, and recommended UI/UX for the notes system.

---

# How Notes Should Work

The crawler generates a vault containing:

- `/papers/` — one markdown file per paper
    
- `/notes/` — empty or partially populated initially
    
- built-in links from each paper to its (future) note file
    

Notes are not required to exist yet. The paper file simply points to where the note _will_ be stored.

---

# Crawler Paper Output (Example)

Each paper file includes:

1. **YAML frontmatter** with metadata
    
2. **Readable markdown content**
    
3. **A “Notes” section linking to the note file**
    

Example:

```markdown
---
paper_id: W3049136412
title: Characterising the application of the "progressive overload" principle…
authors:
  - id: A5012997122
    name: Alaa Khushhal
  - id: A5081514534
    name: Simon Nichols
year: 2020
venue: PLoS ONE
doi: 10.1371/journal.pone.0237197
url: https://openalex.org/W3049136412
abstract: The key exercise training principle...
concepts:
  - id: https://openalex.org/C2778818304
    display_name: Rehabilitation
fields:
  - id: https://openalex.org/C1862650
    display_name: Physical therapy
domains:
  - id: https://openalex.org/C71924100
    display_name: Medicine
---

# Characterising the Application…

> [!info] Paper Info  
> **Authors:** …  
> **Year:** 2020 | **Venue:** PLoS ONE  
> **DOI:** 10.1371/journal.pone.0237197  
> **OpenAlex:** W3049136412

## Abstract
…

---

> [!abstract] Research Context  
> **Top Concepts:** Rehabilitation • Training (meteorology)  
> **Fields:** Physical therapy  
> **Domains:** Medicine, Physics  

## Notes
> [!note] My Notes  
> The notes for this paper can be found here:  
> [[notes/W3049136412_Notes]]
```

---

# Notes File Format

Notes live in:

**`/notes/<paper_id>_Notes.md`**

Minimal recommended template:

```markdown
---
paper_id: W3049136412
linked_paper: ../papers/W3049136412
---

# Notes for W3049136412

## Personal Notes
Write your notes here…
```

This keeps notes flexible and user-driven.

No predefined structure.  
Users control their own formatting.

---

# How Notes Work in the Web App

Below is the recommended data flow and behavior.

---

## 1. Load Vaults

When the web app starts:

- auto-detect vaults in the default directory
    
- or allow the user to browse and select a vault
    

After selecting a vault:

### Load ONLY:

- `/papers/` directory
    
- extract YAML metadata
    
- build a list of papers (title, authors, venue, year, etc.)
    

### Do NOT load:

- `/notes/` directory at this stage
    
- any notes files upfront
    

### Why?

- most papers won't be opened
    
- notes can be large
    
- loading hundreds of markdown files wastes CPU and memory
    
- improves initial load time dramatically
    

This is known as **lazy loading**.

---

## 2. Browse Papers

The UI displays:

- list of all papers
    
- search/filtering options
    
- click to open a paper
    

This should be fast because only metadata was loaded, not full content of all notes.

---

## 3. Open a Paper (Lazy Loading the Note)

When the user selects a paper:

### The app should:

1. Read the markdown for that paper
    
2. Parse frontmatter + content
    
3. Look for the note file:
    
    - `notes/<paper_id>_Notes.md`
        

### If the note file exists:

- read it from disk
    
- render it with markdown preview
    

### If the note file does NOT exist:

- show a button:  
    **“Create Notes File”**
    
- clicking the button generates the template automatically
    

This keeps everything efficient.

---

# Notes Creation & Editing

### Requirements:

- Markdown editor
    
- Live preview
    
- Autosave
    
- Stored locally in the vault
    
- File path: `notes/<paper_id>_Notes.md`
    

### Editor Recommendations:

- **React Markdown + CodeMirror** (simple + reliable)
    
- **TipTap with Markdown extension** (rich, Obsidian-like)
    
- **Monaco Editor** (VS Code experience)
    

### Why Markdown?

Markdown is the best option because:

- Works perfectly with Obsidian-style vaults
    
- NotebookLM reads markdown and YAML frontmatter well
    
- Human-readable
    
- Portable across systems
    
- Supports links, citations, admonitions, and formatting
    

No proprietary note format is needed.

---

# Notes Linking Behavior

When a note is created:

- the crawler’s original paper link (`[[notes/<id>_Notes]]`) becomes active
    
- the note file can link back to the paper if desired
    
- bi-directional linking isn’t required, but can be added later
    

---

# Summary

To implement full notes functionality:

### Crawler:

- generates paper markdown files with links to notes
    
- places notes in `/notes/` folder
    
- no notes are required to exist yet
    

### Web App:

- loads only papers at startup (efficient)
    
- loads notes **only when the user opens a paper**
    
- provides a markdown editor for note creation
    
- saves notes back to the vault
    
- ensures good NotebookLM + vault integration
    

---
