import React, { useState, useRef } from "react";
import "../styles/chatButton.css";

type MessageRole = "user" | "bot";

interface Message {
  id: number;
  role: MessageRole;
  text: string;
}

type TabKey = "home" | "tickets" | "contacts";

const FAQ_SHORT = [
  "Изменение процента аванса в дополнительном соглашении",
  "Ошибка при авторизации",
  "Условия участия в тендере для малого бизнеса",
];

const FAQ_FULL = [
  ...FAQ_SHORT,
  "Как найти тендер по конкретному региону?",
  "Как отфильтровать только рисковые тендеры?",
];

const BOT_STUB_TEXT =
  "Это тестовый ответ ассистента. Позже здесь будет реальный анализ тендера по вашему вопросу.";

const ChatButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [faqExpanded, setFaqExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const [inChatMode, setInChatMode] = useState(false);
  const msgIdRef = useRef(1);

  const nextId = () => msgIdRef.current++;

  const handleToggleOpen = () => {
    setIsOpen((prev) => !prev);
  };

  const handleStartConversation = (question: string) => {
    const firstMsg: Message = {
      id: nextId(),
      role: "user",
      text: question,
    };
    const botReply: Message = {
      id: nextId(),
      role: "bot",
      text: BOT_STUB_TEXT,
    };
    setMessages([firstMsg, botReply]);
    setInChatMode(true);
    setActiveTab("home");
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMsg: Message = {
      id: nextId(),
      role: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setInChatMode(true);
    setIsTyping(true);

    try {
      // TODO: здесь подключишь реальный вызов Groq / LLM
      // пример:
      // const res = await fetch("https://your-llm-endpoint", {...});
      // const data = await res.json();
      // const answerText = data.answer;
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const answerText = BOT_STUB_TEXT;

      const botMsg: Message = {
        id: nextId(),
        role: "bot",
        text: answerText,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      const errMsg: Message = {
        id: nextId(),
        role: "bot",
        text: "Не удалось получить ответ от ассистента. Попробуйте ещё раз.",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleScrollTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const currentFaq = faqExpanded ? FAQ_FULL : FAQ_SHORT;

  return (
    <>
      {/* Лаунчер: стрелка вверх + ряд "плашка + круглая кнопка" */}
      <div className="chat-launcher">
        {/* кнопка скролла вверх */}
        <button
          type="button"
          className="chat-launcher__scroll"
          onClick={handleScrollTop}
          aria-label="Наверх"
        >
          ↑
        </button>

        <div className="chat-launcher__row">
          {/* плашка тоже кнопка */}
          <button
            type="button"
            className="chat-launcher__pill"
            onClick={handleToggleOpen}
          >
            {isOpen ? "Отмена" : "Чем я могу Вам помочь?"}
          </button>

          {/* основная круглая кнопка */}
          <button
            type="button"
            className="chat-launcher__main"
            onClick={handleToggleOpen}
            aria-label={isOpen ? "Закрыть чат-бота @AI-Procure_BizAI" : "Открыть чат-бота"}
          >
            {isOpen ? "✕" : "🎧"}
          </button>
        </div>
      </div>

      {/* Само окно чата */}
      {isOpen && (
        <div className="chat-window">
          {/* header */}
          <div className="chat-window__header">
            <div className="chat-window__title-block">
              <div className="chat-window__avatar">AI</div>
              <div>
                <div className="chat-window__title">AI-Procure Smart Bot</div>
                <div className="chat-window__subtitle">
                  Помощник по тендерам и закупкам
                </div>
              </div>
            </div>
            <button
              className="chat-window__close"
              type="button"
              onClick={handleToggleOpen}
            >
              ✕
            </button>
          </div>

          {/* контент */}
          <div className="chat-window__body">
            {activeTab === "home" && !inChatMode && (
              <div className="chat-faq">
                <div className="chat-faq__header">
                  <div className="chat-faq__title">
                    Часто задаваемые вопросы
                  </div>
                  {faqExpanded ? (
                    <button
                      type="button"
                      className="chat-faq__link"
                      onClick={() => setFaqExpanded(false)}
                    >
                      Закрыть
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="chat-faq__link"
                      onClick={() => setFaqExpanded(true)}
                    >
                      Показать все
                    </button>
                  )}
                </div>

                <div className="chat-faq__list">
                  {currentFaq.map((q) => (
                    <button
                      key={q}
                      type="button"
                      className="chat-faq__item"
                      onClick={() => handleStartConversation(q)}
                    >
                      <span>{q}</span>
                      <span className="chat-faq__icon">📄</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "home" && inChatMode && (
              <div className="chat-messages">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={
                      "chat-message " +
                      (m.role === "user"
                        ? "chat-message--user"
                        : "chat-message--bot")
                    }
                  >
                    <div className="chat-message__text">{m.text}</div>
                  </div>
                ))}

                {isTyping && (
                  <div className="chat-typing">
                    <span className="chat-typing__dot" />
                    <span className="chat-typing__dot" />
                    <span className="chat-typing__dot" />
                  </div>
                )}
              </div>
            )}

            {activeTab === "tickets" && (
              <div className="chat-section">
                <h3 className="chat-section__title">Обращения</h3>
                <div className="chat-faq__list">
                  <button
                    type="button"
                    className="chat-faq__item"
                  >
                    <span>Форма обратной связи AI-Procure</span>
                    <span className="chat-faq__icon">📝</span>
                  </button>
                  <button
                    type="button"
                    className="chat-faq__item"
                  >
                    <span>Проверка статуса заявки</span>
                    <span className="chat-faq__icon">🔍</span>
                  </button>
                </div>
              </div>
            )}

            {activeTab === "contacts" && (
              <div className="chat-section">
                <h3 className="chat-section__title">Инфо</h3>

                <div className="contacts-box">
                  <div className="contacts-row">
                    <span className="contacts-icon">📞</span>
                    <span className="contacts-text">+7 (708) 904 05 59</span>
                  </div>

                  <div className="contacts-row">
                    <span className="contacts-icon">📞</span>
                    <span className="contacts-text">+7 777 382 99 20</span>
                  </div>

                  <div className="contacts-row">
                    <span className="contacts-icon">✈️</span>
                    <span className="contacts-text">Telegram Чат-бот</span>
                  </div>

                  <div className="contacts-row">
                    <span className="contacts-icon">📧</span>
                    <span className="contacts-text">izok2004@gmail.com</span>
                  </div>

                  <div className="contacts-row">
                    <span className="contacts-icon">📧</span>
                    <span className="contacts-text">iorynbass@ltu.edu</span>
                  </div>

                  <div className="contacts-row">
                    <span className="contacts-icon">🌐</span>
                    <span className="contacts-text">Сменить язык</span>
                    <span className="contacts-right">Рус</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* input + отправка — только на вкладке home */}
          {activeTab === "home" && (
            <div className="chat-input-row">
              <input
                className="chat-input"
                placeholder="Сообщение"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button
                type="button"
                className="chat-send"
                onClick={sendMessage}
                disabled={isTyping}
              >
                ➤
              </button>
            </div>
          )}

          {/* нижние табы */}
          <div className="chat-tabs">
            <button
              type="button"
              className={
                "chat-tab" +
                (activeTab === "home" ? " chat-tab--active" : "")
              }
              onClick={() => setActiveTab("home")}
            >
              <span className="chat-tab__icon">🏠</span>
              <span className="chat-tab__label">ГЛАВНАЯ</span>
            </button>
            <button
              type="button"
              className={
                "chat-tab" +
                (activeTab === "tickets" ? " chat-tab--active" : "")
              }
              onClick={() => setActiveTab("tickets")}
            >
              <span className="chat-tab__icon">🧾</span>
              <span className="chat-tab__label">ОБРАЩЕНИЯ</span>
            </button>
            <button
              type="button"
              className={
                "chat-tab" +
                (activeTab === "contacts" ? " chat-tab--active" : "")
              }
              onClick={() => setActiveTab("contacts")}
            >
              <span className="chat-tab__icon">≡</span>
              <span className="chat-tab__label">КОНТАКТЫ</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatButton;
