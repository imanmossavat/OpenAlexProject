import pyalex
from pyalex import Works

# Configure pyalex
pyalex.config.email = "Email"

# Search for the paper
title = "SciBERT: A Pretrained Language Model for Scientific Text"
works = Works().search(title).get(per_page=1)

if works:
    paper_id = works[0]['id']
    print(f"Paper ID: {paper_id}")
else:
    print("Paper not found")