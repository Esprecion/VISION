import { createRouter, createWebHistory } from 'vue-router'
import { ensureAdminAccess, ensureSessionData, session } from '@/data/session'

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

const operationsTabs = [
  { label: 'Overview', to: '/operations/overview' },
  { label: 'Projects', to: '/operations/projects' },
  { label: 'Tools', to: '/operations/tools' },
  { label: 'Engagement Logs', to: '/operations/engagements' },
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
    meta: { module: 'business_dev' },
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
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/pages/AdminUsers.vue'),
    meta: { requiresAdmin: true },
  },
  {
    path: '/operations',
    component: () => import('@/layouts/DepartmentLayout.vue'),
    props: { tabs: operationsTabs },
    meta: { module: 'operations' },
    children: [
      { path: '', redirect: '/operations/overview' },
      {
        path: 'overview',
        name: 'OperationsOverview',
        component: () => import('@/pages/OperationsOverview.vue'),
      },
      {
        path: 'projects',
        name: 'OperationsProjects',
        component: () => import('@/pages/OperationsRecords.vue'),
        props: {
          title: 'Projects',
          doctype: 'Project',
          kind: 'Project',
          orderBy: 'modified desc',
          columns: [
            { key: 'name', label: 'Project' },
            { key: 'client', label: 'Client' },
            { key: 'project_type', label: 'Type' },
            { key: 'stage', label: 'Stage', type: 'status' },
            { key: 'committed_date', label: 'Committed' },
            { key: 'actual_delivery_date', label: 'Delivered' },
          ],
        },
      },
      {
        path: 'tools',
        name: 'OperationsTools',
        component: () => import('@/pages/OperationsRecords.vue'),
        props: {
          title: 'Tools',
          doctype: 'Tool Subscription',
          kind: 'Tool',
          orderBy: 'renewal_date asc',
          columns: [
            { key: 'tool_name', label: 'Tool' },
            { key: 'billing_cycle', label: 'Billing' },
            { key: 'current_cost', label: 'Cost', type: 'money' },
            { key: 'renewal_date', label: 'Renewal' },
          ],
        },
      },
      {
        path: 'engagements',
        name: 'OperationsEngagements',
        component: () => import('@/pages/OperationsRecords.vue'),
        props: {
          title: 'Engagement Logs',
          doctype: 'Client Engagement Log',
          kind: 'Engagement',
          orderBy: 'contact_date desc',
          columns: [
            { key: 'client', label: 'Client' },
            { key: 'contact_date', label: 'Date' },
            { key: 'channel', label: 'Channel', type: 'status' },
            { key: 'notes', label: 'Notes' },
          ],
        },
      },
    ],
  },
  {
    path: '/finance',
    component: () => import('@/layouts/DepartmentLayout.vue'),
    props: { tabs: financeTabs },
    meta: { module: 'finance' },
    children: [
      { path: '', redirect: '/finance/overview' },
      { path: 'overview', name: 'FinanceOverview', component: () => import('@/pages/FinanceOverview.vue') },
      {
        path: 'invoices',
        name: 'FinanceInvoices',
        component: () => import('@/pages/FinanceList.vue'),
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
        component: () => import('@/pages/FinanceList.vue'),
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
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

let router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

export default router

router.beforeEach(async (to) => {
  if (!session.isLoggedIn && to.path !== '/dashboard') {
    window.location.href = '/login?redirect-to=/frontend' + to.fullPath
    return false
  }
  await ensureSessionData()
  if (to.meta.requiresAdmin && !(await ensureAdminAccess())) {
    return { path: '/dashboard' }
  }
  const module = to.meta.module as string | undefined
  if (module && !session.canRead(module)) {
    return { path: '/dashboard' }
  }
})
