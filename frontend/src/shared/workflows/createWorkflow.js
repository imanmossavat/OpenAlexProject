export const createWorkflow = {
  id: 'create-library',
  title: 'Create Library Workflow',
  description:
    'Collect seeds from multiple sources, refine them in staging, run OpenAlex matching, and then capture the final library configuration.',
  steps: [
    {
      id: 'choose-entry',
      title: 'Choose how to start',
      summary: 'Decide whether you want to branch into author-topic analysis or begin assembling your own seed list.',
      details: [
        {
          id: 'author-topic',
          title: 'Author topic exploration',
          description: 'Jump into the author-topic flow by entering a researcher name and letting the wizard guide you.',
        },
        {
          id: 'seed-entry',
          title: 'Seed staging',
          description: 'Stay in the library creation flow to gather papers from your preferred sources.',
        },
      ],
      routes: ['/create/library-start', '/create/seeds'],
    },
    {
      id: 'stage',
      title: 'Stage',
      summary: 'Bring in papers from multiple inputs, refine the metadata, and stage the seeds you intend to use.',
      details: [
        {
          id: 'staging-table',
          title: 'Unified staging table',
          description: 'Edit metadata inline, filter by source or attributes, and toggle the seeds you want to match.',
        },
        {
          id: 'source-imports',
          title: 'Source imports',
          description: 'Add seeds via Zotero collections, manual OpenAlex IDs, or uploaded files (PDF, DOCX, XML, LaTeX, HTML).',
        },
      ],
      routes: [
        '/create/staging',
        '/create/seeds/manual',
        '/create/seeds/zotero',
        '/create/seeds/pdf',
      ],
    },
    {
      id: 'match',
      title: 'Match',
      summary: 'Confirm OpenAlex matches and resolve any seeds that still need attention.',
      details: [
        {
          id: 'auto-match',
          title: 'Auto matches',
          description: 'Review the confident matches, deselect anything you do not want to keep, and accept the rest.',
        },
        {
          id: 'rematch',
          title: 'Fix unmatched seeds',
          description: 'Adjust metadata inline and trigger a rematch for the stubborn items.',
        },
      ],
      routes: ['/create/staging/matched'],
    },
    {
      id: 'library',
      title: 'Library',
      summary: 'Describe and create the library once the seed list looks good.',
      details: [
        {
          id: 'details',
          title: 'Library details',
          description: 'Name the library, customize the location, and optionally describe its purpose.',
        },
        {
          id: 'review',
          title: 'Review & create',
          description: 'Double-check the summary, then create the library to wrap up the workflow.',
        },
      ],
      routes: ['/create/details', '/create/review'],
    },
  ],
}
