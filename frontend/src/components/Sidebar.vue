<script setup>
import { computed } from 'vue'
import { session } from '@/data/session'

const modules = [
  { to: '/business-dev', label: 'Business Development', role: 'CBO' },
  { to: '/finance', label: 'Finance', role: 'CFO' },
]

const items = computed(() =>
  modules.map((m) => ({
    ...m,
    editable: session.isAdmin || (m.role === 'CBO' && session.isCBO) ||
      (m.role === 'COO' && session.isCOO) || (m.role === 'CFO' && session.isCFO),
  }))
)
const roleLabel = computed(() =>
  session.isAdmin ? 'Admin' : (['CBO', 'CFO', 'COO'].find((r) => session.roles.includes(r)) || '')
)
function logout() {
  session.logout.submit()
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-brand">VISION</div>
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item" active-class="nav-item-active">
        Dashboard
      </router-link>
      <router-link
        v-for="m in items"
        :key="m.to"
        :to="m.to"
        class="nav-item"
        active-class="nav-item-active"
      >
        {{ m.label }}
        <span v-if="!m.editable" class="badge">View only</span>
      </router-link>
    </nav>
    <div v-if="session.isLoggedIn" class="sidebar-footer">
      <div class="who">
        <div class="who-name">{{ session.user }}</div>
        <div v-if="roleLabel" class="who-role">{{ roleLabel }}</div>
      </div>
      <button type="button" class="logout" @click="logout">Log out</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: var(--color-white);
  border-right: 1px solid var(--color-gray-200);
  padding: 1.5rem 1rem;
}
.sidebar-brand {
  color: var(--color-amber-700);
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 2rem;
  padding: 0 0.5rem;
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-gray-500);
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  text-decoration: none;
}
.nav-item:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}
.nav-item-active {
  background: var(--color-amber-100);
  color: var(--color-amber-700);
  font-weight: 500;
}
.badge {
  font-size: 0.65rem;
  color: var(--color-gray-400);
  background: var(--color-gray-100);
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
}
.sidebar { display: flex; flex-direction: column; }
.sidebar-footer { margin-top: auto; padding-top: 1rem; border-top: 1px solid var(--color-gray-200); }
.who { padding: 0 0.5rem 0.75rem; }
.who-name { font-size: 0.8rem; color: var(--color-gray-900); word-break: break-all; }
.who-role { font-size: 0.7rem; color: var(--color-gray-500); margin-top: 2px; }
.logout { width: 100%; border: 1px solid var(--color-gray-200); background: var(--color-white); border-radius: 6px; padding: 0.5rem; font-size: 0.85rem; color: var(--color-gray-900); cursor: pointer; font-family: inherit; }
.logout:hover { background: var(--color-gray-100); }
</style>
