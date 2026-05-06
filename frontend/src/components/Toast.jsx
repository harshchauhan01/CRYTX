import { useState, useEffect } from 'react';
import './Toast.css';
import { soundFX } from '../utils/soundFX';

let toastCounter = 0;
let addToastCallback = null;

export const toast = (message, type = 'info', duration = 3000) => {
  if (addToastCallback) {
    addToastCallback(message, type, duration);
    if (type === 'success') soundFX.execute();
    else if (type === 'error') soundFX.error();
    else soundFX.blip();
  }
};

export function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    addToastCallback = (message, type, duration) => {
      const id = ++toastCounter;
      setToasts(prev => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    };
    return () => { addToastCallback = null; };
  }, []);

  return (
    <div className="px-toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`px-toast px-toast-${t.type} glitch-effect-sm`}>
          <span className="toast-icon">
            {t.type === 'success' ? '✔' : t.type === 'error' ? '⚠' : 'ℹ'}
          </span>
          <span className="toast-msg">{t.message}</span>
        </div>
      ))}
    </div>
  );
}
