// src/components/ai/RiskSectionCard.tsx
import React from "react";

interface RiskSectionCardProps {
  title: string;
  children: React.ReactNode;
  accent?: "primary" | "default";
  tone?: "default" | "danger";
  variant?: "solid" | "soft";
}

const RiskSectionCard: React.FC<RiskSectionCardProps> = ({
  title,
  children,
  accent = "default",
  tone = "default",
  variant = "solid",
}) => {
  const classes = [
    "risk-section-card",
    `risk-section-card--accent-${accent}`,
    `risk-section-card--tone-${tone}`,
    `risk-section-card--variant-${variant}`,
  ].join(" ");

  return (
    <section className={classes}>
      <div className="risk-section-card__header">
        <h3 className="risk-section-card__title">{title}</h3>
      </div>
      <div className="risk-section-card__body">{children}</div>
    </section>
  );
};

export default RiskSectionCard;
