import React, { useEffect, useState } from "react";
import "./styles/global.css";

import Topbar from "./components/Topbar";
import SearchRow from "./components/SearchRow";
import Filters from "./components/Filters";
import type { UiFilters } from "./components/Filters";
import ResultsPanel from "./components/ResultsPanel";
import ChatButton from "./components/ChatButton";

export interface TenderItem {
  [key: string]: any;
}

export interface SearchResponse {
  items: TenderItem[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
}

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";

const App: React.FC = () => {
  const [items, setItems] = useState<TenderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [riskLoading, setRiskLoading] = useState(false);
  const [riskResult, setRiskResult] = useState<any | null>(null);
  const [riskError, setRiskError] = useState<string | null>(null);
  const [riskTender, setRiskTender] = useState<TenderItem | null>(null);

  const [searchText, setSearchText] = useState("");

  const PAGE_SIZE = 15;

  const [filters, setFilters] = useState<UiFilters>({
    keywords: "",
    subjectTypes: [],
    purchaseTypes: [],
    methods: [],
    features: [],
    amountSort: "",
  });

  // универсальный запрос
  const normalizeDateToYMD = (value: any): string | null => {
    if (!value || typeof value !== "string") return null;
    // берём всё до пробела
    const [datePart] = value.split(" ");
    // простая валидация формата YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
      return datePart;
    }
    return null;
  };
  const fetchTenders = async (
    pageToLoad: number,
    filtersOverride?: UiFilters
  ) => {
    const effectiveFilters = filtersOverride ?? filters;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/tenders/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: effectiveFilters.keywords || null,
          filters: {
            // category = Общие_Вид предмета закупок
            category:
              effectiveFilters.subjectTypes.length > 0
                ? effectiveFilters.subjectTypes
                : null,
            // method = Общие_Способ проведения закупки
            method:
              effectiveFilters.methods.length > 0
                ? effectiveFilters.methods
                : null,
            // purchaseType = Общие_Тип закупки
            purchaseType:
              effectiveFilters.purchaseTypes.length > 0
                ? effectiveFilters.purchaseTypes
                : null,
            // features (кастомное поле, добавим в backend)
            features:
              effectiveFilters.features.length > 0
                ? effectiveFilters.features
                : null,
            amountSort: effectiveFilters.amountSort || null,
          },
          page: pageToLoad,
          pageSize: PAGE_SIZE,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: SearchResponse = await res.json();

      setItems(data.items);
      setTotal(data.total);
      setPage(data.page);
      setPages(data.pages);
    } catch (err: any) {
      console.error("Load error:", err);
      setError(err.message || "Load failed");
    } finally {
      setLoading(false);
    }
  };

  // старт – первая страница без фильтров
  useEffect(() => {
    fetchTenders(1);
  }, []);

  const handleSearchSubmit = () => {
    const trimmed = searchText.trim();

    const nextFilters: UiFilters = {
      ...filters,
      keywords: trimmed,
    };

    setFilters(nextFilters);
    fetchTenders(1, nextFilters);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage === page || newPage < 1 || newPage > pages) return;
    fetchTenders(newPage);
  };

  const handleFiltersApply = (nextFilters: UiFilters) => {
    setFilters(nextFilters);
    // при смене фильтров всегда грузим первую страницу
    fetchTenders(1, nextFilters);
  };

  const handleAiAnalysis = async (tender: TenderItem) => {
    setRiskTender(tender);
    setRiskLoading(true);
    setRiskError(null);
    setRiskResult(null);

    const payload = {
      tenders: [
        {
          id: tender["ID"],
          name:
            tender["Наименование объявления"] ??
            tender["Детали_Наименование объявления"],
          price:
            parseFloat(
              String(tender["Сумма, тг"] || "0")
                .replace(/\s/g, "")
                .replace(",", ".")
            ) || 0,
          organizer:
            tender["Организатор"] ?? tender["Общие_Организатор"] ?? "",
          invited_supplier: tender["Приглашенный поставщик"] || "",
          method:
            tender["Общие_Способ проведения закупки"] ??
            tender["Способ"] ??
            "",
          start_date:
            normalizeDateToYMD(
              tender["Дата начала приема"] ??
              tender["Детали_Дата начала приема"]
            ) || "",

          end_date:
            normalizeDateToYMD(
              tender["Окончание приема заявок"] ??
              tender["Детали_Срок окончания приема"]
            ) || "",
        },
      ],
    };

    try {
      const res = await fetch(`${API_BASE}/api/v1/tender-risk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setRiskResult(data);
    } catch (err: any) {
      console.error("AI risk error:", err);
      setRiskError(err.message || "Не удалось получить AI-анализ");
    } finally {
      setRiskLoading(false);
    }
  };

  const closeRiskModal = () => {
    setRiskTender(null);
    setRiskResult(null);
    setRiskError(null);
    setRiskLoading(false);
  };

  return (
    <div className="app">
      <Topbar />

      <main className="main">
        <SearchRow
          value={searchText}
          onChange={setSearchText}
          onSubmit={handleSearchSubmit}
        />

        <div className="content">
          <Filters onApply={handleFiltersApply} />

          <ResultsPanel
            items={items}
            total={total}
            page={page}
            pages={pages}
            loading={loading}
            error={error}
            onPageChange={handlePageChange}
            onAiAnalysis={handleAiAnalysis}
          />
        </div>
      </main>

      {riskTender && (riskLoading || riskResult || riskError) && (
        <div className="risk-modal-overlay">
          <div className="risk-modal">
            <div className="risk-modal__header">
              <div>
                <div className="risk-modal__title">AI-анализ риска тендера</div>
                <div className="risk-modal__subtitle">
                  {riskTender["Наименование объявления"] ??
                    riskTender["Детали_Наименование объявления"] ??
                    riskTender["ID"]}
                </div>
              </div>
              <button
                type="button"
                className="risk-modal__close-btn"
                onClick={closeRiskModal}
              >
                ✕
              </button>
            </div>

            {riskLoading && (
              <div className="risk-modal__loading">
                <div className="risk-spinner" />
                <p>AI анализирует тендер, подождите...</p>
              </div>
            )}

            {!riskLoading && riskError && (
              <div className="risk-modal__error">{riskError}</div>
            )}

            {!riskLoading && riskResult && (
              <div className="risk-modal__content">
                {(() => {
                  const first = riskResult.results?.[0];
                  const a = first?.analysis || {};

                  return (
                    <>
                      <div className="risk-modal__top-row">
                        {a.overall_risk_level && (
                          <span
                            className={`risk-badge risk-badge--${a.overall_risk_level}`}
                          >
                            Уровень риска: {a.overall_risk_level}
                          </span>
                        )}

                        {typeof a.risk_score_estimate === "number" && (
                          <span className="risk-score">
                            {a.risk_score_estimate.toFixed(1)} / 10
                          </span>
                        )}
                      </div>

                      {a.executive_summary && (
                        <section className="risk-section">
                          <h3>Краткое резюме</h3>
                          <p>{a.executive_summary}</p>
                        </section>
                      )}

                      {Array.isArray(a.key_risks) &&
                        a.key_risks.length > 0 && (
                          <section className="risk-section">
                            <h3>Ключевые риски</h3>
                            <ul className="risk-list">
                              {a.key_risks.map((r: any, idx: number) => (
                                <li key={idx}>
                                  <strong>
                                    {r.category} ({r.severity})
                                  </strong>
                                  <div>{r.description}</div>
                                </li>
                              ))}
                            </ul>
                          </section>
                        )}

                      {Array.isArray(a.red_flags) &&
                        a.red_flags.length > 0 && (
                          <section className="risk-section">
                            <h3>Красные флаги</h3>
                            <ul className="risk-list">
                              {a.red_flags.map((t: string, idx: number) => (
                                <li key={idx}>{t}</li>
                              ))}
                            </ul>
                          </section>
                        )}

                      {Array.isArray(a.recommendations) &&
                        a.recommendations.length > 0 && (
                          <section className="risk-section">
                            <h3>Рекомендации</h3>
                            <ul className="risk-list">
                              {a.recommendations.map(
                                (t: string, idx: number) => (
                                  <li key={idx}>{t}</li>
                                )
                              )}
                            </ul>
                          </section>
                        )}
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      )}
      <ChatButton />
    </div>
  );
};

export default App;
