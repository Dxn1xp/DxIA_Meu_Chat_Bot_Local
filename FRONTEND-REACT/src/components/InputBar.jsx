/**
 * InputBar.jsx
 * Barra de input inferior: campo de texto + botões de ação.
 * Inclui Speech-to-Text via Web Speech API.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { Plus, Mic, MicOff, Send } from 'lucide-react'
import styles from './InputBar.module.css'

export default function InputBar({ onSend, disabled, status }) {
  const [text, setText]       = useState('')
  const [recording, setRec]   = useState(false)
  const inputRef              = useRef(null)
  const recRef                = useRef(null)

  // Foco automático
  useEffect(() => { inputRef.current?.focus() }, [])

  // Speech-to-text
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const rec = new SR()
    rec.lang = 'pt-BR'
    rec.continuous = false
    rec.interimResults = false
    rec.onresult = e => {
      const t = e.results[0][0].transcript
      setText(t)
      handleSend(t)
    }
    rec.onend  = () => setRec(false)
    rec.onerror = () => setRec(false)
    recRef.current = rec
  }, [])

  const handleSend = useCallback((override) => {
    const val = (override ?? text).trim()
    if (!val || disabled) return
    onSend(val)
    setText('')
    inputRef.current?.focus()
  }, [text, disabled, onSend])

  const toggleMic = () => {
    if (!recRef.current) return
    if (recording) { recRef.current.stop(); setRec(false) }
    else           { recRef.current.start(); setRec(true) }
  }

  const isReady = status === 'online'

  return (
    <div className={styles.bar}>
      {/* Botão + */}
      <button className={styles.iconBtn} title="Adicionar" disabled>
        <Plus size={18} />
      </button>

      {/* Input */}
      <div className={styles.inputWrap}>
        <input
          ref={inputRef}
          className={styles.input}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
          placeholder={isReady ? 'Pergunte alguma coisa…' : 'Aguardando o Assistant…'}
          disabled={!isReady || disabled}
        />
        {/* Status de digitando dentro do input */}
        {disabled && <span className={styles.thinking}>processando…</span>}
      </div>

      {/* Microfone */}
      <button
        className={`${styles.iconBtn} ${recording ? styles.recording : ''}`}
        onClick={toggleMic}
        disabled={!isReady || disabled}
        title={recording ? 'Parar gravação' : 'Microfone (pt-BR)'}
      >
        {recording ? <MicOff size={18} /> : <Mic size={18} />}
      </button>

      {/* Enviar */}
      <button
        className={`${styles.sendBtn} ${text.trim() && isReady && !disabled ? styles.sendReady : ''}`}
        onClick={() => handleSend()}
        disabled={!text.trim() || !isReady || disabled}
        title="Enviar (Enter)"
      >
        <Send size={17} />
      </button>
    </div>
  )
}
