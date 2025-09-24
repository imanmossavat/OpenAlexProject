import pyalex
from pyalex import Works
import time
from multiprocessing import Pool, cpu_count
from functools import partial

# Configure pyalex
pyalex.config.email = "885585@fontys.nl"

# Configuration
SEED_PAPER_ID = "https://openalex.org/w2970771982"
KEYWORDS = [
    "(science OR scientific) AND ((summary AND generation) OR summarization)",
    "(science OR scientific) AND (recommendation OR (recommend OR recommender))",
    "(scientific AND question AND answering)",
    "(scientific AND ((retrieval AND (augmented AND generation)) OR RAG))",
    "(science OR scientific) AND (BERT OR (transformer OR (embedding OR embeddings)))",
]

def simple_keyword_match(text, keywords):
    """Check if text matches any of the keyword expressions"""
    if not text:
        return False
    
    text = text.lower()
    
    # Check each expression - if ANY matches, return True
    
    # 1. "(science OR scientific) AND ((summary AND generation) OR summarization)"
    if ("science" in text or "scientific" in text) and (("summary" in text and "generation" in text) or "summarization" in text):
        return True
    
    # 2. "(science OR scientific) AND (recommendation OR (recommend OR recommender))"
    if ("science" in text or "scientific" in text) and ("recommendation" in text or "recommend" in text or "recommender" in text):
        return True
    
    # 3. "(scientific AND question AND answering)"
    if "scientific" in text and "question" in text and "answering" in text:
        return True
    
    # 4. "(scientific AND ((retrieval AND (augmented AND generation)) OR RAG))"
    if "scientific" in text and (("retrieval" in text and "augmented" in text and "generation" in text) or "rag" in text):
        return True
    
    # 5. "(science OR scientific) AND (BERT OR (transformer OR (embedding OR embeddings)))"
    if ("science" in text or "scientific" in text) and ("bert" in text or "transformer" in text or "embedding" in text or "embeddings" in text):
        return True
    
    return False

def get_paper_text(work):
    """Extract searchable text from a paper"""
    text_parts = []
    
    if work.get('title'):
        text_parts.append(work['title'])
    
    try:
        if work.get('abstract'):
            text_parts.append(work['abstract'])
    except:
        pass
    
    if work.get('concepts'):
        for concept in work['concepts']:
            if concept.get('display_name'):
                text_parts.append(concept['display_name'])
    
    return ' '.join(text_parts).lower()

def process_paper_chunk(papers_chunk):
    """Process a chunk of papers for keyword matching"""
    results = []
    for paper in papers_chunk:
        try:
            paper_text = get_paper_text(paper)
            matches = simple_keyword_match(paper_text, KEYWORDS)
            title = paper.get('title', 'No title')
            results.append({
                'title': title,
                'matches': matches
            })
        except Exception as e:
            results.append({
                'title': 'Error processing paper',
                'matches': False,
                'error': str(e)
            })
    return results

def parallel_keyword_check(papers, chunk_size=100):
    """Check keywords in parallel using multiprocessing"""
    # Split papers into chunks
    chunks = [papers[i:i + chunk_size] for i in range(0, len(papers), chunk_size)]
    
    # Use all available CPU cores
    num_processes = min(cpu_count(), len(chunks))
    print(f"Using {num_processes} processes to check {len(papers)} papers...")
    
    # Process chunks in parallel
    with Pool(processes=num_processes) as pool:
        chunk_results = pool.map(process_paper_chunk, chunks)
    
    # Flatten results
    all_results = []
    for chunk_result in chunk_results:
        all_results.extend(chunk_result)
    
    return all_results

def main():
    # 1. Fetch seed paper
    print("Fetching seed paper...")
    total_start_time = time.time()
    seed_work = Works()[SEED_PAPER_ID]

    print(f"Title: {seed_work['title']}")
    print(f"DOI: {seed_work.get('doi', 'No DOI')}")

    # Venue
    venue = "Unknown venue"
    if seed_work.get('primary_location') and seed_work['primary_location'].get('source'):
        venue = seed_work['primary_location']['source'].get('display_name')
    print(f"Venue: {venue}")

    # 2. Get references and citations
    references = seed_work.get('referenced_works', [])
    citations_count = seed_work.get('cited_by_count', 0)

    print(f"\nReferences: {len(references)}")
    print(f"Citations: {citations_count}")

    # 3. Batch fetch all references
    print(f"\nFetching all {len(references)} references in batches...")
    all_ref_works = []
    batch_size = 25
    all_fetched_ids = []

    for i in range(0, len(references), batch_size):
        batch_ids = references[i:i + batch_size]
        clean_ids = [ref_id.split('/')[-1] if '/' in ref_id else ref_id for ref_id in batch_ids]
        
        try:
            batch_works = Works().filter(openalex_id='|'.join(clean_ids)).get()
            all_ref_works.extend(batch_works)
            
            batch_fetched_ids = [work.get('id', '').split('/')[-1] for work in batch_works]
            all_fetched_ids.extend(batch_fetched_ids)
            
            print(f"Fetched batch {i//batch_size + 1}: {len(batch_works)} references")
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching batch {i//batch_size + 1}: {e}")

    print(f"Successfully fetched {len(all_ref_works)} reference papers")
    
    requested_ids = [ref_id.split('/')[-1] if '/' in ref_id else ref_id for ref_id in references]
    missing_ids = [ref_id for ref_id in requested_ids if ref_id not in all_fetched_ids]
    
    if missing_ids:
        print(f"\nMissing {len(missing_ids)} references:")
        for i, missing_id in enumerate(missing_ids, 1):
            full_url = f"https://openalex.org/{missing_id}"
            print(f"[{i}] {missing_id} - {full_url}")
    else:
        print("\nAll references were successfully fetched!")

    # 4. Parallel keyword checking for references
    print(f"\nChecking references for keyword matches in parallel...")
    start_time = time.time()

    ref_results = parallel_keyword_check(all_ref_works)

    ref_matches = sum(1 for result in ref_results if result['matches'])
    ref_no_matches = len(ref_results) - ref_matches

    # Show first 20 results
    print("\nFirst 20 reference results:")
    for i, result in enumerate(ref_results[:20]):
        status = "YES" if result['matches'] else "NO"
        title = result.get('title', 'No title') or 'No title'
        title = title[:50] + "..." if len(title) > 50 else title
        print(f"[{i+1}] {title} - {status}")

    print(f"\nReference results: YES({ref_matches}) NO({ref_no_matches})")

    processing_time = time.time() - start_time
    print(f"Reference processing time: {processing_time:.2f} seconds")

    # 5. Get citing papers and check them in parallel
    print(f"\nFinding papers that cite this work...")
    try:
        all_citing_works = []
        page_size = 200
        
        for page in Works().filter(cites=SEED_PAPER_ID.split('/')[-1]).paginate(per_page=page_size):
            all_citing_works.extend(page)
            if len(all_citing_works) % 1000 == 0:
                print(f"Fetched {len(all_citing_works)} citing papers so far...")
        
        print(f"Successfully fetched {len(all_citing_works)} citing papers")
        
        # Parallel keyword checking for citations
        print(f"\nChecking citing papers for keyword matches in parallel...")
        start_time = time.time()
        
        cite_results = parallel_keyword_check(all_citing_works)
        
        cite_matches = sum(1 for result in cite_results if result['matches'])
        cite_no_matches = len(cite_results) - cite_matches
        
        # Show first 20 results
        print("\nFirst 20 citing paper results:")
        for i, result in enumerate(cite_results[:20]):
            status = "YES" if result['matches'] else "NO"
            title = result.get('title', 'No title') or 'No title'
            title = title[:50] + "..." if len(title) > 50 else title
            print(f"[{i+1}] {title} - {status}")
        
        print(f"\nCiting paper results: YES({cite_matches}) NO({cite_no_matches})")
        
        processing_time = time.time() - start_time
        print(f"Citation processing time: {processing_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error getting citing papers: {e}")

    # Calculate and display total runtime
    total_end_time = time.time()
    total_runtime = total_end_time - total_start_time
    print(f"TOTAL RUNTIME: {total_runtime:.2f} seconds ({total_runtime/60:.1f} minutes)")

    print("\nDone!")

if __name__ == '__main__':
    main()