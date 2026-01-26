
---

# Citation Graphs

## Overview

After the crawler finishes, users should be able to generate **citation graphs** that visualize relationships between:

- Papers
    
- Authors
    
- (Optionally) the top _N_ most important venues
    

There are two main approaches:

1. **Export to VOSviewer** (fastest, lowest engineering effort)
    
2. **Build an interactive visualization inside the web app** (more advanced)
    

Since the crawler already uses **OpenAlex**, generating VOSviewer-compatible export files is simple because VOSviewer natively supports OpenAlex identifiers and metadata.

This feature helps users explore influence networks, collaboration clusters, and structural connections in the crawled dataset.

---

# Why Citation Graphs Matter

Citation graphs reveal:

- which papers are highly influential
    
- which authors collaborate in a field
    
- how papers are connected through citation chains
    
- dense clusters vs. isolated works
    
- venue-specific research patterns
    

This adds a powerful knowledge-exploration capability after running the crawler.

---

# What Data We Already Have From the Crawler

Because the crawler pulls metadata from **OpenAlex**, every paper already includes:

- `paper_id` (OpenAlex Work ID, e.g., `W12345`)
    
- `title`
    
- `authors` (OpenAlex Author IDs)
    
- `referenced_works` (citations)
    
- `venue` (OpenAlex Venue ID + name)
    
- `year`
    
- `topics / concepts`
    

This is the data VOSviewer expects.

This makes VOSviewer integration easier.

---

# Option 1 — Export to VOSviewer (Recommended Phase 1)

## Why this is easy

VOSviewer already supports:

- OpenAlex paper IDs
    
- OpenAlex author IDs
    
- Citation networks
    
- Co-authorship networks
    
- Bibliometric mappings
    

The crawler already outputs everything needed.

### ✔ No data transformation

### ✔ No complex graph algorithms

### ✔ Users instantly get interactive visualization

---

## VOSviewer Export Format

VOSviewer works best when given **two CSV files**:

### 1. **Nodes file (items.csv)**

Columns:

```
id,label,type
```

Example:

```
W3049136412,Progressive Overload in Cardiac Rehab,paper
A5012997122,Alaa Khushhal,author
V19876,PLOS ONE,venue
```

### 2. **Edges file (links.csv)**

Columns:

```
source,target,type
```

Example:

```
W3049136412,W1234567890,cites
A5012997122,W3049136412,author_of
W3049136412,V19876,published_in
```

### Note on venues

To avoid clutter:

- Only include **top N venues**
    
- Determined by number of papers in the dataset
    
- Skip minor or low-frequency venues
    
- Still fully VOSviewer-compatible
    

---

## FastAPI Backend Implementation

### Endpoint

```
GET /export/citation-graph/vosviewer
```

### What it does

1. Load crawler results
    
2. Generate `items.csv` and `links.csv`
    
3. Zip them
    
4. Return as a downloadable file
    


---

## React Frontend Integration

Add a button:

```
Export Citation Graph (VOSviewer)
```

Click → triggers backend download.

The user then opens the ZIP in VOSviewer.

---

# Option 2 — Build a Custom Interactive Graph (Phase 2)

This is more advanced, and useful if you want:

- clicking nodes to open the paper’s details page
    
- integration with notes
    
- topic-based coloring
    
- dynamic filtering inside your web app
    
- expandable graph neighborhoods (mindmap style)
    

### Tech Choices for React

#### ⭐ Recommended: `vis-network`

- Easy to use
    
- Great for citation networks
    
- Physics simulation
    
- Click events
    
- Good performance
    

#### Other options:

- Cytoscape.js (powerful, heavier)
    
- D3.js (maximum flexibility, maximum effort)
    

### Backend (FastAPI)

Use **NetworkX** to construct graph structure and output as JSON.

Graph JSON format example:

```json
{
  "nodes": [
    { "id": "W3049136412", "label": "Paper A", "type": "paper" },
    { "id": "A5012997122", "label": "Author X", "type": "author" },
    { "id": "V9012", "label": "PLOS ONE", "type": "venue" }
  ],
  "edges": [
    { "from": "W3049136412", "to": "W12345", "type": "cites" },
    { "from": "A5012997122", "to": "W3049136412", "type": "author_of" },
    { "from": "W3049136412", "to": "V9012", "type": "published_in" }
  ]
}
```

React renders the graph with node-click functionality.

---

# Showing Only Top N Venues

To reduce clutter:

1. Count number of papers per venue
    
2. Sort descending
    
3. Select top _N_ (e.g., 5 or 10)
    
4. Include only those venue nodes
    
5. Skip venue connections for others
    

This keeps the graph readable while still showing important venue relationships.

---

# Feasibility Table

|Approach|Difficulty|Pros|Cons|
|---|---|---|---|---|
|**VOSviewer Export**|Easy|Fastest, uses OpenAlex support|External app required|
|**Custom React Graph**|Medium–High|Integrated, interactive, clickable|More engineering|

---

# Recommended Implementation Path

### Phase 1 — VOSviewer Export (Quick Win)

- Generate `items.csv` + `links.csv`
    
- Add download button
    
- Immediate citation graph capability
    
- Uses existing OpenAlex crawler metadata
    

### Phase 2 — Build Your Own Interactive Graph

- `/citation-graph` page in your app
    
- vis-network, clickable nodes, dynamic expansion
    
- Perfect for integrating with notes, topics, filtering
    


---
