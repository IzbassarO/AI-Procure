import React from "react";
import "../styles/resultsPanel.css";
import type { TenderItem } from "../App";

interface ResultsPanelProps {
  items: TenderItem[];
  total: number;
  page: number;
  pages: number;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
  onAiAnalysis?: (tender: TenderItem) => void;
}

function extractAmount(row: TenderItem): string {
  let raw: any =
    row["Сумма, тг"] ??
    row["Сумма, тг "] ??
    row["Сумма"] ??
    null;

  if (!raw) {
    const key = Object.keys(row).find((k) => k.includes("Сумма"));
    if (key) {
      raw = row[key];
    }
  }

  if (!raw) return "-";

  if (typeof raw === "string") {
    return raw;
  }

  if (typeof raw === "object") {
    const values = Object.values(raw);
    if (values.length > 0) {
      return String(values[0]);
    }
  }

  return "-";
}

function getDeadlineInfo(row: TenderItem) {
  const rawDeadline =
    row["Детали_Срок окончания приема"] ?? row["Окончание приема заявок"];

  if (!rawDeadline || typeof rawDeadline !== "string") {
    return {
      deadlineText: "-",
      relativeText: "-",
    };
  }

  const isoLike = rawDeadline.replace(" ", "T");
  const deadlineDate = new Date(isoLike);
  const now = new Date();

  const msPerDay = 1000 * 60 * 60 * 24;
  const diffMs = deadlineDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / msPerDay);

  let relativeText: string;

  if (Number.isNaN(diffDays)) {
    relativeText = "-";
  } else if (diffDays > 1) {
    relativeText = `${diffDays} дней`;
  } else if (diffDays === 1) {
    relativeText = "1 день";
  } else if (diffDays === 0) {
    relativeText = "Сегодня";
  } else {
    relativeText = "Истёк";
  }

  const yyyy = deadlineDate.getFullYear();
  const mm = String(deadlineDate.getMonth() + 1).padStart(2, "0");
  const dd = String(deadlineDate.getDate()).padStart(2, "0");
  const deadlineText = `${dd}.${mm}.${yyyy}`;

  return { deadlineText, relativeText };
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({
  items,
  total,
  page,
  pages,
  loading,
  error,
  onPageChange,
  onAiAnalysis,
}) => {
  const buildPagination = (): (number | "dots")[] => {
    const visibleCount = 15;
    const pagesArray: (number | "dots")[] = [];

    if (pages <= 7) {
      return Array.from({ length: pages }, (_, i) => i + 1);
    }

    if (page <= 3) {
      pagesArray.push(1, 2, 3, 4, 5, "dots", pages);
      return pagesArray;
    }

    if (page >= pages - 2) {
      pagesArray.push(
        1,
        "dots",
        pages - 4,
        pages - 3,
        pages - 2,
        pages - 1,
        pages
      );
      return pagesArray;
    }

    pagesArray.push(
      1,
      "dots",
      page - 1,
      page,
      page + 1,
      "dots",
      pages
    );

    return pagesArray;
  };

  const paginationItems = buildPagination();

  const pageSize = items.length || 15;
  const startIndex = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endIndex =
    total === 0 ? 0 : Math.min(page * pageSize, total);

  return (
    <section className="results">
      <div className="results__header">
        <div className="results__title">Найдено тендеров: {total}</div>
        <div className="results__subtitle">
          Страница {page} из {pages}
        </div>
      </div>

      {loading && (
        <div className="results__empty">
          <p>Загружаем тендеры…</p>
        </div>
      )}

      {!loading && error && (
        <div className="results__empty results__empty--error">
          <p>Ошибка: {error}</p>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="results__empty">
          <p>Нет результатов.</p>
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="results-list">
            {items.map((row, idx) => {
              const amount = extractAmount(row);
              const { deadlineText, relativeText } = getDeadlineInfo(row);

              const id = row["ID"];
              const title =
                row["Наименование объявления"] ??
                row["Детали_Наименование объявления"];
              const organizer =
                row["Организатор"] ?? row["Общие_Организатор"];
              const status =
                row["Детали_Статус объявления"] ?? row["Статус"];
              const method =
                row["Общие_Способ проведения закупки"] ??
                row["Способ"];
              const purchaseType = row["Общие_Тип закупки"];
              const featuresRaw = row["Общие_Признаки"];
              const features =
                typeof featuresRaw === "string"
                  ? featuresRaw.replace(/[\[\]']/g, "")
                  : "";

              const link = row["Ссылка"];
              const email = row["Организатор_E-Mail"];

              return (
                <div className="tender-card" key={id || idx}>
                  {/* LEFT */}
                  <div className="tender-card__left">
                    <div className="tender-card__days">{relativeText}</div>
                    {method && (
                      <div className="tender-card__pill">
                        <span className="tender-card__dot" />
                        <span>{method}</span>
                      </div>
                    )}
                  </div>

                  {/* MIDDLE */}
                  <div className="tender-card__main">
                    <div className="tender-card__header">
                      <div className="tender-card__title-block">
                        <div className="tender-card__meta">
                          ID: {id}
                        </div>
                        {link ? (
                          <a
                            href={link}
                            target="_blank"
                            rel="noreferrer"
                            className="tender-card__title tender-card__title--link"
                          >
                            {title}
                          </a>
                        ) : (
                          <div className="tender-card__title">
                            {title}
                          </div>
                        )}
                      </div>

                      <div className="tender-card__amount-block">
                        <div className="tender-card__amount">
                          {amount} ₸
                        </div>
                        <div className="tender-card__deadline">
                          Дедлайн: {deadlineText}
                        </div>
                      </div>
                    </div>

                    <div className="tender-card__org-line">
                      {organizer && (
                        <div className="tender-card__org">
                          Организатор: {organizer}
                        </div>
                      )}
                      {email && (
                        <a
                          href={`mailto:${email}`}
                          className="tender-card__email"
                        >
                          {email}
                        </a>
                      )}
                    </div>

                    <div className="tender-card__chips">
                      {status && (
                        <span className="chip chip--status">
                          {status}
                        </span>
                      )}
                      {purchaseType && (
                        <span className="chip">{purchaseType}</span>
                      )}
                      {features && (
                        <span className="chip chip--muted">
                          {features}
                        </span>
                      )}
                      <span className="chip">Kazakhstan</span>
                    </div>

                    {link && (
                      <div className="tender-card__link-row">
                        <a
                          href={link}
                          target="_blank"
                          rel="noreferrer"
                          className="tender-card__link"
                        >
                          Открыть объявление на goszakup →
                        </a>

                        <button
                          type="button"
                          className="ai-analysis-btn"
                          onClick={() =>
                            onAiAnalysis ? onAiAnalysis(row) : console.log("AI Analysis for:", id)
                          }
                        >
                          AI Analysis
                        </button>
                      </div>
                    )}
                  </div>

                  {/* RIGHT */}
                  <div className="tender-card__right">
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Добавить в избранное"
                    >
                      ☆
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Подробнее"
                    >
                      i
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="results__footer">
            <div className="results__shown">
              Показано {startIndex}–{endIndex} из {total} результатов
            </div>

            {pages > 1 && (
              <div className="pagination">
                {paginationItems.map((item, index) =>
                  item === "dots" ? (
                    <span
                      key={`dots-${index}`}
                      className="pagination__dots"
                    >
                      ...
                    </span>
                  ) : (
                    <button
                      key={item}
                      className={
                        "pagination__button" +
                        (item === page
                          ? " pagination__button--active"
                          : "")
                      }
                      onClick={() => onPageChange(item)}
                      disabled={item === page}
                    >
                      {item}
                    </button>
                  )
                )}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
};

export default ResultsPanel;
