import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getPapers = (params = {}) =>
  api.get('/papers', { params }).then(r => r.data)

export const getPaper = id =>
  api.get(`/papers/${id}`).then(r => r.data)

export const ratePaper = (id, rating) =>
  api.post(`/papers/${id}/rate`, { rating }).then(r => r.data)

export const toggleDislike = (id, is_disliked) =>
  api.put(`/papers/${id}/dislike`, { is_disliked }).then(r => r.data)

export const trackPaperClick = (id, target) =>
  api.post(`/papers/${id}/click`, { target }).then(r => r.data)

export const getHistoryDates = () =>
  api.get('/papers/history/dates').then(r => r.data.dates)

export const triggerFetch = () =>
  api.post('/fetch/trigger').then(r => r.data)

export const getFetchStatus = () =>
  api.get('/fetch/status').then(r => r.data)

export const getFetchLogs = () =>
  api.get('/fetch/logs').then(r => r.data)

export const getHealth = () =>
  api.get('/health').then(r => r.data)

export const getSettings = () =>
  api.get('/settings').then(r => r.data)

export const updateSettings = data =>
  api.put('/settings', data).then(r => r.data)
