import React, { useState } from "react";

export type MultiSelectProps = {
  label: string;
  placeholder: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
};

export const MultiSelect: React.FC<MultiSelectProps> = ({
  label,
  placeholder,
  options,
  selected,
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  const toggleOption = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((v) => v !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  const handleSelectAll = () => {
    if (selected.length === options.length) {
      onChange([]);
    } else {
      onChange([...options]);
    }
  };

  const selectedLabel =
    selected.length === 0
      ? placeholder
      : selected.length === options.length
      ? "Выбраны все"
      : `Выбрано: ${selected.length}`;

  return (
    <div className="multi-select">
      <div className="multi-select__label">{label}</div>

      <button
        type="button"
        className={
          "multi-select__control" +
          (selected.length > 0 ? " multi-select__control--active" : "")
        }
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="multi-select__value">{selectedLabel}</span>
        <span className="multi-select__arrow">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="multi-select__menu">
          <div className="multi-select__menu-header">
            <button
              type="button"
              className="multi-select__menu-link"
              onClick={handleSelectAll}
            >
              {selected.length === options.length
                ? "Снять выделение"
                : "Выбрать все"}
            </button>

            <button
              type="button"
              className="multi-select__menu-link"
              onClick={() => setOpen(false)}
            >
              Готово
            </button>
          </div>

          <div className="multi-select__options">
            {options.map((opt) => (
              <label key={opt} className="multi-select__option">
                <input
                  type="checkbox"
                  checked={selected.includes(opt)}
                  onChange={() => toggleOption(opt)}
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
