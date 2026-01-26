
---

# Metadata & Topic Labeling Improvements Proposal

## Overview

The current system successfully crawls metadata from OpenAlex and groups papers into topics, but several limitations reduce usability. This document outlines three core issues and provides detailed improvement plans, including how to integrate topic labeling directly into the crawler and how to generate semantic topic names using local AI models.

---

# Issue 1: Missing Open Access Metadata

**Impact:** High  
**User Pain:** Users must manually check accessibility for 100+ venues and papers.  
**Fix:** Add OpenAlex `is_oa`, `oa_status`, and `oa_url` fields to paper metadata.

## Details

OpenAlex provides rich Open Access (OA) metadata, but these fields are currently not included in the crawler output. Incorporating them will allow users to immediately see whether a paper is accessible without paywalls.

### Required Fields

- `is_oa` — whether the paper is Open Access
    
- `oa_status` — gold, green, hybrid, bronze
    
- `oa_url` — direct link to legal full text
    

### Implementation Plan

- Extend metadata extraction to include OA fields.
    
- Add these fields to:
    
    - paper metadata objects
        
    - venue accessibility outputs
        
    - exported vault markdown
        

### User Benefit

Instant visibility into whether a paper can be read, removing the need for manual checks.

---

# Issue 2: Generic Topic Labels

**Impact:** Medium  
**User Pain:** Users must manually interpret 20+ topics using only keywords.  
**Fix:** Automatically generate semantic topic labels.

## Summary

Topic assignment currently works, but labels such as “Topic 0” or “Topic 1” are difficult to understand. A labeling system exists, but it is currently a **separate use case** and is not integrated into the crawler. The labeling step must be merged into the crawler so topics receive final names during the crawl.

---

# How Topic Assignment Works Today

_(Currently separate — must be integrated into the crawler)_

### Step 1 — Topic Model Generates Probabilities

The crawler runs an LDA or NMF model, producing probability scores for each paper across all topics.

Example for Paper A:

- Topic 0: 0.70
    
- Topic 1: 0.20
    
- Topic 2: 0.10
    

Paper A → Topic 0.

### Step 2 — Papers Are Grouped by Topic

Examples:

- Topic 0 → Papers A, D, E
    
- Topic 1 → Papers B, F
    
- Topic 2 → Papers C, H, I
    

### Step 3 — Current Labeling Uses OpenAlex Concepts

1. Gather all papers in a topic
    
2. Collect their OpenAlex concept tags
    
3. Count most common concepts
    
4. Use top 1–2 concepts as topic name
    

Example:  
Topic 0 → “Deep Learning & Neural Networks”

### Important Note

This process is **currently separate** from the crawler pipeline.  
It must be moved **into** the crawler so topics are labeled during metadata generation.

---

# Improved Topic Labeling Approaches

The goal is to keep the crawler’s topic groups but replace the generic labels with semantic names generated automatically.

All approaches below **use the topics created by the crawler**.  
Nothing changes about the topic model — only the naming step is improved.

---

## Option A — LLM-Based Label Generation

(External API or local LLM)

### How It Works

- Provide top OpenAlex concepts
    
- Provide topic model keywords
    
- Provide representative paper titles or abstracts
    
- Ask the LLM to generate a short topic name
    

### Example Output

> “Machine Learning for Crop Yield Prediction”

### Pros

- Best quality labels
    
- Human-like and context-aware
    

### Cons

- Requires LLM
    
- Higher latency
    

---

## Option B — Semantic Labeling Using Local Embedding Models

_(AI inside the app, no external LLM)_

This approach uses embedding models (like Specter or SentenceTransformers) to compute semantic similarity between concepts, keywords, and paper titles.

### Models to Use

- **Specter / Specter2** — optimized for scientific papers
    
- **Sentence-BERT (MiniLM or MPNet)** — fast and accurate
    

### How It Works

#### Step 1 — Generate embeddings for:

- Topic model keywords
    
- Paper titles in this topic
    
- OpenAlex concepts
    

#### Step 2 — Cluster embeddings inside each topic

Use KMeans or Agglomerative Clustering to find the dominant semantic cluster.

#### Step 3 — Identify centroid

Choose the concept/keyword closest to the centroid.

#### Step 4 — Combine top 1–2 elements

Form a short descriptive title.

### Example Output

> “Computer Vision for Agricultural Monitoring”

### Pros

- Runs fully offline
    
- No dependency on GPT
    
- Stable and deterministic
    

### Cons

- Less human-like than LLM labels
    

---

## Option C — Small In-App Text Generation Model

_(Local AI text generator, still no external LLM)_

Use a small sequence-to-sequence model (like FLAN-T5-Small or DistilT5) embedded in the app.

### How It Works

#### Step 1 — Build a small input prompt:

```
Concepts: Deep Learning, Neural Network
Keywords: agriculture, crop yield
Paper Titles:
 - "Deep Learning for Crop Yield Prediction"
 - "Neural Networks for Agricultural Imaging"

Generate a short topic title:
```

#### Step 2 — The model generates a label:

> “Deep Learning in Agricultural Imaging”

#### Step 3 — Apply cleanup rules:

- Limit to 4–8 words
    
- Capitalize
    
- Remove filler words
    

### Pros

- Human-like labels
    
- Fully offline
    
- Small models run fast on CPU
    

### Cons

- Less accurate than GPT-4
    
- Slightly more integration work
    

---

# Integration Into the Crawler

To unify the pipeline, the crawler should perform:


1. Run topic modeling
    
2. Assign papers to topics
    
3. Run improved label generator (Option A, B, or C)
    
4. Write results to vault
    

This makes the crawler a single, self-contained process.

---

# Issue 3: No Source URL Export

**Impact:** High  
**User Pain:** Users must manually copy URLs to import into NotebookLM.  
**Fix:** Add a “Export URLs” feature.

## Details

NotebookLM and other AI tools require direct lists of URLs to ingest documents. The current system forces users to copy-paste manually.

### How to Implement

#### Option A — Add URLs to Metadata

Include:

- `openalex_url`
    
- `pdf_url` (from OA metadata)
    
- `publisher_url`
    

#### Option B — Create a Vault Export File

Generate a file such as `source_urls.md` or `source_urls.txt`:

```
# Source URLs Export
- Paper A: https://openalex.org/W12345
- Paper B: https://openalex.org/W56789
- Venue X: https://openalex.org/V112233
```

#### Option C — Add UI Button

A button: **“Export for NotebookLM”**  
Downloads a `.txt` or `.md` containing all URLs.

### User Benefit

One-click import into NotebookLM.

---

# Summary of Suggested Improvements

## 1. Add Open Access Metadata

- Add `is_oa`, `oa_status`, `oa_url`
    
- Add `access_type` for venues
    
- **User Benefit:** Instantly know which papers are readable
    

## 2. Export Source URLs Feature

- Create export file
    
- Add button to UI
    
- **User Benefit:** Simplifies NotebookLM usage
    

## 3. Improved Topic Labeling

Replace “Topic 0 / Topic 1” with meaningful names like:

> “Machine Learning in Agriculture”

- **User Benefit:** Immediate understanding of each group of papers
    

---