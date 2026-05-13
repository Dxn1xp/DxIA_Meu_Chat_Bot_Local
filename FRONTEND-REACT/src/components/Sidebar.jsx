/**
 * Sidebar.jsx
 * Painel lateral: lista de conversas + botão nova conversa.
 * Estilo WhatsApp Web — dark.
 */

import { Pencil, Trash2, MessageSquare } from 'lucide-react'
import styles from './Sidebar.module.css'

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  status,
  modelInfo,
}) {
  const statusMap = {
    online:     { label: 'Online',      cls: styles.dotOnline },
    starting:   { label: 'Iniciando…',  cls: styles.dotStarting },
    connecting: { label: 'Conectando…', cls: styles.dotLoading },
    offline:    { label: 'Offline',     cls: styles.dotOffline },
  }
  const { label, cls } = statusMap[status] ?? statusMap.connecting

  function fmt(ts) {
    const d = new Date(ts)
    const now = new Date()
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }

  return (
    <aside className={styles.sidebar}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.brandDot} />
          <span className={styles.brandName}>DX_IA</span>
          <span className={styles.brandVer}>v2.1</span>
        </div>
        <button className={styles.newBtn} onClick={onNew} title="Nova conversa">
          <Pencil size={15} />
        </button>
      </div>

      {/* ── Status do backend ── */}
      <div className={styles.statusBar}>
        <span className={`${styles.dot} ${cls}`} />
        <span className={styles.statusLabel}>{label}</span>
        {modelInfo?.model && (
          <span className={styles.modelPill}>{modelInfo.model}</span>
        )}
      </div>

      {/* ── Lista de conversas ── */}
      <div className={styles.list}>
        {conversations.length === 0 && (
          <div className={styles.empty}>
            <MessageSquare size={28} opacity={.3} />
            <p>Nenhuma conversa ainda</p>
            <button className={styles.emptyBtn} onClick={onNew}>Começar</button>
          </div>
        )}

        {conversations.map(conv => {
          const last = conv.messages.at(-1)
          const isActive = conv.id === activeId
          return (
            <div
              key={conv.id}
              className={`${styles.item} ${isActive ? styles.itemActive : ''}`}
              onClick={() => onSelect(conv.id)}
            >
              {/* Avatar */}
              <div className={styles.avatar}>
                <span>DX</span>
              </div>

              {/* Info */}
              <div className={styles.info}>
                <div className={styles.itemTop}>
                  <span className={styles.title}>{conv.title}</span>
                  {last && <span className={styles.time}>{fmt(last.ts)}</span>}
                </div>
                {last && (
                  <p className={styles.preview}>
                    {last.role === 'user' ? 'Você: ' : ''}
                    {last.content.slice(0, 48)}
                  </p>
                )}
              </div>

              {/* Deletar */}
              <button
                className={styles.delBtn}
                onClick={e => { e.stopPropagation(); onDelete(conv.id) }}
                title="Excluir"
              >
                <Trash2 size={13} />
              </button>
            </div>
          )
        })}
      </div>

      {/* ── Rodapé ── */}
      <div className={styles.footer}>
        <span>Ollama · Local</span>
        {modelInfo?.cache_size != null && (
          <span>{modelInfo.cache_size} cache</span>
        )}
      </div>
    </aside>
  )
}
