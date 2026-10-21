<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { session } from '@/data/session'
import MenuIcon from '~icons/lucide/menu'
import XIcon from '~icons/lucide/x'

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

const open = ref(false)
const route = useRoute()
watch(() => route.fullPath, () => { open.value = false })

function logout() {
  session.logout.submit()
}
</script>

<template>
  <button
    type="button"
    class="sidebar-toggle"
    :aria-expanded="open"
    aria-label="Open navigation"
    @click="open = true"
  >
    <MenuIcon class="sidebar-toggle__icon" aria-hidden="true" />
  </button>

  <div v-if="open" class="sidebar-backdrop" @click="open = false" />

  <aside class="sidebar" :class="{ 'sidebar--open': open }">
    <div class="sidebar-head">
      <span class="sidebar-brand">VISION</span>
      <button
        type="button"
        class="sidebar-close"
        aria-label="Close navigation"
        @click="open = false"
      >
        <XIcon class="sidebar-close__icon" aria-hidden="true" />
      </button>
    </div>
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
  display: flex;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  background: var(--color-white);
  border-right: 1px solid var(--color-gray-200);
  padding: var(--space-6) var(--space-4);
  position: sticky;
  top: 0;
  height: 100vh;
}
.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}
.sidebar-brand {
  color: var(--color-amber-700);
  font-weight: 700;
  font-size: var(--fs-md);
  letter-spacing: 0.02em;
  padding: 0 var(--space-2);
}
.sidebar-close {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--color-gray-600);
  cursor: pointer;
}
.sidebar-close:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}
.sidebar-close__icon {
  width: 18px;
  height: 18px;
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  color: var(--color-gray-600);
  font-size: var(--fs-sm);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  text-decoration: none;
}
.nav-item:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}
.nav-item-active {
  background: var(--color-amber-100);
  color: var(--color-amber-800);
  font-weight: 500;
}
.badge {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  background: var(--color-gray-100);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  white-space: nowrap;
}
.sidebar-footer {
  margin-top: auto;
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-gray-200);
}
.who {
  padding: 0 var(--space-2) var(--space-3);
}
.who-name {
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
  word-break: break-all;
}
.who-role {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  margin-top: 2px;
}
.logout {
  width: 100%;
  border: 1px solid var(--color-gray-200);
  background: var(--color-white);
  border-radius: var(--radius-sm);
  padding: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
  cursor: pointer;
  font-family: inherit;
}
.logout:hover {
  background: var(--color-gray-100);
}
.sidebar-toggle {
  display: none;
}
.sidebar-backdrop {
  display: none;
}

@media (max-width: 767px) {
  .sidebar-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: var(--space-3);
    left: var(--space-3);
    z-index: 40;
    width: 40px;
    height: 40px;
    border: 1px solid var(--color-gray-200);
    background: var(--color-white);
    border-radius: var(--radius-sm);
    color: var(--color-gray-700);
    cursor: pointer;
    box-shadow: var(--shadow-sm);
  }
  .sidebar-toggle__icon {
    width: 20px;
    height: 20px;
  }
  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    width: min(280px, 85vw);
    height: 100%;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: var(--shadow-md);
  }
  .sidebar--open {
    transform: translateX(0);
  }
  .sidebar-close {
    display: inline-flex;
  }
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 45;
    background: rgba(17, 24, 39, 0.4);
  }
}
</style>
