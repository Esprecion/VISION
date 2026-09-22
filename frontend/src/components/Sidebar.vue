<template>
  <aside class="sidebar">
    <div class="sidebar-brand">VISION</div>
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item" active-class="nav-item-active">
        Dashboard
      </router-link>
      <router-link to="/business-dev" class="nav-item" active-class="nav-item-active">
        Business Dev
      </router-link>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 1.5rem 1rem;
}
.sidebar-brand {
  color: #b45309;
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
  color: #6b7280;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  text-decoration: none;
}
.nav-item:hover {
  background: #f3f4f6;
  color: #111827;
}
.nav-item-active {
  background: #fef3c7;
  color: #b45309;
  font-weight: 500;
}
</style>
