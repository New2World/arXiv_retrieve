export default function StarRating({ value, onChange, readonly = false }) {
  const stars = [1, 2, 3, 4, 5]
  return (
    <div className={`stars ${readonly ? 'readonly' : ''}`}>
      {stars.map(s => (
        <button
          key={s}
          className={`star ${s <= (value || 0) ? 'filled' : ''}`}
          onClick={() => !readonly && onChange?.(s)}
          title={readonly ? `${value}/5` : `评分 ${s}`}
          type="button"
        >
          ★
        </button>
      ))}
    </div>
  )
}
