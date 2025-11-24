const apiUrl = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) || 'http://localhost:8000'

const config = { apiUrl }

export { config }
export default config

