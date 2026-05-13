/**
 * ChatWindow.jsx
 * Painel principal do chat: hero (sem conversa) ou histórico de mensagens.
 * Estrutura:
 *   Topbar  ─  área de mensagens  ─  InputBar
 */

import { Settings, X, ChevronLeft } from 'lucide-react'
import OrbSphere     from './OrbSphere'
import MessageBubble from './MessageBubble'
import InputBar      from './InputBar'
import styles        from './ChatWindow.module.css'

// Sugestões de comandos reais do seu Assistant
const CHIPS = [
  { label: '⏱ Que horas são?',    msg: 'Que horas são agora?' },
  { label: '📅 Data de hoje',      msg: 'Qual é a data de hoje?' },
  { label: '📝 Abrir Notepad',     msg: 'abrir bloco de notas' },
  { label: '⚙️ Processos ativos', msg: 'listar processos' },
  { label: '📊 RAM e CPU',         msg: 'monitor' },
  { label: '📷 Screenshot',        msg: 'screenshot' },
  { label: '💾 Status do sistema', msg: 'status' },
  { label: '🧠 Memória',           msg: 'memória' },
]

export default function ChatWindow({
  activeConv,
  sending,
  bottomRef,
  onSend,
  onNew,
  onSettings,
  onClose,
  backendStatus,
}) {
  const hasMessages = activeConv && activeConv.messages.length > 0

  return (
    <div className={styles.window}>

      {/* ── Topbar ── */}
      <div className={styles.topbar}>
        {/* Identidade da conversa ou do assistente */}
        <div className={styles.convInfo}>
          {activeConv ? (
            <>
              <div className={styles.convAvatar}>DX</div>
              <div>
                <p className={styles.convTitle}>{activeConv.title}</p>
                <p className={styles.convSub}>{activeConv.messages.length} mensagens</p>
              </div>
            </>
          ) : (
            <>
              <div className={styles.convAvatar}>DX</div>
              <div>
                <p className={styles.convTitle}>DX_IA Assistant</p>
                <p className={styles.convSub}>Windows AI · Ollama local</p>
              </div>
            </>
          )}
        </div>

        <div className={styles.topActions}>
          <button className={styles.topBtn} onClick={onSettings} title="Configurações">
            <Settings size={16} />
          </button>
          <button className={`${styles.topBtn} ${styles.closeBtn}`} onClick={onClose} title="Fechar">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* ── Área principal ── */}
      <div className={styles.main}>

        {/* HERO: sem mensagens */}
        {!hasMessages && (
          <div className={styles.hero}>
            <p className={styles.heroLabel}>Por onde começamos?</p>

            <OrbSphere status={backendStatus} size={200} />

            {/* Chips de sugestão */}
            <div className={styles.chips}>
              {CHIPS.map(c => (
                <button
                  key={c.msg}
                  className={styles.chip}
                  onClick={() => onSend(c.msg)}
                  disabled={backendStatus !== 'online' || sending}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* CHAT: com mensagens */}
        {hasMessages && (
          <div className={styles.messages}>
            {activeConv.messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Input ── */}
      <InputBar
        onSend={onSend}
        disabled={sending}
        status={backendStatus}
      />
    </div>
  )
}
