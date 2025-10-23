# ArticleCrawler - Installation and User Guide

## Table of Contents

1. System Requirements
2. Installation
3. Configuration
4. Getting Started

---

## System Requirements

### Required Software

- **Python**: 3.10 or higher
- **Docker** (required for PDF processing with GROBID)
- **Git** (for cloning the repository)

### Operating Systems

- Windows 10/11


---

## Installation

### Step 1: Clone the Repository

Clone the repository and switch to the Bryan branch:

```bash
git clone https://github.com/imanmossavat/OpenAlexProject.git
cd OpenAlexProject
git checkout Bryan
```

### Step 2: Set Up Python Environment

I highly recommend using a virtual environment to avoid conflicts with your system Python packages.

#### Option A: Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n articlecrawler python=3.10
conda activate articlecrawler
```

### Step 3: Install Dependencies

Install the package with all dependencies using pip:

First, navigate to your project directory:

```bash
cd OpenAlexProject\fakenewscitationnetwork
```

```bash
pip install -e ".[cli,dev]"
```

This installs:

- Core dependencies (pandas, networkx, scikit-learn, etc.)
- CLI dependencies (typer, rich, questionary)
- Dev dependencies (pytest, black, flake8)

### Step 4: Download NLTK Data

The system uses NLTK for text processing. Download required data:

```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### Step 5: Install Docker (for PDF Processing)

PDF processing requires GROBID, which runs in Docker.

Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

After installation, make sure Docker Desktop is running before processing PDFs.


---

## Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```bash
# On Linux/macOS:
cp _env .env

# On Windows:
copy _env .env
```

Edit `.env` with your credentials:

```ini
# OpenAlex Configuration (Required)
OPENALEX_EMAIL=your.email@example.com

# Zotero Configuration (Optional - only needed for Zotero integration)
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_LIBRARY_TYPE=user
ZOTERO_API_KEY=your_api_key
```

#### Getting API Keys


**Zotero API Key** (Optional):

1. Create account at https://www.zotero.org/
2. Go to https://www.zotero.org/settings/keys
3. Click "Create new private key"
4. Select read permissions
5. Copy the API key to your `.env` file
6. Find your library ID

### GROBID Docker Setup

GROBID is required because of the PDF processing

**IMPORTANT:** Run GROBID commands in a **separate terminal/command prompt** window and keep it running while processing PDFs.

#### Step 1: Pull the GROBID Docker Image
```bash
docker pull lfoppiano/grobid:0.8.2
```

This will download the GROBID image (~2GB). It may take several minutes depending on your internet connection.

#### Step 2: Start GROBID (in a separate terminal)

**Open a new terminal/command prompt window** and run:
```bash
docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2
```

**Notes:**
- Keep this terminal window open while processing PDFs
- Wait about 30-60 seconds for GROBID to fully start


---

## Getting Started

**ArticleCrawler** provides 5 main use cases accessible through the command-line interface.

First, navigate to your project directory:

```bash
cd OpenAlexProject\fakenewscitationnetwork
```

---

### 1. Interactive Wizard

```bash
python -m ArticleCrawler.cli.main wizard
```

Guides you through setting up and running a new crawl experiment with step-by-step prompts.

**Steps:**

1. **Name:** (e.g., `Testing`)
    
2. **Data Source:** `OpenAlex`
    
3. **Seed Paper Selection:** Choose from options (if using IDs, use OpenAlex IDs)
    
4. **Keywords or Expressions:**  
    Examples:
    
    - `Healthcare`
        
    - `(science OR scientific) AND ((summary AND generation) OR summarization)`
        
5. **Quick Testing Configuration:**
    
    - Iterations: `1`
        
    - Papers per iteration: `1`
        
6. **Advanced Configuration:**
    
    - Choose topic modeling algorithm: `LDA`
        
    - Num topics: `20`
        
    - Include Author nodes: `n`
        
    - Enable retraction watch: `y`
        
    - Save figures: `y`
        
    - Customize ignored venues:
        
        - `No` to keep default ignored (ArXiv, WWW, medRxiv)
            
        - Optionally add more
            
    - Language: `EN`
        
7. **Review and Confirm:**  
    Start crawling — will open the **Vault** with all markdown files, folders, Excel files, and figures.
    

---

### 2. Edit Configuration

```bash
python -m ArticleCrawler.cli.main edit
```

Edit existing experiment configurations.  
_(You must have run the wizard at least once before using this.)_

**Steps:**

1. Select from existing experiments (choose the one you made with the wizard)
    
2. Give the edited experiment a new name
    
3. Choose what to modify (e.g., remove or add a seed paper)
    
4. Save and run when done
    
5. Review and confirm (`Y`)
    

Will open the **Vault** for review.

---

### 3. Library Creation

```bash
python -m ArticleCrawler.cli.main library-create
```

Build a comprehensive literature library from seed papers.

**Steps:**

1. **Library Name:** (e.g., `Healthcare`)
    
2. **Confirm Location**
    
3. _(Optional)_ Add description
    
4. Select paper sources and add papers
    
5. Review and confirm to create the library
    

Creates the library at the specified location with markdown files and paper metadata.

---

### 4. Topic Modeling

```bash
python -m ArticleCrawler.cli.main topic-modeling
```

Discover and analyze topics across a literature collection.

**Steps:**

1. Use an existing library _(or create a new one — it will take you through library creation first)_
    
2. **Specify Path** to the library
    
3. Select algorithm: `LDA`
    
4. Number of topics: `5`
    
5. Review and confirm (`Y`)
    

Creates a **topics** folder inside your library with:

- Papers grouped by topic
    
- Topic overview markdown file
    

---

### 5. Author Evolution

```bash
python -m ArticleCrawler.cli.main author-evolution
```

Track how an author’s research interests evolve over time.

**Steps:**

1. **Select Author:** e.g., `Jason Priem`  
    (e.g., `Jason Priem - OpenAlex (62 papers, 3,991 citations)`)
    
2. **Advanced Configuration**
    
3. **Algorithm:** `LDA`
    
    - Number of topics: `10`
        
    - Year time period: `1`
        
    - Visualization type: (e.g., `Line chart`)
        
    - Limit papers to analyze: `n`
        
    - Save library permanently: `y`
        
    - Confirm library path (press enter to use shown location)
        
    - Save visualizations to different location: `n`
        
4. **Review and Confirm**
    

Outputs will be saved to the specified location, including:

- Papers
    
- Topics
    
- Visualization files