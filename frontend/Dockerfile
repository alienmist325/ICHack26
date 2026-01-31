FROM node:20-alpine

WORKDIR /home/app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml* ./

RUN pnpm install --quiet

COPY . .

RUN pnpm run build

EXPOSE 5173

CMD ["pnpm", "dev"]
