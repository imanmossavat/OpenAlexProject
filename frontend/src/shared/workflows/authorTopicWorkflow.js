export const authorTopicWorkflow = {
  id: 'author-topic-evolution',
  title: 'Author Topic Evolution Workflow',
  description:
    'Search for an author in OpenAlex, review their complete publication history, run topic modeling + temporal analysis, and capture the insights in a reusable library.',
  steps: [
    {
      id: 'select-author',
      title: 'Select author',
      summary: 'Search OpenAlex and confirm the exact researcher identity before running any analysis.',
      details: [
        {
          id: 'search',
          title: 'Search & shortlist',
          description: 'Type a name, inspect the returned affiliations/metrics, and pick the right identity.',
        },
        {
          id: 'max-results',
          title: 'Result limits',
          description: 'We cap the list to the top matches so you can resolve the correct author quickly.',
        },
      ],
      routes: ['/author-topic-evolution', '/author-topic-evolution/select'],
    },
    {
      id: 'configure',
      title: 'Configure',
      summary: 'Set topic modeling parameters and storage preferences before launching the run.',
      details: [
        {
          id: 'model-choice',
          title: 'Topic model',
          description: 'Pick between NMF and LDA and choose how many topics to model.',
        },
        {
          id: 'temporal-window',
          title: 'Temporal window',
          description: 'Define how many years make up each period in the evolution charts.',
        },
        {
          id: 'library-save',
          title: 'Save location',
          description: 'Optionally point at a permanent library root to save the generated papers and outputs.',
        },
      ],
      routes: ['/author-topic-evolution/configure'],
    },
    {
      id: 'analyze',
      title: 'Analyze',
      summary: 'Run the topic modeling + temporal enrichment pipeline on the selected author’s corpus.',
      details: [
        {
          id: 'paper-pull',
          title: 'Paper collection',
          description: 'We fetch every OpenAlex work for the author (respecting optional caps).',
        },
        {
          id: 'model-run',
          title: 'Model execution',
          description: 'Topic assignments, temporal grouping, and visualization assets are generated automatically.',
        },
      ],
    },
    {
      id: 'results',
      title: 'Results',
      summary: 'Review the summary metrics, period counts, emerging/declining topics, and downloads.',
      details: [
        {
          id: 'summary-cards',
          title: 'Summary cards',
          description: 'See total papers analyzed, time span, and the topics extracted.',
        },
        {
          id: 'visualizations',
          title: 'Visualizations',
          description: 'Toggle between line, heatmap, and stacked-area views to inspect topic evolution.',
        },
        {
          id: 'artifacts',
          title: 'Artifacts & libraries',
          description: 'When saved permanently, grab the generated visualization path and library location.',
        },
      ],
      routes: ['/author-topic-evolution/results'],
    },
  ],
}

export default authorTopicWorkflow
