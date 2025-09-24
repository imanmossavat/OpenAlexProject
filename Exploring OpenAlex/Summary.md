# OpenAlex Migration Report: Paper & Keyword Exploration

**Task:** Initial exploration of OpenAlex API capabilities for potential migration from Semantic Scholar

## Objective

This report evaluates OpenAlex as a replacement for Semantic Scholar by implementing a representative use case: starting from a seed paper, extracting metadata, and performing keyword matching across references and citations to assess feasibility for our existing pipeline.

## Implementation Overview

The exploration focused on SciBERT paper (https://openalex.org/w2970771982) using five keyword expressions related to scientific text processing, recommendations, question answering, RAG systems, and transformer models.

### Core Functionality Implemented

**Paper Metadata Extraction:**

- Successfully retrieved DOI, venue information, abstract, and citation counts
- Extracted all 35 references and 2,570 citing papers
- Reference retrieval: 100% success rate with optimized batch size (25 papers per batch)
batches of 25 papers for references and 100 for citations, 100 papers is the max for batches and 25 is used for references because anything higher than that will result in some paper losses.

**Keyword Matching System:**

- Implemented boolean logic for complex expressions (AND, OR operations)
- Searched across title, abstract, and concept fields
- Applied parallel processing for performance optimization

**Additional Query Capabilities:**

- Title-to-ID lookup functionality
- Author-based paper retrieval (by name or OpenAlex ID)

## Results Summary

**Reference Analysis:**

- Total references: 35 (all successfully retrieved)
- Keyword matches: 6 YES, 29 NO
- Match rate: 17.1% of references matched keywords

**Citation Analysis:**

- Total citing papers: 2,570
- Keyword matches: 815 YES, 1,755 NO
- Match rate: 32% of citing papers

**Performance Metrics:**

- Reference processing: ~0.5 seconds (parallelized)
- Citation processing: ~1.81 seconds (parallelized)
- Total runtime: ~0.2 minutes

## Key Observations: OpenAlex vs Semantic Scholar

### Advantages of OpenAlex

**API Access:** No API key requirements, eliminating rate limit barriers that plague our current S2 implementation.

**Data Completeness:** Comprehensive metadata including venues, concepts, and full citation networks. Abstract access through inverted index with automatic text reconstruction.

Important note: Not always is the metadata from OpenAlex complete, a lot of the papers I found don't have venues. Some don't even have titles or abstracts

**Scalability:** Efficient batch fetching and pagination support for large datasets. Parallel processing capabilities significantly improve throughput.

**Query Flexibility:** Support for filters including author searches, and concept-based queries.

### Limitations and Differences


**Metadata Variations:** Different field structures require pipeline refactoring. Venue information sometimes missing or inconsistent.

**Processing Requirements:** Text processing needed for inverted index abstracts, though PyAlex handles this automatically.


## Technical Implementation Notes

**Batch Processing:** Implemented 100-paper batches with 1-second delays for API politeness. This approach reduced API calls from 2,570 individual requests to approximately 26 batch requests.

**Parallel Processing:** Multiprocessing implementation achieved significant speedup for keyword matching across large paper collections.

**Error Handling:** Needs handling for missing data like titles, failed API calls.

## Recommendations

**Migration Feasibility:** OpenAlex presents a viable alternative to Semantic Scholar with good API and library accesibility and high rate limits.

**Required Adaptations:**

- Citation metadata handling is different from S2, so changes have to be made accordingly using the batch processing used in the files.
- Conversion methods have to be made since OpenAlex has different field names than S2

## Conclusion

OpenAlex demonstrates strong potential as a Semantic Scholar replacement, offering API access with high rate limits and comprehensive academic data. While some data coverage limitations exist, the benefits of eliminating API key constraints and rate limits outweigh the drawbacks for most use cases. The migration would require careful pipeline refactoring but appears technically feasible.