<template>
	<section class="card records-card">
		<div class="card-label">{{ title }}</div>
		<div v-if="loading" class="records-loading">
			<AppSkeleton variant="table" :rows="5" :cols="3" />
		</div>
		<div v-else-if="error" class="records-error">
			<p>{{ errorMessage }}</p>
			<button v-if="onRetry" type="button" class="retry-link" @click="retry">Retry</button>
		</div>
		<div v-else class="records-groups">
			<div v-for="group in groups" :key="group.key" class="records-group">
				<div class="group-label">{{ group.label }}</div>
				<div v-if="!group.rows.length" class="group-empty">
					No {{ group.label.toLowerCase() }} yet.
				</div>
				<template v-else>
					<RecordRow
						v-for="row in group.rows"
						:key="`${row.doctype}-${row.name}`"
						:name="displayName(row)"
						:detail="row.subtitle || ''"
						:status="row.meta || ''"
						@select="emit('select', row)"
					/>
				</template>
			</div>
			<EmptyState v-if="!hasRows" :title="emptyMessage" />
		</div>
	</section>
</template>

<script setup>
import { computed } from 'vue'
import AppSkeleton from './AppSkeleton.vue'
import EmptyState from './EmptyState.vue'
import RecordRow from './RecordRow.vue'

const props = defineProps({
	title: { type: String, default: 'Records' },
	emptyMessage: { type: String, default: 'No records yet.' },
	groups: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	error: { type: [Object, String], default: null },
	onRetry: { type: Function, default: null },
})

const emit = defineEmits(['select'])
const errorMessage = 'Unable to load records. Please try again.'
const hashIdPattern = /^[a-z0-9]{10}$/i
const hasRows = computed(() => props.groups.some((group) => group.rows.length))

function displayName(row) {
	const title = String(row.title || '')
	if (row.doctype !== 'Service Contract') return title || row.name
	if (title && !hashIdPattern.test(title)) return title
	const client = String(row.subtitle || '').trim()
	if (client) return `Contract with ${client}`
	return row.name || title || 'Contract'
}

function retry() {
	if (props.onRetry) props.onRetry()
}
</script>

<style scoped>
.records-card {
	background: var(--color-white);
	border: 1px solid var(--color-gray-200);
	border-radius: var(--radius-lg);
	padding: var(--space-5);
	box-shadow: var(--shadow-xs);
}
.card-label {
	font-size: var(--fs-sm);
	font-weight: 600;
	color: var(--color-gray-700);
	margin-bottom: var(--space-3);
}
.records-loading {
	min-height: 160px;
}
.records-error {
	display: flex;
	align-items: center;
	gap: var(--space-2);
	flex-wrap: wrap;
	padding: var(--space-4);
	border-radius: var(--radius-md);
	background: var(--color-red-50, var(--color-gray-50));
	color: var(--color-red-700, var(--color-gray-700));
	font-size: var(--fs-sm);
}
.records-error p {
	margin: 0;
}
.retry-link {
	border: 0;
	background: transparent;
	color: inherit;
	font-weight: 600;
	cursor: pointer;
	font-family: inherit;
	text-decoration: underline;
}
.records-groups {
	display: grid;
	gap: var(--space-4);
}
.group-label {
	font-size: var(--fs-xs);
	text-transform: uppercase;
	letter-spacing: 0.06em;
	color: var(--color-gray-500);
	margin-bottom: var(--space-2);
}
.group-empty {
	font-size: var(--fs-sm);
	color: var(--color-gray-500);
}
.records-group {
	min-width: 0;
}
</style>
