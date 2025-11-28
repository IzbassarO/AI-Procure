import React, { useState } from "react";
import "../styles/filters.css";

/** Значения из датасета */
const SUBJECT_TYPES = ["Работа", "Товар", "Услуга"];

const PURCHASE_TYPES = [
  "ИОИ от ЗЦП",
  "ИОИ от ЗЦП не ГЗ",
  "ИОИ от Конкурс по приобретению товаров, связанных с обеспечением питания воспитанников и обучающихся",
  "ИОИ от конкурса",
  "Первая закупка",
  "Повторная закупка",
];

const METHODS = [
  "Аукцион",
  "Государственные закупки с применением особого порядка",
  "Закупка жилища",
  "Закупка по государственному социальному заказу",
  "Запрос ценовых предложений",
  "Запрос ценовых предложений (не ГЗ new)",
  "Из одного источника по несостоявшимся закупкам",
  "Из одного источника по несостоявшимся закупкам не ГЗ",
  "Конкурс по приобретению товаров, связанных с обеспечением питания воспитанников и обучающихся",
  "Конкурс по приобретению услуг по организации питания воспитанников и обучающихся",
  "Конкурс с использованием рейтингово-балльной системы",
  "Открытый конкурс",
  "Тендер",
  "Тендер с использованием рейтингово-балльной системы",
];

/** Признаки (из базы) */
const FEATURES = [
  "Без учета НДС",
  "Закупка среди организаций инвалидов",
  "Работы по проектированию",
  "Работы, не связанные со строительством",
  "Строительно-монтажные работы",
];

/** Категории тендеров – чипсы */
const TENDER_CATEGORIES = [
  "Дорожные работы",
  "Строительство и ремонт",
  "IT и программное обеспечение",
  "Медицинские закупки",
  "Оборудование и техника",
  "Транспорт и логистика",
  "Охрана и безопасность",
  "Консалтинг и услуги",
  "Продукты и питание",
  "Прочее",
];

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

type MultiSelectProps = {
  label: string;
  placeholder: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
};

const MultiSelect: React.FC<MultiSelectProps> = ({
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

const Filters: React.FC<FiltersProps> = ({ onApply }) => {
  const [keywords, setKeywords] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

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
    setSelectedCategories([]);
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

  const toggleCategory = (cat: string) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
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

        {/* Категории тендеров (фронтовая категоризация) */}
        <div className="field">
          <span className="field__label">Категории тендеров</span>
          <div className="filter-chips">
            {TENDER_CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                className={
                  "filter-chip" +
                  (selectedCategories.includes(cat)
                    ? " filter-chip--active"
                    : "")
                }
                onClick={() => toggleCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
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

        {/* Способы закупки */}
        <MultiSelect
          label="Способ проведения закупки"
          placeholder="Любой"
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
