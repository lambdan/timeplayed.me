import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../views/HomePage.vue";
import UserPage from "../views/UserPage.vue";

const routes = [
  { path: "/", component: HomePage },
  {
    path: "/user/:id",
    name: "UserPage",
    component: UserPage,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
