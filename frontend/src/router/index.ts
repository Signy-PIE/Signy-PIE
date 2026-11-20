import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/home",
    },
    {
      path: "/home",
      name: "home",
      component: () => import("../views/view-home.vue"),
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("../views/view-profile.vue"),
    },
    {
      path: "/lexique",
      name: "lexique",
      component: () => import("../views/view-lexique.vue"),
    },
    {
      path: "/lesson/:lessonId",
      name: "lesson",
      component: () => import("../views/view-lesson.vue"),
    },
  ],
})

export default router
