# Лёгкий Node-образ
FROM node:20-alpine

# Рабочая директория внутри контейнера
WORKDIR /app

# 1. Копируем package.json и lockfile
COPY package*.json ./

# 2. Ставим зависимости
RUN npm install

# 3. Копируем остальной код
COPY . .

# 4. Открываем порт Vite
EXPOSE 5173

# Vite будет брать VITE_API_BASE из environment (задаём в docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
