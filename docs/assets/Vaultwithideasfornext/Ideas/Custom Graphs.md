
---

# Custom Graphs

## Overview

Beyond exporting citation graphs to VOSviewer, the system should provide a **fully interactive custom graph** directly inside the web app. This graph allows users to explore relationships between papers, authors, venues, and citations in a dynamic, mindmap-like interface — similar to a skill tree in games.

The graph starts with a selected node (e.g., a venue), and users can **expand outward** by clicking nodes to reveal their connected neighbors (±1 depth). This makes visual exploration intuitive and controlled, avoiding graph clutter.

---

# Goal

Enable users to:

- Click any venue, paper, or author
    
- See its immediate neighbors (±1 depth)
    
- Click those neighbors to expand further
    
- Navigate academic networks like a skill tree
    
- Explore the literature graph interactively, without visual overload
    

The result is a **zoom-in, zoom-out, expand-as-you-go exploration tool**, deeply integrated into your research workflow.

---

# Why Custom Graphs Are Useful

This feature allows:

- Exploration of citation connections
    
- Seeing how authors connect to papers
    
- Viewing venue-focused subgraphs
    
- Topic-cluster exploration
    
- Following citation chains step by step
    
- Insight into local neighborhoods rather than whole datasets
    

Users can follow literature paths manually:

> Paper → Authors → Other Papers → Venues → Dominant Topic → Citation Trails

This mimics an academic "skill tree" that grows as the user explores.

---

# Behavior

## Starting point

The graph starts at a specific node type:

- Venue
    
- Paper
    
- Author
    
- Topic
    
- Concept
    

User clicks to open “Custom Graph View” for that node.

---

## Expansion Logic

When the graph loads:

- Show the selected node in the center
    
- Show its **immediate neighbors** (±1 depth)
    
    - For a venue:
        
        - papers published in that venue
            
        - top authors associated with it
            
    - For a paper:
        
        - authors
            
        - citations
            
        - references
            
        - venue
            
    - For an author:
        
        - authored papers
            
        - co-authors
            

User can then:

1. Click any node
    
2. The graph expands by loading that node’s neighbors
    
3. New nodes appear in the graph
    
4. Graph adjusts via physics layout
    

This is identical to:

- Obsidian graph view expansion
    
- A mindmap
    
- A videogame skill tree
    

---

# Node Types & Their Connections

### Paper node

- Links to authors
    
- Links to venue
    
- Links to referenced papers
    
- Links to citations
    

### Author node

- Links to authored papers
    
- Links to co-authors (optional)
    

### Venue node

- Links to papers (limit to top N papers to avoid clutter)
    
- Link to top authors for that venue
    

### Topic/Concept node (optional extension)

- Links to papers in that topic
    

### Behavior rule:

Only show a manageable number of neighbors (limit per type).  
The user can expand deeper by clicking nodes.

---

# Graph Style

The interface should feel like:

- A **mindmap**, where nodes expand when selected
    
- A **skill tree**, where users choose which branches to open
    
- An **interactive network**, with physics and smooth animations
    

Recommended styling:

- Papers → circle
    
- Authors → square
    
- Venues → diamond
    
- Topics → hexagon
    

Colors can represent node type.

---

# Recommended Library: vis-network

For this feature, **vis-network is ideal** because it supports:

- Dynamic addition and removal of nodes
    
- Physics-based layout
    
- Node-click events
    
- Clustering
    
- Smooth expansion animations
    
- Graph stabilization
    
- Good performance for medium-sized literature graphs
    

Users will be able to click a node and instantly see the graph expand around it.

---

# Backend Logic (FastAPI)

FastAPI endpoint:

```
GET /graph/node/{id}
```

What it returns:

- The selected node’s metadata
    
- The immediate neighbors (papers, authors, citations, venue, etc.)
    
- Nodes and edges formatted as JSON for vis-network
    

Example response format:

```json
{
  "nodes": [
    { "id": "V123", "label": "PLOS ONE", "type": "venue" },
    { "id": "W456", "label": "Paper A", "type": "paper" },
    { "id": "A789", "label": "Jane Doe", "type": "author" }
  ],
  "edges": [
    { "from": "V123", "to": "W456", "type": "published_in" },
    { "from": "A789", "to": "W456", "type": "author_of" }
  ]
}
```

This endpoint is called each time the user expands a node.

---

# Frontend Logic (React)

When the user clicks a node:

1. React calls `/graph/node/{id}`
    
2. Backend returns neighbors
    
3. vis-network adds the new nodes and edges
    
4. The graph rebounds and stabilizes
    
5. User continues exploring
    

This creates a “living” academic graph.

---

# Limiting Expansion to Prevent Noise

To prevent the graph from becoming overwhelming:

- Limit neighbors per node type (e.g., max 15 papers per venue)
    
- Introduce pagination for papers (optional)
    
- Allow collapsing a node after expansion
    
- Only expand when user clicks; never auto-expand
    

These controls keep the graph usable.

---

# Example User Flow

1. User opens a venue: **PLOS ONE**
    
2. Graph shows:
    
    - PLOS ONE → top 10 papers
        
    - PLOS ONE → top authors
        
3. User clicks a paper: **“Cardiac Rehab Study”**
    
4. Graph expands:
    
    - Paper → authors
        
    - Paper → citations
        
    - Paper → references
        
    - Paper → venue
        
5. User clicks an author: **“Alaa Khushhal”**
    
6. Graph expands:
    
    - Author → authored papers
        
    - Author → co-authors
        

They can explore endlessly.

---

# Summary

A **Custom Graph View** inside the web app allows users to navigate academic relationships like a skill tree:

- Start with any node type
    
- Expand outward by ±1 neighbors
    
- Click to reveal deeper layers
    
- Style and structure similar to the mindmap feature
    
- Powered by vis-network and backend neighbor queries
    

This is the most intuitive and powerful way for users to explore their crawled literature datasets.

---
