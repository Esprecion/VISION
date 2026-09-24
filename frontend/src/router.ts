import { createRouter, createWebHistory } from 'vue-router'

const businessDevTabs = [
  { label: 'Overview', to: '/business-dev/overview' },
  { label: 'Pipeline', to: '/business-dev/pipeline' },
  { label: 'Clients', to: '/business-dev/clients' },
  { label: 'Products', to: '/business-dev/products' },
]

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/business-dev',
    component: () => import('@/layouts/DepartmentLayout.vue'),
    props: { tabs: businessDevTabs },
    children: [
      { path: '', redirect: '/business-dev/overview' },
      {
        path: 'overview',
        name: 'BusinessDevOverview',
        component: () => import('@/pages/BusinessDevDashboard.vue'),
      },
      {
        path: 'pipeline',
        name: 'Pipeline',
        component: () => import('@/pages/Pipeline.vue'),
      },
      {
        path: 'clients',
        name: 'Clients',
        component: () => import('@/pages/Clients.vue'),
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/pages/Products.vue'),
      },
    ],
  },
]

let router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

export default router
