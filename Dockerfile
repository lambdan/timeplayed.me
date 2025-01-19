FROM node:22-alpine AS build

WORKDIR /build
COPY package.json package-lock.json tsconfig.json /build/
COPY src /build/src

RUN npm ci
RUN npm run build

FROM node:22-alpine AS final
WORKDIR /app
COPY --from=build /build/dist ./dist
COPY --from=build /build/node_modules ./node_modules

CMD [ "node", "dist/index.js" ]