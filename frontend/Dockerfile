###########
# builder #
###########

FROM node:22 AS builder
WORKDIR /app
# install dependencies
# (only copy in package.json so we don't bust cache on src changes)
COPY package.json package-lock.json ./
RUN npm ci
# copy in rest of src
COPY . .
# build
RUN npm run build

###############
# final image #
###############

# served with nginx
FROM nginx:alpine
# copy in build output
COPY --from=builder /app/dist /html
# copy in custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf
