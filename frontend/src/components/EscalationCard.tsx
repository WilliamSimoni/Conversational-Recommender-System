import styles from './EscalationCard.module.css'

interface Props {
  phone: string
  email: string
}

function PhoneIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  )
}

function MailIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  )
}

export function EscalationCard({ phone, email }: Props) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.icon}>
          <PhoneIcon />
        </div>
        <h4 className={styles.title}>Parla con un nostro assistente</h4>
      </div>
      <p className={styles.description}>
        Il nostro team di supporto è a tua disposizione per aiutarti.
      </p>
      <div className={styles.actions}>
        <a href={`tel:${phone.replace(/\s+/g, '')}`} className={styles.button}>
          <PhoneIcon />
          <span>{phone}</span>
        </a>
        <a href={`mailto:${email}`} className={`${styles.button} ${styles.secondary}`}>
          <MailIcon />
          <span>Invia un'email</span>
        </a>
      </div>
    </div>
  )
}
