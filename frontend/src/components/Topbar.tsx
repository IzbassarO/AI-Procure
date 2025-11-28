import React from "react";
import "../styles/topbar.css";

const Topbar: React.FC = () => {
  return (
    <header className="topbar">
      <div className="topbar__left">
        <div className="logo">
          <div className="logo__icon">AI</div>
          <div className="logo__text">
            <div className="logo__title">AI-Procure</div>
            <div className="logo__subtitle">
              Tender &amp; Supplier Risk Intelligence
            </div>
          </div>
        </div>

        <nav className="tabs">
          <button className="tabs__item tabs__item--active">Тендеры</button>
        </nav>
      </div>

      <div className="topbar__right">
        <span className="topbar__project">Hackathon · Forte Bank MVP</span>
        <div className="avatar">IZ</div>
      </div>
    </header>
  );
};

export default Topbar;
