const homeHelpContent = {
  contextLabel: 'Overview',
  title: 'Welcome to the workflow hub',
  intro:
    'Use this space to get a sense of what the tool can do. From here you can start a brand-new library, return to existing work, or use your saved libraries.',
  sections: [
    {
      title: 'Main use cases',
      description: 'Everything starts from the homepage. Pick the flow that best matches your task.',
      bullets: [
        'Create library – spin up a fresh session that guides you from seed collection to review.',
        'Edit library – open a previously created library to add or remove seeds',
        'Load library – browse the repositories of completed libraries to use in the avaible use cases.',
      ],
    },
    {
      title: 'Create library',
      description: 'Launching a new library session from here automatically:',
      bullets: [
        'Create a new library.',
        'Add papers from various sources into a staging area where you can refine their metadata and selected wanted papers for your library.',
        'Matches selected papers from staging against openalex to use in library.',
        'Configure library details and create your library.',
      ],
    },
  ],
}

const libraryWorkflowContent = {
  contextLabel: 'Library creation workflow',
  title: 'Help for creating and staging a library',
  intro:
    'Whether you are on the start, seeds, or staging screens, the library creation workflow follows the same rhythm: collect inputs, review matches, and finalize outputs.',
  sections: [
    {
      title: '1. Intake seeds',
      description: 'Use whichever intake mode fits your source material.',
      bullets: [
        'Upload PDFs – drop a folder of PDFs and we extract DOIs, titles, and metadata automatically.',
        'Import from Zotero – paste a collection link or select a library to fetch items directly.',
        'Manual IDs – type or paste DOI/OpenAlex IDs for quick experiments or patch-ups.',
      ],
    },
    {
      title: '2. Staging & matching',
      description: 'After intake, every seed lands in staging for validation.',
      bullets: [
        'Review the match confidence scores, metadata, and any conflicts.',
        'Use the detail modal to inspect abstracts, related works, and matching rationale.',
        'Approve or discard seeds before they move into your final library.',
      ],
    },
    {
      title: '3. Finalize & export',
      description: 'Once satisfied with matches, publish the library.',
      bullets: [
        'Provide the final library details (name, tags, description) for future discovery.',
        'Export the curated set back to Zotero, CSV, or other downstream tools.',
        'Share the session link so team members can inspect the decisions you made.',
      ],
    },
  ],
}

const libraryLoadContent = {
  contextLabel: 'Load existing library',
  title: 'Pick a saved library and launch a workflow',
  intro:
    'Browse all discovered libraries or point to a custom folder. After you pick one, choose which workflow should launch with it.',
  sections: [
    {
      title: '1. Discover existing work',
      description: 'We scan the default directories configured for ArticleCrawler.',
      bullets: [
        'Every discovered library shows its name, description, and paper count.',
        'Use the refresh button if you recently created a new library outside the app.',
        'If nothing appears, use the custom path option to point to the correct folder.',
      ],
    },
    {
      title: '2. Validate a path on demand',
      description: 'Entering a custom path does not trigger any work until you confirm it.',
      bullets: [
        'Paths must be absolute (e.g., /Users/me/library or C:\\Libraries\\MyLib).',
        'We only validate after you pick a workflow and start a session.',
        'This keeps browsing snappy while still ensuring the folder is real.',
      ],
    },
    {
      title: '3. Attach to a use case',
      description: 'Loading a library now requires choosing how you plan to use it.',
      bullets: [
        'Pick a workflow (such as the crawler wizard) to create a fresh session.',
        'We bind the selected library to that session behind the scenes.',
        'Once ready, jump straight into the workflow that matches your task.',
      ],
    },
  ],
}

const libraryEditContent = {
  contextLabel: 'Edit existing library',
  title: 'Open a saved library in the staging workspace',
  intro:
    'Use this page when you want to reopen a completed library, review its staged papers, and make adjustments before publishing an updated version.',
  sections: [
    {
      title: '1. Locate the library',
      description: 'Search, filter, or point directly to the folder you want to edit.',
      bullets: [
        'Libraries shown here come from your configured default directories.',
        'Use the search bar or pagination to narrow down the list.',
        'If the library lives elsewhere, paste its absolute path in the custom path panel.',
      ],
    },
    {
      title: '2. Load into staging',
      description: 'Selecting a library opens a fresh staging session for it.',
      bullets: [
        'We keep the original metadata, selections, and notes intact.',
        'You can immediately add new sources or discard older seeds.',
        'Edits happen in the same staging interface you already know from creation.',
      ],
    },
    {
      title: '3. Publish updates',
      description: 'Once satisfied, finish the staging flow to save or export an updated library.',
      bullets: [
        'Run matching again if you have added new or updated sources.',
        'Configure the library details just as you would when creating a new one.',
        'Create the updated library to save it for downstream use.',
      ],
    },
  ],
}

const otherWorkflowsContent = {
  contextLabel: 'Other workflows',
  title: 'Explore secondary actions beyond the main flows',
  intro:
    'This screen lists the utility workflows that sit outside the three primary home cards. Use it to revisit experiments or discover helper tools.',
  sections: [
    {
      title: 'Browse available workflows',
      description: 'Each card highlights a specialized task you can trigger.',
      bullets: [
        'Cards summarize what the workflow does and where it will take you.',
        'The layout mirrors the homepage so interactions feel familiar.',
        'Expect this space to grow as we add more secondary tools.',
      ],
    },
    {
      title: 'Rerun crawler experiments',
      description: 'Quickly jump into the crawler rerun experience.',
      bullets: [
        'Select “Re-run crawler experiment” to list stored experiments.',
        'Preview saved configurations and launch a new job or edit before rerunning.',
        'Use this when you need reproducibility or to tweak earlier crawls.',
      ],
    },
  ],
}

const libraryStartContent = {
  contextLabel: 'Library creation kickoff',
  title: 'Choose the right path before you dive in',
  intro:
    'This screen helps you decide whether to begin with seed ingestion or explore an author topic.',
  sections: [
    {
      title: 'Seeds workflow',
      description: 'For if you want to create your own library from your own collected papers.',
      bullets: [
        'Create a library from various sourcecs such as zotero, files(Pdf, docx, LaTeX, HTML).',
        'Edit their metadata if not correct.',
        'Proceed to matching against openalex to create your library.',
      ],
    },
    {
      title: 'Author evolution',
      description: 'Great for quick investigations into how a researcher’s topics evolved.',
      bullets: [
        'Type the author name.',
        'Select the correct author',
        'Create a library from the authors papers.',
      ],
    },
  ],
}

const stagingContent = {
  contextLabel: 'Unified staging',
  title: 'Stage, clean, and approve your seed papers',
  intro:
    'Every seed flows through here so you can validate metadata, change metadata, and select what will be used for the final library.',
  sections: [
    {
      title: 'Add seeds to staging.',
      description: 'Click on the "add more papers" button and choose one of the sources to add more papers.',
      bullets: [
        'Select Zotero to load you zotero collections and add papers from the selected collections.',
        'Select uploaded files to pick individual files or a folder, extract their metadata, and add those to the staging area',
        'Select manual ID to enter OpenAlex IDs to add papers from OpenAlex to the staging area.',
      ],
    },
    {
      title: 'Edit metadata',
      description: 'Change papers their metadata if not filled in correctly or missing.',
      bullets: [
        'Double click on a entry in a column to change that data from a paper.',
        'Simply click somewhere else to finish editing',
        'The changes will be used to match against openalex if the paper is selected.',
      ],
    },
    {
      title: 'Select & filter papers',
      description: 'Choose which papers to use for your library',
      bullets: [
        'Use the filters to find the papers you like.',
        'Select or bulk select papers that you want to use in your library.',
        'Once done selecting, press "Done selecting seed papers" to match the selected papers against OpenAlex for your library',
      ],
    },
  ],
}

const crawlerFlowContent = {
  contextLabel: 'Crawler workflow',
  title: 'Gather keywords, configure, and run the crawler',
  intro:
    'Follow the same rhythm as the library flow: define inputs, confirm configuration, and let the crawler run before reviewing the outputs.',
  sections: [
    {
      title: '1. Keywords',
      description: 'Provide boolean expressions to focus the crawl.',
      bullets: [
        'Expressions support AND, OR, NOT, and parentheses.',
        'Clear keywords if you want to crawl broadly.',
        'Finalize to move into the configuration step.',
      ],
    },
    {
      title: '2. Configuration',
      description: 'Set the iteration plan and optional advanced parameters.',
      bullets: [
        'Basic settings include iteration count and papers per iteration.',
        'Advanced options adjust topic modeling, language, and network output.',
        'Save changes before moving forward.',
      ],
    },
    {
      title: '3. Run & results',
      description: 'Finalize, launch the crawl, and monitor results.',
      bullets: [
        'Give the experiment a descriptive name so you can reference it later.',
        'Watch the job status and refresh as needed.',
        'Review top papers, topics, and authors once the crawl completes.',
      ],
    },
  ],
}

const helpContentRules = [
  {
    match: (pathname) => pathname === '/' || pathname === '',
    content: homeHelpContent,
  },
  {
    match: (pathname) => pathname.startsWith('/libraries/edit'),
    content: libraryEditContent,
  },
  {
    match: (pathname) => pathname.startsWith('/workflow/other'),
    content: otherWorkflowsContent,
  },
  {
    match: (pathname) => pathname.startsWith('/libraries'),
    content: libraryLoadContent,
  },
  {
    match: (pathname) => pathname.startsWith('/about') || pathname.startsWith('/settings'),
    content: homeHelpContent,
  },
  {
    match: (pathname) => pathname.startsWith('/create/library-start'),
    content: libraryStartContent,
  },
  {
    match: (pathname) => pathname.startsWith('/create/staging'),
    content: stagingContent,
  },
  {
    match: (pathname) => pathname.startsWith('/crawler'),
    content: crawlerFlowContent,
  },
  {
    match: (pathname) => pathname.startsWith('/create'),
    content: libraryWorkflowContent,
  },
]

export function getHelpContent(pathname) {
  for (const rule of helpContentRules) {
    if (rule.match(pathname)) {
      return rule.content
    }
  }
  return homeHelpContent
}
