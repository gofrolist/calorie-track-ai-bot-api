import { useTranslation } from 'react-i18next';

const PERIODS = [7, 30, 90] as const;
type Period = (typeof PERIODS)[number];

interface PeriodSelectorProps {
  selected: Period;
  onChange: (period: Period) => void;
}

export type { Period };

export function PeriodSelector({ selected, onChange }: PeriodSelectorProps) {
  const { t } = useTranslation();

  const labels: Record<Period, string> = {
    7: t('statistics.period.7days'),
    30: t('statistics.period.30days'),
    90: t('statistics.period.90days'),
  };

  return (
    <div className="flex gap-2" role="group" aria-label={t('statistics.period.title')}>
      {PERIODS.map((period) => (
        <button
          key={period}
          type="button"
          aria-pressed={selected === period}
          onClick={() => onChange(period)}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            selected === period
              ? 'bg-tg-button text-tg-button-text'
              : 'bg-tg-secondary-bg text-tg-hint'
          }`}
        >
          {labels[period]}
        </button>
      ))}
    </div>
  );
}
