/**
 * SettingsModal.jsx
 * Modal de configurações com status real do Assistant.
 */
import { X, RefreshCw } from 'lucide-react'
import styles from './SettingsModal.module.css'

export default function SettingsModal({ open, onClose, info, onRefresh }) {
  if (!open) return null

  const stat = (ok) =>
    ok ? <span className={styles.ok}>✓ ok</span>
       : <span className={styles.err}>✗ indisponível</span>

  return (
    <div className={styles.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2>Configurações</h2>
          <button className={styles.closeBtn} onClick={onClose}><X size={16} /></button>
        </div>

        <div className={styles.body}>
          {/* Status em tempo real */}
          <div className={styles.section}>
            <div className={styles.sectionTitle}>
              Status do Assistant
              <button className={styles.refreshBtn} onClick={onRefresh} title="Atualizar">
                <RefreshCw size={12} />
              </button>
            </div>

            {info ? (
              <div className={styles.statGrid}>
                <div className={styles.statRow}><span>Modelo</span>     <strong>{info.model || '—'}</strong></div>
                <div className={styles.statRow}><span>Ollama</span>     {stat(info.ollama_up)}</div>
                <div className={styles.statRow}><span>Modelo pronto</span>{stat(info.model_ready)}</div>
                <div className={styles.statRow}><span>TTS</span>        {stat(info.tts)} {info.tts_engine ? <em>{info.tts_engine}</em> : null}</div>
                <div className={styles.statRow}><span>STT</span>        {stat(info.stt)}</div>
                <div className={styles.statRow}><span>Admin</span>      {stat(info.admin)}</div>
                <div className={styles.statRow}><span>Cache</span>      <strong>{info.cache_size ?? '—'} entradas</strong></div>
              </div>
            ) : (
              <p className={styles.loading}>Carregando…</p>
            )}
          </div>

          {/* Info sobre o vídeo */}
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Vídeo da IA</div>
            <p className={styles.hint}>
              Coloque <code>ia.mp4</code> em <code>frontend-react/public/</code>.
              Proporção 1:1 dá o melhor efeito circular.
            </p>
          </div>

          {/* Dica de backend URL */}
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Backend</div>
            <p className={styles.hint}>
              O proxy Vite redireciona <code>/api/*</code> → <code>localhost:5000</code>.
              Para trocar a porta edite <code>vite.config.js</code>.
            </p>
          </div>
        </div>

        <div className={styles.footer}>
          <button className={styles.okBtn} onClick={onClose}>Fechar</button>
        </div>
      </div>
    </div>
  )
}
