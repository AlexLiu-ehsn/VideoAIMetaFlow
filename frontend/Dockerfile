FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .
RUN npm run build-only

# --- 生產環境：Nginx 靜態服務 ---
FROM nginx:alpine

# 複製建置產物
COPY --from=builder /app/dist /usr/share/nginx/html

# 將 nginx.conf 放入 templates 目錄，啟動時自動 envsubst 注入環境變數
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

# nginx 官方映像檔啟動時會自動處理 /etc/nginx/templates/*.template
CMD ["nginx", "-g", "daemon off;"]
