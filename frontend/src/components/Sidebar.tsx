import styles from './Sidebar.module.css'

interface Props {
  onNewRequest: () => void
}

export function Sidebar({ onNewRequest }: Props) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.brandName}>Cierge</span>
        <span className={styles.brandSub}>L'Expert du Parfum</span>
      </div>

      <div className={styles.spacer} />

      <button className={styles.newRequestBtn} onClick={onNewRequest}>
        New Request
      </button>
    </aside>
  )
}
