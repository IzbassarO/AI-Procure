import React from "react";
import "../styles/searchRow.css";

type SearchRowProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

const SearchRow: React.FC<SearchRowProps> = ({
  value,
  onChange,
  onSubmit,
}) => {
  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="search-row">
      <input
        className="search-row__input"
        placeholder="Поиск по тендерам (название, организатор, описание)…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        className="btn btn--primary"
        type="button"
        onClick={onSubmit}
      >
        Поиск
      </button>
    </div>
  );
};

export default SearchRow;
