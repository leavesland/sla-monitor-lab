# Builds the Next.js app and serves it. Single stage to keep it readable;
# production images usually use a second, smaller stage that copies only the
# build output.

FROM node:22-alpine

WORKDIR /app

# Dependencies first, so editing components later does not re-run npm ci.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
