const CURRENCY_CONFIG: Record<string, { locale: string; symbol: string }> = {
  INR: { locale: 'en-IN', symbol: 'INR' },
  USD: { locale: 'en-US', symbol: 'USD' },
  EUR: { locale: 'en-DE', symbol: 'EUR' },
  GBP: { locale: 'en-GB', symbol: 'GBP' },
  AED: { locale: 'ar-AE', symbol: 'AED' },
  SGD: { locale: 'en-SG', symbol: 'SGD' },
  AUD: { locale: 'en-AU', symbol: 'AUD' },
  CAD: { locale: 'en-CA', symbol: 'CAD' },
}

interface CurrencyDisplayProps {
  amount: number
  currency?: string
  showOriginal?: { amount: number; currency: string }
  className?: string
}

export function CurrencyDisplay({
  amount,
  currency = 'INR',
  showOriginal,
  className = '',
}: CurrencyDisplayProps) {
  const config = CURRENCY_CONFIG[currency] ?? { locale: 'en-US', symbol: currency }

  const formatted = new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.symbol,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount)

  if (showOriginal && showOriginal.currency !== currency) {
    const origConfig = CURRENCY_CONFIG[showOriginal.currency] ?? { locale: 'en-US', symbol: showOriginal.currency }
    const origFormatted = new Intl.NumberFormat(origConfig.locale, {
      style: 'currency',
      currency: origConfig.symbol,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(showOriginal.amount)

    return (
      <span className={className}>
        {formatted}{' '}
        <span className="text-[11px]" style={{ color: '#7C85C0' }}>
          ({origFormatted})
        </span>
      </span>
    )
  }

  return <span className={className}>{formatted}</span>
}
