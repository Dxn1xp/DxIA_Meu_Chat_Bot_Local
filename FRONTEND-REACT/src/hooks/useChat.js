/**
 * hooks/useChat.js
 * Gerencia o histórico de conversas e o envio de mensagens.
 */

import { useState, useCallback, useRef } from 'react'
import { sendChat } from '../utils/api'

let msgId = 0
const newId = () => ++msgId

export function useChat() {
  // Lista de conversas na sidebar: [{ id, title, messages, createdAt }]
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId]           = useState(null)
  const [sending, setSending]             = useState(false)
  const bottomRef                         = useRef(null)

  // Conversa atualmente aberta
  const activeConv = conversations.find(c => c.id === activeId) ?? null

  /** Cria uma nova conversa e torna-a ativa */
  const newConversation = useCallback(() => {
    const id = newId()
    setConversations(prev => [
      { id, title: 'Nova conversa', messages: [], createdAt: Date.now() },
      ...prev,
    ])
    setActiveId(id)
  }, [])

  /** Seleciona uma conversa existente */
  const selectConversation = useCallback((id) => setActiveId(id), [])

  /** Deleta uma conversa */
  const deleteConversation = useCallback((id) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    setActiveId(prev => (prev === id ? null : prev))
  }, [])

  /** Envia mensagem na conversa ativa */
  const send = useCallback(async (texto, isReady) => {
    texto = texto.trim()
    if (!texto || sending) return

    if (!isReady) return 'not-ready'

    // Garante que há uma conversa aberta
    let convId = activeId
    if (!convId) {
      const id = newId()
      convId = id
      setConversations(prev => [
        { id, title: texto.slice(0, 36), messages: [], createdAt: Date.now() },
        ...prev,
      ])
      setActiveId(id)
    }

    // Adiciona mensagem do usuário
    const userMsg = { id: newId(), role: 'user', content: texto, ts: Date.now() }
    appendMsg(convId, userMsg)

    // Adiciona placeholder de "digitando"
    const typingMsg = { id: newId(), role: 'typing', content: '', ts: Date.now() }
    appendMsg(convId, typingMsg)

    setSending(true)

    try {
      const resposta = await sendChat(texto)
      // Substitui o placeholder pela resposta real
      replaceMsg(convId, typingMsg.id, {
        id: typingMsg.id,
        role: 'ai',
        content: resposta,
        ts: Date.now(),
      })
      // Atualiza título da conversa com a primeira mensagem
      setConversations(prev =>
        prev.map(c => c.id === convId && c.title === 'Nova conversa'
          ? { ...c, title: texto.slice(0, 36) }
          : c
        )
      )
    } catch (err) {
      replaceMsg(convId, typingMsg.id, {
        id: typingMsg.id,
        role: 'error',
        content: err.name === 'TimeoutError'
          ? '⚠️ Tempo limite. O modelo pode estar processando — tente novamente.'
          : `⚠️ ${err.message}`,
        ts: Date.now(),
      })
    } finally {
      setSending(false)
      // Scroll para o fim
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }, [sending, activeId])

  // ── Helpers internos ─────────────────────────────────────────
  function appendMsg(convId, msg) {
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: [...c.messages, msg] } : c)
    )
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 30)
  }

  function replaceMsg(convId, msgId, newMsg) {
    setConversations(prev =>
      prev.map(c =>
        c.id === convId
          ? { ...c, messages: c.messages.map(m => m.id === msgId ? newMsg : m) }
          : c
      )
    )
  }

  return {
    conversations,
    activeConv,
    activeId,
    sending,
    bottomRef,
    newConversation,
    selectConversation,
    deleteConversation,
    send,
  }
}
