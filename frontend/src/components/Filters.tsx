import React, { useState } from "react";
import "../styles/filters.css";

import {
  SUBJECT_TYPES,
  PURCHASE_TYPES,
  METHODS,
  FEATURES,
} from "./filters/filtersConstants";
import { MultiSelect } from "./filters/MultiSelect";
import { ChipsFilter } from "./filters/ChipsFilter";

export interface UiFilters {
  keywords: string;
  subjectTypes: string[];
  purchaseTypes: string[];
  methods: string[];
  features: string[];
  amountSort: "" | "asc" | "desc";
}

type FiltersProps = {
  onApply: (filters: UiFilters) => void;
};

const Filters: React.FC<FiltersProps> = ({ onApply }) => {
  const [keywords, setKeywords] = useState("");

  const [selectedSubjectTypes, setSelectedSubjectTypes] = useState<string[]>(
    []
  );
  const [selectedPurchaseTypes, setSelectedPurchaseTypes] = useState<string[]>(
    []
  );
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [amountSort, setAmountSort] = useState<"" | "asc" | "desc">("");

  const initialFilters: UiFilters = {
    keywords: "",
    subjectTypes: [],
    purchaseTypes: [],
    methods: [],
    features: [],
    amountSort: "",
  };

  const handleReset = () => {
    setKeywords("");
    setSelectedSubjectTypes([]);
    setSelectedPurchaseTypes([]);
    setSelectedMethods([]);
    setSelectedFeatures([]);
    setAmountSort("");

    onApply(initialFilters);
  };

  const handleApply = () => {
    onApply({
      keywords,
      subjectTypes: selectedSubjectTypes,
      purchaseTypes: selectedPurchaseTypes,
      methods: selectedMethods,
      features: selectedFeatures,
      amountSort,
    });
  };

  const SORT_LABELS: Record<"" | "asc" | "desc", string[]> = {
    "": [],
    asc: ["По возрастанию"],
    desc: ["По убыванию"],
  };

  const handleAmountSortChange = (selectedLabels: string[]) => {
    const hasAsc = selectedLabels.includes("По возрастанию");
    const hasDesc = selectedLabels.includes("По убыванию");

    let value: "" | "asc" | "desc" = "";

    if (hasAsc && !hasDesc) value = "asc";
    else if (!hasAsc && hasDesc) value = "desc";
    else value = "";

    setAmountSort(value);
  };

  return (
    <aside className="filters">
      <div className="filters__card">
        <div className="filters__header">
          <h2 className="filters__title">Фильтры</h2>
          <button className="filters__reset" onClick={handleReset}>
            Сбросить
          </button>
        </div>

        <p className="filters__subtitle">Уточните поиск по параметрам</p>

        {/* 1. Ключевые слова */}
        <div className="field">
          <span className="field__label">Ключевые слова</span>
          <input
            className="field__input"
            placeholder="Например, дорожные работы"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </div>

        {/* 2. Тип закупки */}
        <ChipsFilter
          label="Тип закупки"
          options={PURCHASE_TYPES}
          selected={selectedPurchaseTypes}
          onChange={setSelectedPurchaseTypes}
        />

        {/* 3. Вид предмета закупок */}
        <MultiSelect
          label="Вид предмета закупок"
          placeholder="Любой"
          options={SUBJECT_TYPES}
          selected={selectedSubjectTypes}
          onChange={setSelectedSubjectTypes}
        />

        {/* 4. Способ проведения закупки */}
        <MultiSelect
          label="Способ проведения закупки"
          placeholder="Любой"
          options={METHODS}
          selected={selectedMethods}
          onChange={setSelectedMethods}
        />

        {/* 5. Признаки закупки */}
        <MultiSelect
          label="Признаки закупки"
          placeholder="Любые"
          options={FEATURES}
          selected={selectedFeatures}
          onChange={setSelectedFeatures}
        />

        {/* 6. Сортировка суммы */}
        <MultiSelect
          label="Сортировка суммы"
          placeholder="Не выбрано"
          options={["По возрастанию", "По убыванию"]}
          selected={SORT_LABELS[amountSort]}
          onChange={handleAmountSortChange}
        />

        {/* Кнопка применить */}
        <button
          type="button"
          className="filters__apply-btn"
          onClick={handleApply}
        >
          Применить фильтры
        </button>
      </div>
    </aside>
  );
};

export default Filters;
