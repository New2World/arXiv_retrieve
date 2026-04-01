export default function StarRating({ value, onChange, readonly = false }) {
  const stars = [1, 2, 3, 4, 5]

  return (
    <div className={`stars ${readonly ? 'readonly' : ''}`}>
      {stars.map((s) => {
        const isCurrentRating = s === (value || 0)

        return (
          <button
            key={s}
            className={`star ${s <= (value || 0) ? 'filled' : ''}`}
            onClick={() => !readonly && onChange?.(isCurrentRating ? 0 : s)}
            title={readonly ? `${value}/5` : isCurrentRating ? `再次点击清除 ${s} 星评分` : `评分 ${s} 星`}
            type="button"
          >
            ★
          </button>
        )
      })}
    </div>
  )
}
