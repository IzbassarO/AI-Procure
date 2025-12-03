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

/** Тип фильтров, которые уйдут в App + бэк */
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
  // Теперь методы – это чипсы, а не dropdown
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

        {/* Ключевые слова */}
        <div className="field">
          <span className="field__label">Ключевые слова</span>
          <input
            className="field__input"
            placeholder="Например, дорожные работы"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </div>

        {/* Виды предмета закупок */}
        <MultiSelect
          label="Вид предмета закупок"
          placeholder="Любой"
          options={SUBJECT_TYPES}
          selected={selectedSubjectTypes}
          onChange={setSelectedSubjectTypes}
        />

        {/* Типы закупок */}
        <MultiSelect
          label="Тип закупки"
          placeholder="Любой"
          options={PURCHASE_TYPES}
          selected={selectedPurchaseTypes}
          onChange={setSelectedPurchaseTypes}
        />

        {/* Способ проведения закупки — ТЕПЕРЬ КАК ЧИПСЫ */}
        <ChipsFilter
          label="Способ проведения закупки"
          options={METHODS}
          selected={selectedMethods}
          onChange={setSelectedMethods}
        />

        {/* Признаки */}
        <MultiSelect
          label="Признаки закупки"
          placeholder="Любые"
          options={FEATURES}
          selected={selectedFeatures}
          onChange={setSelectedFeatures}
        />

        {/* Сортировка суммы */}
        <div className="field">
          <span className="field__label">Сортировка суммы</span>
          <select
            className="field__input"
            value={amountSort}
            onChange={(e) =>
              setAmountSort(e.target.value as "" | "asc" | "desc")
            }
          >
            <option value="">Не выбрано</option>
            <option value="asc">По возрастанию</option>
            <option value="desc">По убыванию</option>
          </select>
        </div>

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
