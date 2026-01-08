import { ArrowLeft, Terminal } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const dockerCommand = 'docker run -d -p 8070:8070 lfoppiano/grobid:0.8.2'

export default function GrobidSetupPage() {
  const navigate = useNavigate()
  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <div className="flex items-center gap-4">
          <Button variant="outline" className="rounded-full" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">PDF imports</p>
            <h1 className="text-3xl font-semibold text-gray-900">Set up GROBID for metadata extraction</h1>
            <p className="text-sm text-gray-500 mt-2">
              The PDF pipeline relies on an external GROBID service to parse titles, authors, and DOIs. Follow these
              steps to spin up the official Docker image locally.
            </p>
          </div>
        </div>

        <section className="border border-gray-200 rounded-3xl p-6 shadow-sm space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">1. Install Docker</h2>
          <p className="text-gray-600 text-sm">
            Download Docker Desktop (Windows/macOS) or install Docker Engine on Linux. Once installed, ensure Docker is
            running before continuing.
          </p>
          <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 text-sm text-gray-700">
            <p className="font-semibold mb-2">Helpful links</p>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <a
                  href="https://docs.docker.com/desktop/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-purple-600 hover:text-purple-700"
                >
                  Docker Desktop download
                </a>
              </li>
              <li>
                <a
                  href="https://docs.docker.com/engine/install/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-purple-600 hover:text-purple-700"
                >
                  Docker Engine installation guides
                </a>
              </li>
            </ul>
          </div>
        </section>

        <section className="border border-gray-200 rounded-3xl p-6 shadow-sm space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">2. Start the GROBID container</h2>
          <p className="text-gray-600 text-sm">
            Open a terminal with Docker access and run the container below. It exposes port 8070, which the crawler
            expects by default.
          </p>
          <CommandBlock command={dockerCommand} />
          <p className="text-xs text-gray-500">
            The container runs in the background (<code>-d</code>). Restart Docker Desktop or rerun the command if you
            ever stop it.
          </p>
        </section>

        <section className="border border-gray-200 rounded-3xl p-6 shadow-sm space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">3. Verify it is reachable</h2>
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
            <li>Visit http://localhost:8070/api/isalive in the browser. A JSON response means it is running.</li>
            <li>Return to the “Import from uploaded files” dialog and try uploading again.</li>
          </ol>
        </section>
      </div>
    </div>
  )
}

function CommandBlock({ command }) {
  const copyToClipboard = () => navigator.clipboard?.writeText(command)
  return (
    <div className="bg-gray-900 text-white rounded-2xl p-4 font-mono text-sm flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Terminal className="w-4 h-4 text-gray-400" />
        <span>{command}</span>
      </div>
      <button
        type="button"
        className="text-xs uppercase tracking-wider text-gray-400 hover:text-white"
        onClick={copyToClipboard}
      >
        Copy
      </button>
    </div>
  )
}
