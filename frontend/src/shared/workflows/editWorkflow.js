export const editWorkflow = {
  id: 'edit-library',
  title: 'Edit Library Workflow',
  description:
    'Load the papers from an existing library into the staging workspace, adjust the seed list, and either update the original library or save a duplicate.',
  steps: [
    {
      id: 'select-library',
      title: 'Select library',
      summary: 'Choose which saved library you want to edit or duplicate.',
      details: [
        {
          id: 'library-discovery',
          title: 'Library discovery',
          description:
            'Browse all detected libraries (or specify a custom path) and attach one to a fresh edit session.',
        },
      ],
      routes: ['/libraries/edit'],
    },
    {
      id: 'stage',
      title: 'Stage & refine',
      summary: 'All papers from the chosen library appear in staging, where you can add new sources or prune existing ones.',
      details: [
        {
          id: 'library-seeds',
          title: 'Existing seeds imported',
          description:
            'Every paper from the library is auto-selected inside staging so you can filter, edit metadata, and toggle selections.',
        },
        {
          id: 'additional-sources',
          title: 'Add more sources',
          description:
            'Augment the library by bringing in papers from Zotero, manual IDs, or uploaded documents—just like the create workflow.',
        },
      ],
      routes: ['/create/staging'],
    },
    {
      id: 'match',
      title: 'Match & confirm',
      summary: 'Re-run OpenAlex matching to reconcile any new or edited seeds before applying changes.',
      details: [
        {
          id: 'review-matches',
          title: 'Review matches',
          description:
            'Inspect the matched results, deselect anything you no longer want, and fix metadata for remaining unmatched seeds.',
        },
      ],
      routes: ['/create/staging/matched'],
    },
    {
      id: 'apply',
      title: 'Apply changes',
      summary: 'Decide whether to update the current library in place or save the curated selection to a new location.',
      details: [
        {
          id: 'review-selection',
          title: 'Review summary',
          description:
            'Double-check the name, location, and paper counts before finalizing. See exactly how many papers will be added or removed.',
        },
        {
          id: 'update-or-duplicate',
          title: 'Update vs duplicate',
          description:
            'Either apply the add/remove diff to the existing library or specify a new path/name to save a copy.',
        },
      ],
      routes: ['/create/review'],
    },
  ],
}
