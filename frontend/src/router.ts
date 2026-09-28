import { createRouter, createWebHistory } from 'vue-router'

const businessDevTabs = [
  { label: 'Overview', to: '/business-dev/overview' },
  { label: 'Pipeline', to: '/business-dev/pipeline' },
  { label: 'Clients', to: '/business-dev/clients' },
  { label: 'Products', to: '/business-dev/products' },
  { label: 'Contracts', to: '/business-dev/contracts' },
]

const operationsTabs = [
  { label: 'Overview', to: '/operations/overview' },
  { label: 'Projects', to: '/operations/projects' },
  { label: 'Engagement Log', to: '/operations/engagement' },
  { label: 'Tools', to: '/operations/tools' },
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
  {
    path: '/operations',
    component: () => import('@/layouts/DepartmentLayout.vue'),
    props: { tabs: operationsTabs },
    children: [
      { path: '', redirect: '/operations/overview' },
      { path: 'overview', name: 'OperationsOverview', component: () => import('@/pages/OperationsOverview.vue') },
      {
        path: 'projects',
        name: 'OpsProjects',
        component: () => import('@/pages/OperationsList.vue'),
        props: {
          title: 'Projects',
          doctype: 'Project',
          columns: [
            { key: 'name', label: 'ID' },
            { key: 'client', label: 'Client' },
            { key: 'project_type', label: 'Type' },
            { key: 'stage', label: 'Stage' },
            { key: 'committed_date', label: 'Committed' },
            { key: 'actual_delivery_date', label: 'Delivered' },
          ],
        },
      },
      {
        path: 'engagement',
        name: 'OpsEngagement',
        component: () => import('@/pages/OperationsList.vue'),
        props: {
          title: 'Client Engagement Log',
          doctype: 'Client Engagement Log',
          orderBy: 'contact_date desc',
          columns: [
            { key: 'client', label: 'Client' },
            { key: 'contact_date', label: 'Date' },
            { key: 'channel', label: 'Channel' },
            { key: 'notes', label: 'Notes' },
          ],
        },
      },
      {
        path: 'tools',
        name: 'OpsTools',
        component: () => import('@/pages/OperationsList.vue'),
        props: {
          title: 'Tool Subscriptions',
          doctype: 'Tool Subscription',
          columns: [
            { key: 'tool_name', label: 'Tool' },
            { key: 'billing_cycle', label: 'Billing' },
            { key: 'current_cost', label: 'Cost', type: 'money' },
            { key: 'renewal_date', label: 'Renewal' },
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
