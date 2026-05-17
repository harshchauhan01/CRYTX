import { useState, useEffect } from 'react';
import './Toast.css';

let toastCounter = 0;
let addToastCallback = null;

export const toast = (message, type = 'info', duration = 3500) => {
  if (addToastCallback) {
    addToastCallback({ id: ++toastCounter, message, type, duration });
  }
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    addToastCallback = (t) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== t.id));
      }, t.duration);
    };
    return () => { addToastCallback = null; };
  }, []);

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">
            {t.type === 'success' ? '✓' : t.type === 'error' ? '✗' : 'ℹ'}
          </span>
          <span className="toast-msg">{t.message}</span>
        </div>
      ))}
    </div>
  );
}
