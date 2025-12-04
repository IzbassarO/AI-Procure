// src/components/RiskAnalysisModal.tsx
import React from "react";
import "../styles/risk.css";
import type { TenderItem } from "../App";
import type { TenderRiskResponse } from "../types/risk";

interface RiskAnalysisModalProps {
  tender: TenderItem;
  result: TenderRiskResponse | null;
  loading: boolean;
  error: string | null;
  downloadingPdf: boolean;
  onClose: () => void;
  onDownloadPdf: () => void;
}

const RiskAnalysisModal: React.FC<RiskAnalysisModalProps> = ({
  tender,
  result,
  loading,
  error,
  downloadingPdf,
  onClose,
  onDownloadPdf,
}) => {
  const first = result?.results?.[0];
  const a = first?.analysis || {};

  const title =
    tender["Наименование объявления"] ??
    tender["Детали_Наименование объявления"] ??
    tender["ID"];

  return (
    <div className="risk-modal-overlay">
      <div className="risk-modal">
        {/* HEADER */}
        <div className="risk-modal__header">
          <div>
            <div className="risk-modal__title">AI-анализ риска тендера</div>
            <div className="risk-modal__subtitle">{title}</div>
          </div>
          <button
            type="button"
            className="risk-modal__close-btn"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* LOADING / ERROR / CONTENT */}
        {loading && (
          <div className="risk-modal__loading">
            <div className="risk-spinner" />
            <p>AI анализирует тендер, подождите...</p>
          </div>
        )}

        {!loading && error && (
          <div className="risk-modal__error">{error}</div>
        )}

        {!loading && !error && result && (
          <div className="risk-modal__content">
            {/* ==== TOP STRIP ==== */}
            {(a.overall_risk_level ||
              typeof a.risk_score_estimate === "number" ||
              typeof a.investment_opportunity_score === "number") && (
              <div className="risk-topstrip">
                <div className="risk-topstrip__left">
                  {a.overall_risk_level && (
                    <span
                      className={`risk-badge risk-badge--${a.overall_risk_level}`}
                    >
                      Уровень риска: {a.overall_risk_level}
                    </span>
                  )}

                  <div className="risk-topstrip__scores">
                    {typeof a.risk_score_estimate === "number" && (
                      <div className="risk-score-pill">
                        <div className="risk-score-pill__label">
                          Риск-скор
                        </div>
                        <div className="risk-score-pill__value">
                          {a.risk_score_estimate.toFixed(1)} / 10
                        </div>
                      </div>
                    )}

                    {typeof a.investment_opportunity_score === "number" && (
                      <div className="risk-score-pill">
                        <div className="risk-score-pill__label">
                          Инвест. потенциал
                        </div>
                        <div className="risk-score-pill__value">
                          {a.investment_opportunity_score}/10
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="risk-topstrip__right">
                  <button
                    className="risk-topstrip__button"
                    onClick={onDownloadPdf}
                    disabled={downloadingPdf}
                  >
                    {downloadingPdf
                      ? "Генерация PDF..."
                      : "Скачать PDF-отчёт"}
                  </button>
                </div>
              </div>
            )}

            {/* ==== SECTIONS ==== */}
            {a.executive_summary && (
              <section className="risk-section">
                <h3>Краткое резюме</h3>
                <p>{a.executive_summary}</p>
              </section>
            )}

            {Array.isArray(a.positive_factors) &&
              a.positive_factors.length > 0 && (
                <section className="risk-section">
                  <h3>Позитивные факторы</h3>
                  <ul className="risk-list">
                    {a.positive_factors.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </section>
              )}

            {Array.isArray(a.red_flags) && a.red_flags.length > 0 && (
              <section className="risk-section">
                <h3>Красные флаги</h3>
                <ul className="risk-list">
                  {a.red_flags.map((t, idx) => (
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
                    {a.recommendations.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </section>
              )}

            {Array.isArray(a.key_risks) && a.key_risks.length > 0 && (
              <section className="risk-section">
                <h3>Ключевые риски</h3>
                <ul className="risk-list">
                  {a.key_risks.map((r, idx) => (
                    <li key={idx} className="risk-key-item">
                      <div className="risk-key-item__header">
                        <span className="risk-key-item__category">
                          {r.category}
                        </span>
                        <span className="risk-key-item__severity">
                          ({r.severity})
                        </span>
                      </div>
                      <div className="risk-key-item__desc">
                        {r.description}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {Array.isArray(a.banking_products) &&
              a.banking_products.length > 0 && (
                <section className="risk-section">
                  <h3>Банковские продукты</h3>
                  <ul className="risk-list">
                    {a.banking_products.map((bp, idx) => (
                      <li key={idx}>
                        <div className="risk-product-item__name">
                          {bp.product}
                        </div>
                        {bp.justification && (
                          <div className="risk-product-item__line">
                            Обоснование: {bp.justification}
                          </div>
                        )}
                        {bp.conditions && (
                          <div className="risk-product-item__line">
                            Условия: {bp.conditions}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

            {Array.isArray(a.manager_checklist) &&
              a.manager_checklist.length > 0 && (
                <section className="risk-section">
                  <h3>Чек-лист для менеджера</h3>
                  <ul className="risk-list">
                    {a.manager_checklist.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </section>
              )}

            {Array.isArray(a.investment_risks) &&
              a.investment_risks.length > 0 && (
                <section className="risk-section">
                  <h3>Инвестиционные риски</h3>
                  <ul className="risk-list">
                    {a.investment_risks.map((t, idx) => (
                      <li key={idx}>{t}</li>
                    ))}
                  </ul>
                </section>
              )}

            {a.detailed_analysis && (
              <section className="risk-section">
                <h3>Детальный анализ</h3>
                <p className="risk-detailed-text">
                  {a.detailed_analysis}
                </p>
              </section>
            )}

            {/* можно оставить JSON в конце, по желанию */}
            <section className="risk-section risk-section--raw-json">
              <details>
                <summary>Показать сырой JSON ответа</summary>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </details>
            </section>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskAnalysisModal;
