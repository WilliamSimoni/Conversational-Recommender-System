import type { ProductCard as ProductCardType } from '../types'
import styles from './ProductCard.module.css'

interface Props {
  product: ProductCardType
  index: number
}

function AffinityDots({ value }: { value: number }) {
  const filled = Math.round(value * 5)
  return (
    <div className={styles.affinity}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`${styles.dot} ${i < filled ? styles.dotFilled : ''}`}
        />
      ))}
      <span className={styles.affinityLabel}>{Math.round(value * 100)}% affinity</span>
    </div>
  )
}

export function ProductCard({ product, index }: Props) {
  return (
    <article
      className={styles.card}
      style={{ animationDelay: `${index * 120}ms` }}
    >
      <div className={styles.cardInner}>
        <header className={styles.header}>
          <div className={styles.meta}>
            <span className={styles.house}>Cierge Édition</span>
            {product.in_stock ? (
              <span className={styles.badge}>In Stock</span>
            ) : (
              <span className={`${styles.badge} ${styles.badgeOut}`}>Épuisé</span>
            )}
          </div>
          <h3 className={styles.title}>{product.title}</h3>
          <div className={styles.priceRow}>
            <span className={styles.price}>
              €{product.price.toLocaleString('it-IT')}
            </span>
          </div>
        </header>

        <AffinityDots value={product.affinity} />

        <p className={styles.reason}>{product.reason}</p>

        <a
          href={product.link}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.cta}
        >
          Discover
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 7h10M7 2l5 5-5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </a>
      </div>
    </article>
  )
}
