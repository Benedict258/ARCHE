const DEFAULT_API_BASE = 'https://arche-webapp-api.onrender.com'
const LOCAL_API_BASE = 'http://localhost:8000'

function isLocalHost(hostname){
  return hostname === 'localhost' || hostname === '127.0.0.1'
}

function isLocalApiBase(base){
  return /localhost|127\.0\.0\.1/i.test(base)
}

const configuredBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : ''
const runtimeIsLocal = isLocalHost(runtimeHost)

let resolvedBase = configuredBase || (runtimeIsLocal ? LOCAL_API_BASE : DEFAULT_API_BASE)
if(!runtimeIsLocal && isLocalApiBase(resolvedBase)){
  resolvedBase = DEFAULT_API_BASE
}

export const API_BASE = resolvedBase.replace(/\/$/, '')

export function apiUrl(path){
  if(!path.startsWith('/')){
    throw new Error('apiUrl path must start with /')
  }
  if(!API_BASE){
    return path
  }
  return `${API_BASE}${path}`
}

export const docsUrl = `${API_BASE}/docs`