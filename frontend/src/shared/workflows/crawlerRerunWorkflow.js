export const crawlerRerunWorkflow = {
  id: 'crawler-rerun-workflow',
  title: 'Crawler Rerun Workflow',
  description:
    'Locate previously saved crawler experiments, inspect their configurations, and either rerun them immediately or reload them for edits.',
  steps: [
    {
      id: 'discover-experiments',
      title: 'Discover experiments',
      summary: 'Scan the default experiments folder or supply a custom path to locate saved crawler runs.',
      details: [
        {
          id: 'set-root',
          title: 'Default folder',
          description: 'Set or reset the root directory that is scanned for experiment configs.',
        },
        {
          id: 'custom-path',
          title: 'Use custom experiment path',
          description: 'Provide an absolute path when you only need a single experiment folder.',
        },
      ],
      routes: ['/crawler/reruns'],
    },
    {
      id: 'choose-action',
      title: 'Choose rerun mode',
      summary: 'Select an experiment card to either launch a new job immediately or load the wizard with saved settings.',
      details: [
        {
          id: 'rerun-now',
          title: 'Re-run now',
          description: 'Starts a new crawler job using the stored configuration without any edits.',
        },
        {
          id: 'rerun-with-edits',
          title: 'Re-run with edits',
          description: 'Preloads the crawler wizard so you can adjust keywords or configuration before launching.',
        },
      ],
      routes: ['/crawler/reruns'],
    },
  ],
}

export default crawlerRerunWorkflow
