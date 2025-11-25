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

const helpContentRules = [
  {
    match: (pathname) => pathname === '/' || pathname === '',
    content: homeHelpContent,
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
