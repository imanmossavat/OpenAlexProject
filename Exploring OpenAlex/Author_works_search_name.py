import pyalex
from pyalex import Works, Authors

# Configure pyalex
pyalex.config.email = "Email"

# Find author by name
author_name = "Iz Beltagy"
authors = Authors().search(author_name).get(per_page=1)

if authors:
    author_id = authors[0]['id']
    
    # Get all papers by this author
    works = Works().filter(**{"authorships.author.id": author_id}).get()
    
    print(f"Total papers by {author_name}: {len(works)}")
    print("\nAll papers:")
    
    for i, work in enumerate(works):
        print(f"{i+1}. {work['title']}")
        print(f"   ID: {work['id']}")
else:
    print("Author not found")