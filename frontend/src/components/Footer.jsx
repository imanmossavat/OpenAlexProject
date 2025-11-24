import { Link } from 'react-router-dom'
import githubIcon from '../assets/github.png'

export default function Footer() {
  return (
    <footer className="w-full bg-white border-t border-gray-200 text-sm">
      <div className="w-full px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between text-gray-600">
        <section className="space-y-1 max-w-md">
          <div className="font-semibold text-gray-700">About</div>
          <p className="text-gray-600">
            Curious about who we are or why this exists? Give the About page a quick read.
          </p>
          <Link
            to="/about"
            className="inline-flex items-center gap-2 text-purple-600 font-semibold hover:text-purple-700 no-underline"
          >
            Learn more
            <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M6.624 1.5L10.5 5.376L6.624 9.252"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M1.5 5.376H10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </Link>
        </section>

        <section className="flex items-center gap-2 text-gray-700">
          <img src={githubIcon} alt="GitHub" className="w-4 h-4" />
          <a
            href="https://github.com/imanmossavat/OpenAlexProject"
            target="_blank"
            rel="noreferrer"
            className="hover:text-gray-900 no-underline"
          >
            Github repository
          </a>
        </section>
      </div>
    </footer>
  )
}
