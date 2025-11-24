const teamMembers = [
  {
    name: 'Bryan Hoppenbrouwer',
    role: 'Full stack developer',
    linkedin: 'https://www.linkedin.com/in/bryan-hoppenbrouwer/',
    blurb:
      'I am a student studying at Fontys University of Applied sciences, focusing mainly on full-stack development',
  },
  {
    name: 'Iman Mossavat',
    role: 'Mentor & AI specialist',
    linkedin: 'https://www.linkedin.com/in/iman-mossavat/',
    blurb:
      'I have over a decade of industrial expertise in machine learning algorithm development and prototyping within the semiconductor sector, specializing in statistical modeling, signal processing, deep learning, and optimization. I bring knowledge and experience, but most importantly passion and purpose, to my current role teaching within the ICT department at Fontys University of Applied Sciences. My interests span from science to applied math, and Physics. I am deeply committed to collaboration and innovation, societal well-being, and inclusion. I enjoy coaching young professionals.',
  },
]

export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-12 space-y-16">
      <section className="text-center space-y-4">
        <p className="text-sm uppercase tracking-widest text-purple-500 font-semibold">
          About us
        </p>
        <h1 className="text-4xl font-semibold text-gray-900">
          Making literature reviews less painful
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          We’re building a tool that could help researchers discover, organize, and stay current with academic literature.
        </p>
      </section>

      <section className="bg-purple-50 rounded-2xl p-8 space-y-4 shadow-md">
        <h2 className="text-2xl font-semibold text-gray-900">Our story</h2>
        <p className="text-gray-700 leading-relaxed">
          In a time where there is a lot of information overload and widespread misinformation, researchers face a significant challenge in efficiently analysing and making academic literature.
          This is why we aimed to create a tool that leverages OpenAlex to retrieve and organize data, find topics, create citation graphs, and identify important papers. Whilst also making the research path faster by ingestion from various sources researchers use (Different file types, Zotero library).
        </p>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">The team</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {teamMembers.map((member) => (
            <article
              key={member.name}
              className="border border-gray-200 rounded-2xl p-6 space-y-3 bg-white shadow-md"
            >
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{member.name}</h3>
                <p className="text-sm text-purple-600 font-medium">{member.role}</p>
              </div>
              <p className="text-gray-600">{member.blurb}</p>
              <a
                href={member.linkedin}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                <svg
                  className="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M20.452 20.452h-3.554v-5.569c0-1.328-.024-3.036-1.85-3.036-1.851 0-2.134 1.445-2.134 2.939v5.666H9.361V9h3.414v1.561h.049c.476-.9 1.637-1.85 3.37-1.85 3.602 0 4.267 2.371 4.267 5.455v6.286zM5.337 7.433a2.063 2.063 0 11.001-4.126 2.063 2.063 0 01-.001 4.126zM7.114 20.452H3.558V9h3.556v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
                Connect
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="border border-gray-200 rounded-2xl p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shadow-md">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">See the code</h2>
          <p className="text-gray-600">
            Everything we build here is open source. Feel free to take a look.
          </p>
        </div>
        <a
          href="https://github.com/imanmossavat/OpenAlexProject"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full border border-gray-300 text-gray-900 text-sm font-medium shadow-sm hover:shadow-md hover:bg-gray-50 transition"
        >
          <svg className="w-5 h-5" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 005.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49 0 0-2 .37-2.42-.85 0 0-.36-.92-.88-1.17 0 0-.72-.49.05-.48 0 0 .78.06 1.19.8.69 1.19 1.84.85 2.29.65.07-.5.27-.85.49-1.05-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.56 7.56 0 012.01-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.27.23.52.68.52 1.38 0 1-.01 1.81-.01 2.06 0 .21.15.46.55.38A8 8 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          GitHub repository
        </a>
      </section>
    </div>
  )
}
