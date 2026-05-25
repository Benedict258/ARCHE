const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim()

export const API_BASE = rawBase.replace(/\/$/, '')

export function apiUrl(path){
  if(!path.startsWith('/')){
    throw new Error('apiUrl path must start with /')
  }
  if(!API_BASE){
    return path
  }
  return `${API_BASE}${path}`
}

export const docsUrl = API_BASE ? `${API_BASE}/docs` : '/docs'