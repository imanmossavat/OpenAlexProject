export const crawlerWorkflow = {
  id: 'crawler-workflow',
  title: 'Crawler Workflow',
  description:
    'Start from saved libraries or seeds, focus the crawl with keywords, configure iterations, and gather enriched results.',
  steps: [
    {
      id: 'keywords',
      title: 'Keywords',
      summary: 'Add or refine keyword expressions to guide which papers the crawler prioritizes.',
      details: [
        {
          id: 'expression-editor',
          title: 'Expression editor',
          description: 'Supports AND/OR/NOT along with parentheses for precise scoping.',
        },
      ],
      routes: ['/crawler/keywords'],
    },
    {
      id: 'configuration',
      title: 'Configuration',
      summary: 'Set iterations, sampling rates, and optional advanced settings.',
      details: [
        {
          id: 'basic-config',
          title: 'Basic configuration',
          description: 'Max iterations and papers per iteration.',
        },
        {
          id: 'advanced-config',
          title: 'Advanced configuration',
          description: 'Topic modeling, language, ignored venues, retraction checks.',
        },
      ],
      routes: ['/crawler/configuration'],
    },
    {
      id: 'run',
      title: 'Run',
      summary: 'Finalize the experiment, start the crawler, and monitor progress.',
      details: [
        {
          id: 'finalize',
          title: 'Finalize configuration',
          description: 'Review the summary before launching the job.',
        },
        {
          id: 'start',
          title: 'Start crawler',
          description: 'Kick off the background job and track its status.',
        },
      ],
      routes: ['/crawler/run'],
    },
    {
      id: 'results',
      title: 'Results',
      summary: 'Explore network metrics, topics, and top papers after the crawl completes.',
      routes: ['/crawler/results'],
    },
  ],
}

export default crawlerWorkflow
