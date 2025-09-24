import pyalex
from pyalex import Works

# Configure pyalex
pyalex.config.email = "885585@fontys.nl"

# Configuration
SEED_PAPER_ID = "https://openalex.org/w2970771982"

# Fetch the seed paper
work = Works()[SEED_PAPER_ID]

# Extract metadata
print("SEED PAPER METADATA:")
print(f"Title: {work['title']}")
print(f"DOI: {work.get('doi', 'No DOI')}")
print(f"Year: {work.get('publication_year', 'Unknown')}")

# Venue
venue = "Unknown venue"
if work.get('primary_location') and work['primary_location'].get('source'):
    venue = work['primary_location']['source'].get('display_name')
print(f"Venue: {venue}")

# Abstract
try:
    abstract = work["abstract"]
    print(f"Abstract: {abstract}")
except (KeyError, TypeError):
    print("Abstract: No abstract available")

# References and Citations
references = work.get('referenced_works', [])
print(f"References: {len(references)} papers")
print(f"Citations: {work.get('cited_by_count', 0)} papers")

print(f"\nreference IDs:")
for i, ref_id in enumerate(references):
    print(f"{i+1}. {ref_id}")

print(f"\nTotal references: {len(references)}")
print(f"Total citations: {work.get('cited_by_count', 0)}")