import pyalex
from pyalex import Works

# Configure pyalex
pyalex.config.email = "Email"

# Use author ID directly
author_id = "https://openalex.org/A5090038537"

# Get all papers by this author
works = Works().filter(**{"authorships.author.id": author_id}).get()

print(f"Total papers by author ID {author_id}: {len(works)}")
print("\nAll papers:")

for i, work in enumerate(works):
    print(f"{i+1}. {work['title']}")
    print(f"   ID: {work['id']}")