import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../views/HomePage.vue";
import UserPage from "../views/UserPage.vue";
import NewsPage from "../views/NewsPage.vue";
import UserListPage from "../views/UserListPage.vue";
import GameListPage from "../views/GameListPage.vue";
import PlatformListPage from "../views/PlatformListPage.vue";
import GamePage from "../views/GamePage.vue";
import PlatformPage from "../views/PlatformPage.vue";
import YearRecapUser from "../views/YearRecapUser.vue";
import HelpPage from "../views/HelpPage.vue";
import ActivityPage from "../views/ActivityPage.vue";

const routes = [
  { path: "/", component: HomePage },
  {
    path: "/user/:id/recap/:year",
    name: "UserRecap",
    component: YearRecapUser,
  },
  {
    path: "/activity/:id",
    name: "ActivityPage",
    component: ActivityPage,
  },
  {
    path: "/user/:id",
    name: "UserPage",
    component: UserPage,
  },
  {
    path: "/game/:id",
    name: "GamePage",
    component: GamePage,
  },
  { path: "/news", component: NewsPage },
  { path: "/help", component: HelpPage },
  { path: "/users", component: UserListPage },
  { path: "/games", component: GameListPage },
  { path: "/platforms", component: PlatformListPage },
  {
    path: "/platform/:id",
    name: "PlatformPage",
    component: PlatformPage,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
