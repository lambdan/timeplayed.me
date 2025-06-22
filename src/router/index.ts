import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../views/HomePage.vue";
import UserPage from "../views/UserPage.vue";
import NewsPage from "../views/NewsPage.vue";
import UserListPage from "../views/UserListPage.vue";
import GameListPage from "../views/GameListPage.vue";
import PlatformListPage from "../views/PlatformListPage.vue";

const routes = [
  { path: "/", component: HomePage },
  {
    path: "/user/:id",
    name: "UserPage",
    component: UserPage,
  },
  { path: "/news", component: NewsPage },
  { path: "/users", component: UserListPage },
  { path: "/games", component: GameListPage },
  { path: "/platforms", component: PlatformListPage },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
