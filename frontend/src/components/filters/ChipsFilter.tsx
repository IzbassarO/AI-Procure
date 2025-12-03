import React from "react";

type ChipsFilterProps = {
  label: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
};

export const ChipsFilter: React.FC<ChipsFilterProps> = ({
  label,
  options,
  selected,
  onChange,
}) => {
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="field">
      <span className="field__label">{label}</span>
      <div className="filter-chips">
        {options.map((opt) => (
          <button
            key={opt}
            type="button"
            className={
              "filter-chip" +
              (selected.includes(opt) ? " filter-chip--active" : "")
            }
            onClick={() => toggle(opt)}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
};
