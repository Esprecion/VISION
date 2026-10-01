import { createRouter, createWebHistory } from 'vue-router'
import { session } from '@/data/session'

const businessDevTabs = [
  { label: 'Overview', to: '/business-dev/overview' },
  { label: 'Pipeline', to: '/business-dev/pipeline' },
  { label: 'Clients', to: '/business-dev/clients' },
  { label: 'Products', to: '/business-dev/products' },
  { label: 'Contracts', to: '/business-dev/contracts' },
]

const financeTabs = [
  { label: 'Overview', to: '/finance/overview' },
  { label: 'Invoices', to: '/finance/invoices' },
  { label: 'Expenses', to: '/finance/expenses' },
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
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/pages/Contracts.vue'),
      },
    ],
  },
  { path: '/operations/:pathMatch(.*)*', redirect: '/dashboard' },
  {
    path: '/finance',
    component: () => import('@/layouts/DepartmentLayout.vue'),
    props: { tabs: financeTabs },
    children: [
      { path: '', redirect: '/finance/overview' },
      { path: 'overview', name: 'FinanceOverview', component: () => import('@/pages/FinanceOverview.vue') },
      {
        path: 'invoices',
        name: 'FinanceInvoices',
        component: () => import('@/pages/OperationsList.vue'),
        props: {
          title: 'Invoices',
          doctype: 'Invoice',
          createKind: 'Invoice',
          orderBy: 'issue_date desc',
          columns: [
            { key: 'name', label: 'ID' },
            { key: 'client', label: 'Client' },
            { key: 'amount', label: 'Amount', type: 'money' },
            { key: 'issue_date', label: 'Issued' },
            { key: 'due_date', label: 'Due' },
            { key: 'status', label: 'Status' },
            { key: 'owner', label: 'Entered by' },
          ],
        },
      },
      {
        path: 'expenses',
        name: 'FinanceExpenses',
        component: () => import('@/pages/OperationsList.vue'),
        props: {
          title: 'Expenses',
          doctype: 'Expense',
          createKind: 'Expense',
          orderBy: 'expense_date desc',
          columns: [
            { key: 'category', label: 'Category' },
            { key: 'amount', label: 'Amount', type: 'money' },
            { key: 'expense_date', label: 'Date' },
            { key: 'project', label: 'Project' },
            { key: 'owner', label: 'Entered by' },
          ],
        },
      },
    ],
  },
]

let router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

export default router

router.beforeEach((to) => {
  if (!session.isLoggedIn && to.path !== '/dashboard') {
    window.location.href = '/login?redirect-to=/frontend' + to.fullPath
    return false
  }
})
