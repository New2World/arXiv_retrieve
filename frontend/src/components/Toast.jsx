import { useState, useCallback } from 'react'

let _addToast = null

export function ToastContainer() {
  const [toasts, setToasts] = useState([])

  _addToast = useCallback((msg, type = 'success') => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500)
  }, [])

  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>{t.msg}</div>
      ))}
    </div>
  )
}

export const toast = {
  success: msg => _addToast?.(msg, 'success'),
  error:   msg => _addToast?.(msg, 'error'),
}
