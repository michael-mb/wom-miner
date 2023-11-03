import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SearchView from "@/views/SearchView.vue";
import DetailView from "@/views/DetailView.vue";
import ExploreView from "@/views/ExploreView.vue";
import AdvancedSearchView from "@/views/AdvancedSearchView.vue";
import FavoritesView from "@/views/FavoritesView.vue";
import AboutView from "@/views/AboutView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/advanced_search',
      name: 'advanced_search',
      component: AdvancedSearchView
    },
    {
      path: '/detail/:index/:id?',
      name: 'detail',
      component: DetailView,
    },
    {
      path: '/graph_viz',
      name: 'graph',
      component: ExploreView
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: FavoritesView
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView
    }
  ]
})

export default router
