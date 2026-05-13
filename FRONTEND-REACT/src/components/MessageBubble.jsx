/**
 * MessageBubble.jsx
 * Renderiza uma mensagem individual: usuário, IA, erro ou typing.
 */
import styles from './MessageBubble.module.css'

function fmt(ts) {
  return new Date(ts).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export default function MessageBubble({ msg }) {
  const { role, content, ts } = msg

  if (role === 'typing') {
    return (
      <div className={`${styles.row} ${styles.ai}`}>
        <div className={styles.avatar}>DX</div>
        <div className={`${styles.bubble} ${styles.bubbleAi}`}>
          <div className={styles.typing}>
            <span /><span /><span />
          </div>
        </div>
      </div>
    )
  }

  const isUser  = role === 'user'
  const isError = role === 'error'

  return (
    <div className={`${styles.row} ${isUser ? styles.user : styles.ai}`}>
      {!isUser && <div className={styles.avatar}>DX</div>}

      <div className={`${styles.wrap}`}>
        <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : isError ? styles.bubbleError : styles.bubbleAi}`}>
          {content}
        </div>
        <span className={`${styles.time} ${isUser ? styles.timeUser : ''}`}>
          {fmt(ts)}
        </span>
      </div>

      {isUser && <div className={`${styles.avatar} ${styles.avatarUser}`}>EU</div>}
    </div>
  )
}
