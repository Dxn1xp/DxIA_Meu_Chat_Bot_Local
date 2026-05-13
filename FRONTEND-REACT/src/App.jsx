/**
 * App.jsx — DX_IA Windows Assistant
 *
 * Layout: split-panel (WhatsApp Web)
 *   ┌──────────────┬────────────────────────────┐
 *   │   Sidebar    │       ChatWindow            │
 *   │  (conversas) │  topbar / mensagens / input │
 *   └──────────────┴────────────────────────────┘
 *
 * Estado centralizado aqui, distribuído via props.
 */

import { useState, useCallback } from 'react'
import Sidebar        from './components/Sidebar'
import ChatWindow     from './components/ChatWindow'
import SettingsModal  from './components/SettingsModal'
import { useBackendStatus } from './hooks/useBackendStatus'
import { useChat }          from './hooks/useChat'
import { getStatus }        from './utils/api'
import styles               from './App.module.css'

export default function App() {
  const { state: backendStatus, info, refresh } = useBackendStatus()
  const {
    conversations, activeConv, activeId, sending, bottomRef,
    newConversation, selectConversation, deleteConversation, send,
  } = useChat()

  const [settingsOpen, setSettingsOpen] = useState(false)

  // Envia mensagem — passa o estado de backend para o hook
  const handleSend = useCallback(async (texto) => {
    const result = await send(texto, backendStatus === 'online')
    if (result === 'not-ready') {
      // já trata no InputBar (botão disabled)
    }
  }, [send, backendStatus])

  const handleClose = () => {
    window.close()
    // fallback caso window.close() não funcione (browser blocks it)
    document.title = '⚠️ DX_IA — Feche esta aba manualmente'
  }

  const handleRefreshStatus = () => {
    refresh()
    getStatus().catch(() => {})
  }

  return (
    <div className={styles.layout}>
      {/* ── Sidebar ── */}
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={selectConversation}
        onNew={newConversation}
        onDelete={deleteConversation}
        status={backendStatus}
        modelInfo={info}
      />

      {/* ── Área de chat ── */}
      <ChatWindow
        activeConv={activeConv}
        sending={sending}
        bottomRef={bottomRef}
        onSend={handleSend}
        onNew={newConversation}
        onSettings={() => setSettingsOpen(true)}
        onClose={handleClose}
        backendStatus={backendStatus}
      />

      {/* ── Modal de configurações ── */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        info={info}
        onRefresh={handleRefreshStatus}
      />
    </div>
  )
}
