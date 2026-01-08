import { Download, Loader2, RefreshCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'

export default function CatalogToolbar({
  catalogEnabled,
  catalogLoading,
  exportingCatalog,
  onExport,
  onRefresh,
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">All papers</h2>
        <p className="text-sm text-gray-500">
          Browse every paper captured by this crawl and search across the catalog.
        </p>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Button
          variant="outline"
          className="rounded-full"
          onClick={onExport}
          disabled={exportingCatalog || !catalogEnabled}
        >
          {exportingCatalog ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Preparing…
            </>
          ) : (
            <>
              <Download className="w-4 h-4 mr-2" />
              Export (.xlsx)
            </>
          )}
        </Button>
        <Button
          variant="outline"
          className="rounded-full"
          onClick={onRefresh}
          disabled={catalogLoading || !catalogEnabled}
        >
          {catalogLoading ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <RefreshCcw className="w-4 h-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>
    </div>
  )
}
