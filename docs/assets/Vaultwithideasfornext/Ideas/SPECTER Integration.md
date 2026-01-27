
---

# Semantic Academic Search Using SPECTER2 and OpenAlex

## Full Feasibility and Implementation Guide (Local, Single-User, Session-Based)

---

# 1. Overview

This document describes how to implement semantic academic search using OpenAlex for data retrieval and SPECTER2 for embedding and semantic ranking.

The design targets:

- Local execution
    
- Single-user workflow
    
- No persistent database
    
- No shared backend
    
- No long-term corpus storage
    

Data and embeddings are held in memory for the duration of the session and cleared when the session.

---

# 2. Model Requirements

## SPECTER2 Model

- Recommended: `allenai/specter2_base`
    
- Size: ~420–480 MB
    
- Embedding size: 768 dimensions
    
- Runtime memory: ~1.5–2 GB
    

Automatically downloaded on first use via HuggingFace.

## Runtime Environment

- Python 3.9+
    
- PyTorch (CPU or CUDA)
    
- HuggingFace Transformers
    
- Optional GPU for faster embedding
    

---

# 3. Data Requirements

SPECTER2 embeds text only.  
All paper data is fetched dynamically from OpenAlex at query time.

Fields retrieved from OpenAlex:

- Title
    
- Abstract
    
- Year
    
- Venue
    
- Concepts
    
- IDs and metadata
    

No long-term local corpus is maintained.

---

# 4. Architecture Overview

Since the application is local and single-user, the entire workflow stays in memory:

1. User enters a natural-language query.
    
2. The application generates keywords.
    
3. The application fetches candidate papers from OpenAlex.
    
4. Papers are stored in a pandas DataFrame for the entire session.
    
5. SPECTER2 embeddings are computed and stored in the DataFrame.
    
6. The query itself is embedded.
    
7. Cosine similarity ranking is performed.
    
8. Results are displayed.
    
9. The DataFrame remains available for the user to explore.
    
10. Session data is cleared when the session ends or user closes the app.
    

---

# 5. Query Flow (Session-Based)

All steps below are automatic except the initial user query.

## Step 1. User Input

The user provides any natural-language query.  
No structured input is required.

## Step 2. Keyword Extraction (Automatic)

Purpose: Convert natural-language queries into terms suitable for OpenAlex.

Procedure:

- Extract noun phrases (spaCy or similar).
    
- Remove stopwords.
    
- Select 3–8 relevant terms.
    

These terms form an OpenAlex search query.

## Step 3. Candidate Retrieval from OpenAlex (Automatic)

Example search:

`search=title_and_abstract:(prediction AND fertilizer AND application)`

Typical result set:

- 300–500 papers
    

This is the candidate pool for semantic re-ranking.

## Step 4. Create a Session DataFrame (Automatic)

For each paper, store:

- id
    
- title
    
- abstract
    
- year
    
- venue
    
- concepts
    
- embedding (initially empty)
    

The DataFrame persists for the entire session.

## Step 5. Embed Papers with SPECTER2 (Automatic)

Batch-embed all paper texts:

`title + ". " + abstract`

Batch sizes of 16–64 are recommended.  
Embeddings are stored as numpy arrays in a DataFrame column.

## Step 6. Embed User Query (Automatic)

Embed the user’s complete query string using SPECTER2.  
This produces a 768-dimensional vector consistent with paper embeddings.

## Step 7. Compute Cosine Similarity (Automatic)

Compute similarities between the query embedding and all paper embeddings.

Store results in:

`df["similarity"]`

## Step 8. Rank and Filter (Automatic and User-Interactive)

Sort papers by similarity:

`df.sort_values("similarity", ascending=False)`

Because the DataFrame persists through the session, the user may:

- Filter by year
    
- Filter by venue
    
- Filter by concepts
    
- Re-sort
    
- Drill into details
    

No recomputation is required after embedding.

## Step 9. Display Top Results

Return top-N ranked papers, including:

- title
    
- key metadata
    
- abstract snippet
    
- similarity score (optional)
    
- external links
    

## Step 10. Persist Results for the Entire Session

The DataFrame containing:

- metadata
    
- embeddings
    
- similarity scores
    

remains in memory until:

- the user runs a new query,
    
- explicitly resets the session,
    
- or closes the application.
    

---

# 6. Why a pandas DataFrame Is Ideal for This Architecture

- Stores 300–1000 papers efficiently in memory
    
- Holds numpy embeddings directly in cells
    
- Fast filtering and sorting
    
- Simple integration with vectorized cosine similarity
    
- Zero setup overhead
    
- Perfect for temporary, in-session data
    
- No persistence required
    
- Extremely lightweight compared to vector databases or SQL systems
    

This matches the local, stateless, session-based design precisely.


---

# 8. Limitations

- The runtime depends on the number of candidate papers.
    
- SPECTER2 uses only titles and abstracts, not full PDFs.
    
- OpenAlex must return relevant candidates for the semantic ranking to be effective.
    
- Large candidate sets (1000+) increase embedding time.
    

These constraints are consistent with in-memory, session-based design.

---

# 9. Summary

For a local, single-user, stateless application:

- A pandas DataFrame is the optimal structure for storing paper metadata, embeddings, and similarity scores.
    
- The entire query retrieval and re-ranking pipeline runs in memory.
    
- SPECTER2 provides powerful semantic matching with no training.
    
- OpenAlex provides high-recall candidate retrieval.
    
- Results and embeddings persist only for the duration of the session.
    
- No database, vector index, or disk persistence is required.
    

This approach is simple, performant, and aligns with your intended architecture.

---