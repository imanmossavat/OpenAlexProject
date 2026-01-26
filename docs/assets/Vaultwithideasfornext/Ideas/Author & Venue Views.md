

---

# Showing Papers for an Author or Venue in the Web App

## Overview

After the crawler finishes running, the web application already highlights important authors and venues, we can use this to get the papers from those and show it in the web app.

## How It Works

When a user clicks on an author or a venue in the web interface, the application can send a request to the OpenAlex API to retrieve all related papers. OpenAlex provides structured metadata that makes it easy to fetch:

- Papers written by a given author
    
- Papers published in a given venue
    
- Relevant metadata such as titles, abstracts, citations, and publication years
    

## Why This Is Easy to Add

The crawler has already prepared the foundational data (authors, venues, and connections). The web app can simply:

1. Detect when an author or venue is selected
    
2. Call an OpenAlex endpoint with the corresponding ID
    
3. Display the list of papers and metadata in the interface
    


## Summary

- Clicking on an author or venue triggers an OpenAlex API request.
    
- The request returns all papers associated with that entity.
    
- The app can then show these papers in the same way it already shows papers in other pages
    
- Implementing this is simple because it reuses existing patterns already in the project.
    

---