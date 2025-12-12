import { createBrowserRouter } from 'react-router-dom'
import Layout from '@/components/Layout'

import HomePage from '@/pages/home/HomePage'
import LibraryCreationStartPage from '@/pages/create/LibraryCreationStartPage'
import UnifiedStagingPage from '@/pages/create/UnifiedStagingPage'
import MatchedSeedsPage from '@/pages/create/MatchedSeedsPage'
import PdfImportPage from '@/pages/create/pdf/PdfImportPage'
import ZoteroImportPage from '@/pages/create/zotero/ZoteroImportPage'
import ManualIdsPage from '@/pages/create/manual/ManualIdsPage'
import LibraryDetailsPage from '@/pages/create/details/LibraryDetailsPage'
import ReviewCreatePage from '@/pages/create/review/ReviewCreatePage'
import IntegrationsSettingsPage from '@/pages/settings/IntegrationsSettingsPage'
import GrobidSetupPage from '@/pages/help/GrobidSetupPage'
import AboutPage from '@/pages/about/AboutPage'
import WorkflowPage from '@/pages/workflow/WorkflowPage'
import LibraryLoadPage from '@/pages/libraries/LibraryLoadPage'
import LibraryEditPage from '@/pages/libraries/LibraryEditPage'
import CrawlerKeywordsPage from '@/pages/crawler/keywords/CrawlerKeywordsPage'
import CrawlerConfigurationPage from '@/pages/crawler/configuration/CrawlerConfigurationPage'
import CrawlerRunPage from '@/pages/crawler/run/CrawlerRunPage'
import CrawlerResultsPage from '@/pages/crawler/results/CrawlerResultsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'create/seeds', element: <LibraryCreationStartPage /> },
      { path: 'create/library-start', element: <LibraryCreationStartPage /> },
      { path: 'create/staging', element: <UnifiedStagingPage /> },
      { path: 'create/staging/matched', element: <MatchedSeedsPage /> },
      { path: 'create/seeds/pdf', element: <PdfImportPage /> },
      { path: 'create/seeds/zotero', element: <ZoteroImportPage /> },
      { path: 'create/seeds/manual', element: <ManualIdsPage /> },
      { path: 'create/details', element: <LibraryDetailsPage /> },
      { path: 'create/review', element: <ReviewCreatePage /> },
      { path: 'libraries', element: <LibraryLoadPage /> },
      { path: 'libraries/edit', element: <LibraryEditPage /> },
      { path: 'crawler/keywords', element: <CrawlerKeywordsPage /> },
      { path: 'crawler/configuration', element: <CrawlerConfigurationPage /> },
      { path: 'crawler/run', element: <CrawlerRunPage /> },
      { path: 'crawler/results', element: <CrawlerResultsPage /> },
      { path: 'settings/integrations', element: <IntegrationsSettingsPage /> },
      { path: 'help/grobid', element: <GrobidSetupPage /> },
      { path: 'about', element: <AboutPage /> },
      { path: 'workflow', element: <WorkflowPage /> },
    ],
  },
])

export default router
