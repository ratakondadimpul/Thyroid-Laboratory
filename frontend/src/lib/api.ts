const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeader(){
  if(typeof window==='undefined') return {}
  const t = localStorage.getItem('thyroid_token')
  return t ? { 'Authorization': `Bearer ${t}` } : {}
}
async function jfetch(url: string, opts?: RequestInit){
  const headers:any = { ...(opts?.headers||{}), ...authHeader() }
  const r = await fetch(`${API}${url}`, { ...opts, headers })
  if(!r.ok){
    const t = await r.text().catch(()=> '')
    throw new Error(t || `${r.status} ${r.statusText}`)
  }
  const ct = r.headers.get('content-type')||''
  if(ct.includes('application/json')) return r.json()
  return r
}

export async function login(email:string, password:string){
  const r = await fetch(`${API}/api/auth/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password})})
  if(!r.ok) throw new Error(await r.text())
  return r.json()
}
export async function getMe(){ return jfetch('/api/auth/me') }
export async function getDashboard(){ return jfetch('/api/dashboard/stats') }
export async function uploadDataset(file:File){
  const fd = new FormData(); fd.append('file', file)
  const headers:any = authHeader()
  const r = await fetch(`${API}/api/datasets/upload`, { method:'POST', body: fd, headers})
  if(!r.ok) throw new Error(await r.text())
  return r.json()
}
export async function analyzeDataset(batchId:string){ return jfetch(`/api/datasets/${batchId}/analyze`, { method:'POST'}) }
export async function getValidation(batchId:string){ return jfetch(`/api/datasets/${batchId}/validation`) }
export async function getResults(batchId:string, params:Record<string,any>={}){
  const q = new URLSearchParams(params).toString()
  return jfetch(`/api/datasets/${batchId}/results${q?'?'+q:''}`)
}
export async function getPatient(batchId:string, pid:string){ return jfetch(`/api/datasets/${batchId}/patient/${encodeURIComponent(pid)}`) }
export async function getAnalytics(batchId:string){ return jfetch(`/api/datasets/${batchId}/analytics`) }
export async function getHistory(limit=20, offset=0){ return jfetch(`/api/datasets/history?limit=${limit}&offset=${offset}`)}
export async function getPerformance(){ return jfetch('/api/model/performance')}
export function downloadUrl(batchId:string, segment:string){ return `${API}/api/datasets/${batchId}/downloads/${segment}` }
export function reportUrl(batchId:string){ return `${API}/api/datasets/${batchId}/report` }
