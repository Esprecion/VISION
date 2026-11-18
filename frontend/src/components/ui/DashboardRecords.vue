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
				<div v-else class="table-scroll">
					<table class="records-table">
						<tbody>
							<tr v-for="row in group.rows" :key="`${row.doctype}-${row.name}`">
								<td>
									<button
										type="button"
										class="record-link"
										@click="emit('select', row)"
									>
										{{ row.title }}
									</button>
								</td>
								<td class="record-subtitle">{{ row.subtitle || '—' }}</td>
								<td class="record-meta">{{ row.meta || '—' }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
			<EmptyState v-if="!hasRows" :title="emptyMessage" />
		</div>
	</section>
</template>

<script setup>
import { computed } from 'vue'
import AppSkeleton from './AppSkeleton.vue'
import EmptyState from './EmptyState.vue'

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
const hasRows = computed(() => props.groups.some((group) => group.rows.length))

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
.table-scroll {
	overflow-x: auto;
}
.records-table {
	width: 100%;
	border-collapse: collapse;
	font-size: var(--fs-sm);
}
.records-table td {
	padding: var(--space-2) var(--space-2);
	border-bottom: 1px solid var(--color-gray-100);
	text-align: left;
	color: var(--color-gray-700);
}
.records-table tr:last-child td {
	border-bottom: 0;
}
.record-link {
	border: 0;
	background: transparent;
	padding: 0;
	color: var(--color-gray-900);
	font-weight: 600;
	cursor: pointer;
	font-family: inherit;
	text-align: left;
}
.record-link:hover {
	text-decoration: underline;
}
.record-subtitle,
.record-meta {
	color: var(--color-gray-500);
}
</style>
