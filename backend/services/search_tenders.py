import re
from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss
from pymorphy3 import MorphAnalyzer

tenders = [
    {"id": 1, "title": "Поставка медицинского оборудования",
     "description": "Закупка томографов и расходных материалов для больницы."},

    {"id": 2, "title": "Строительство школы в Астане",
     "description": "Возведение нового учебного корпуса на 600 мест."},

    {"id": 3, "title": "Разработка программного обеспечения",
     "description": "Создание веб-системы для анализа тендеров."},

    {"id": 4, "title": "Поставка мебели и оборудования",
     "description": "Поставка школьных парт, стульев, интерактивных досок."},

    {"id": 5, "title": "Реконструкция автомобильной дороги",
     "description": "Капитальный ремонт трассы длиной 25 км с установкой освещения."},

    {"id": 6, "title": "Закуп топлива",
     "description": "Поставка дизельного топлива и бензина АИ-95 для муниципальной техники."},

    {"id": 7, "title": "Охрана объектов",
     "description": "Предоставление услуг физической охраны для государственных учреждений."},

    {"id": 8, "title": "Уборка городских улиц",
     "description": "Машинная уборка дорог, тротуаров, вывоз снега зимой."},

    {"id": 9, "title": "Канализационные работы",
     "description": "Реконструкция водопроводных и канализационных сетей."},

    {"id": 10, "title": "Поставка канцтоваров",
     "description": "Папки, бумаги, картриджи, принтеры для госорганов."},

    {"id": 11, "title": "IT-аудит государственного портала",
     "description": "Проверка безопасности и оптимизация инфраструктуры."},

    {"id": 12, "title": "Поставка продуктов питания для школ",
     "description": "Закуп овощей, фруктов, круп и мясной продукции."},

    {"id": 13, "title": "Строительство спортивного комплекса",
     "description": "Возведение крытого спортзала с бассейном."},

    {"id": 14, "title": "Обновление городского транспорта",
     "description": "Поставка 50 новых автобусов на газовом топливе."},

    {"id": 15, "title": "Разработка системы видеонаблюдения",
     "description": "Создание и установка IP-камер в госучреждениях."},

    {"id": 16, "title": "Ремонт школьной крыши",
     "description": "Замена кровли, утепление, водоотвод."},

    {"id": 17, "title": "Архитектурное проектирование парка",
     "description": "Создание планировки парка и малых архитектурных форм."},

    {"id": 18, "title": "Поставка серверного оборудования",
     "description": "Серверные стойки, системы хранения данных, маршрутизаторы."},

    {"id": 19, "title": "Разработка мобильного приложения",
     "description": "Приложение для онлайн-запросов и обработки обращений граждан."},

    {"id": 20, "title": "Поставка школьных учебников",
     "description": "Закуп учебных пособий по математике, физике и истории."},

    {"id": 21, "title": "Косметический ремонт здания",
     "description": "Покраска стен, замена пола, ремонт санузлов."},

    {"id": 22, "title": "Строительство детского сада",
     "description": "Здание на 280 мест, игровая площадка и благоустройство."},

    {"id": 23, "title": "Поставка спецодежды",
     "description": "Зимняя и летняя рабочая форма для коммунальщиков."},

    {"id": 24, "title": "Озеленение города",
     "description": "Посадка деревьев, установка системы автоматического полива."},

    {"id": 25, "title": "Поставка лабораторного оборудования",
     "description": "Микроскопы, реагенты, центрифуги для колледжей."},

    {"id": 26, "title": "Обслуживание лифтового оборудования",
     "description": "Регулярный техосмотр и ремонт городских лифтов."},

    {"id": 27, "title": "Строительство ветклиники",
     "description": "Ветеринарная лаборатория, приёмные, хирургический блок."},

    {"id": 28, "title": "Установка пожарной сигнализации",
     "description": "Монтаж датчиков дыма, пожарных щитов, систем оповещения."},

    {"id": 29, "title": "Поставка медикаментов для поликлиник",
     "description": "Лекарственные препараты первой необходимости и расходники."},

    {"id": 30, "title": "Разработка аналитической BI-системы",
     "description": "Панель статистики по закупкам, финансу и KPI госучреждений."},

    {"id": 31, "title": "Капитальный ремонт мостового перехода",
     "description": "Укрепление опор, замена дорожного настила, ограждений."},

    {"id": 32, "title": "Закуп электрооборудования",
     "description": "Трансформаторы, кабельная продукция, распределительные щиты."},

    {"id": 33, "title": "Строительство многоквартирного дома",
     "description": "12-этажный ЖК с парковкой и лифтами."},

    {"id": 34, "title": "Организация конференции",
     "description": "Аренда зала, оборудование, кейтеринг, регистрация участников."}
]

STOPWORDS = {
    "и", "в", "во", "для", "на", "по", "с", "со", "от", "как", "что", "это",
    "к", "до", "из", "у", "же", "бы", "или", "а", "о", "об", "ко", "при"
}

morph = MorphAnalyzer()


def normalize_token(word: str) -> str:
    """Приводим слово к начальной форме (лемме)."""
    parsed = morph.parse(word)[0]
    return parsed.normal_form


def tokenize(text: str):
    words = re.findall(r"[А-Яа-яA-Za-zЁё]+", text.lower())
    return [normalize_token(w) for w in words if w not in STOPWORDS]


documents_text = [t["title"] + " " + t["description"] for t in tenders]
tokenized_docs = [tokenize(doc) for doc in documents_text]
bm25 = BM25Okapi(tokenized_docs)


def search_bm25(query: str, top_k: int = 10):
    tokens = tokenize(query)
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)
    best_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in best_idx:
        if scores[idx] <= 0:
            continue
        tender = tenders[idx]
        results.append({**tender, "bm25_score": float(scores[idx])})
    return results


print("Загружаю embedding-модель...")
model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")
print("Модель загружена.")

print("Строю эмбеддинги корпуса...")
corpus_embeddings = model.encode(documents_text, convert_to_numpy=True)
corpus_embeddings = corpus_embeddings.astype("float32")

faiss.normalize_L2(corpus_embeddings)

dim = corpus_embeddings.shape[1]

M = 32  
index = faiss.IndexHNSWFlat(dim, M)
index.hnsw.efConstruction = 200
index.hnsw.efSearch = 64

index.add(corpus_embeddings)
print(f"FAISS HNSW индекс построен. Документов: {index.ntotal}")


def search_embeddings(query: str, top_k: int = 10, min_score: float = 0.1):
    """Поиск через FAISS HNSW, метрика — косинус (через L2)."""
    if not query.strip():
        return []

    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)

    # distances — это L2^2 между нормализованными векторами
    distances, indices = index.search(q_emb, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        # косинус из L2^2: cos = 1 - 0.5 * L2^2
        cos_sim = 1.0 - 0.5 * float(dist)
        if cos_sim < min_score:
            continue
        tender = tenders[int(idx)]
        results.append({**tender, "embedding_score": cos_sim})

    return results


def hybrid_search(query: str, alpha: float = 0.6, top_k: int = 10):
    bm_results = search_bm25(query, top_k=top_k)
    emb_results = search_embeddings(query, top_k=top_k)

    scores = {}

    for r in bm_results:
        scores[r["id"]] = scores.get(r["id"], 0.0) + r["bm25_score"] * alpha

    for r in emb_results:
        scores[r["id"]] = scores.get(r["id"], 0.0) + r["embedding_score"] * (1.0 - alpha)

    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    final = []
    for tid, score in ranked[:top_k]:
        tender = next(t for t in tenders if t["id"] == tid)
        final.append({**tender, "final_score": round(score, 4)})

    return final



if __name__ == "__main__":
    while True:
        q = input("\nПоиск: ").strip()
        if not q:
            continue

        print("\nHYBRID SEARCH (BM25 + Embeddings + FAISS HNSW) — лучший вариант:")
        results = hybrid_search(q, alpha=0.6, top_k=10)

        if not results:
            print("Ничего не найдено.")
            continue

        for r in results:
            print(f"{r['title']}")