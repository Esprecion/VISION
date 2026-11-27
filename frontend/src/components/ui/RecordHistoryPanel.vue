<template>
	<div class="record-history">
		<div class="audit-meta">
			<div class="audit-line">
				Created on <strong>{{ formatAuditDateTime(metadata.created_on) }}</strong>
			</div>
			<div class="audit-line">
				Last edited by <strong>{{ formatUser(metadata.modified_by) }}</strong> on
				<strong>{{ formatAuditDateTime(metadata.modified_on) }}</strong>
			</div>
		</div>

		<div class="history-section">
			<button class="history-toggle" type="button" @click="showHistory = !showHistory">
				History ({{ visibleChanges.length }})
				<ChevronDownIcon
					class="history-chevron"
					:class="{ 'history-chevron--open': showHistory }"
					aria-hidden="true"
				/>
			</button>
			<div v-if="showHistory" class="history-body">
				<AppSkeleton v-if="loading" variant="table" :rows="3" :cols="5" />
				<div v-else-if="errorText" class="history-empty">{{ errorText }}</div>
				<div v-else-if="!visibleChanges.length" class="history-empty">
					No changes recorded.
				</div>
				<div v-else class="history-scroll">
					<table class="history-table">
						<thead>
							<tr>
								<th>Field</th>
								<th>Old value</th>
								<th>New value</th>
								<th>User</th>
								<th>Date</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="change in visibleChanges" :key="change.key">
								<td class="history-field">{{ change.label || change.field }}</td>
								<td class="history-old">{{ change.old }}</td>
								<td class="history-new">{{ change.new }}</td>
								<td>{{ formatUser(change.user) }}</td>
								<td class="history-date">{{ formatAuditDateTime(change.date) }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import ChevronDownIcon from '~icons/lucide/chevron-down'
import { formatAuditDateTime } from '@/utils/format'

const props = defineProps({
	doctype: { type: String, required: true },
	docname: { type: String, required: true },
	hiddenFields: { type: Array, default: () => [] },
	refreshKey: { type: Number, default: 0 },
})

const metadata = ref({})
const history = ref([])
const loading = ref(false)
const errorText = ref('')
const showHistory = ref(true)

const visibleChanges = computed(() => {
	const changes = []
	history.value.forEach((entry) => {
		entry.changes.forEach((change, index) => {
			if (props.hiddenFields.includes(change.field)) return
			changes.push({
				...change,
				key: `${entry.name}-${index}`,
				user: entry.owner,
				date: entry.creation,
			})
		})
	})
	return changes
})

function formatUser(email) {
	if (!email) return 'Unknown'
	const namePart = String(email)
		.split('@')[0]
		.replace(/[._-]+/g, ' ')
		.trim()
	if (!namePart) return 'Unknown'
	return namePart.charAt(0).toUpperCase() + namePart.slice(1)
}

async function load() {
	loading.value = true
	errorText.value = ''
	try {
		const data = await call('my_custom_app.shared.dashboard.get_record_history', {
			doctype: props.doctype,
			name: props.docname,
		})
		metadata.value = {
			created_on: data?.metadata?.creation,
			modified_on: data?.metadata?.modified,
			modified_by: data?.metadata?.modified_by || data?.metadata?.owner,
		}
		history.value = data?.history || []
	} catch (error) {
		metadata.value = {}
		history.value = []
		errorText.value = String(
			error?.messages?.[0] || error?.message || 'Unable to load history.'
		).replace(/<[^>]+>/g, '')
	} finally {
		loading.value = false
	}
}

watch(
	() => [props.doctype, props.docname, props.refreshKey],
	([doctype, docname]) => {
		metadata.value = {}
		history.value = []
		errorText.value = ''
		if (doctype && docname) load()
	},
	{ immediate: true }
)
</script>

<style scoped>
.record-history {
	display: flex;
	flex-direction: column;
	gap: var(--space-4);
}
.audit-meta {
	display: flex;
	flex-direction: column;
	gap: var(--space-1);
	font-size: var(--fs-xs);
	color: var(--color-gray-600);
}
.audit-line strong {
	color: var(--color-gray-900);
	font-weight: 600;
}
.history-section {
	border-top: 1px solid var(--color-gray-200);
	padding-top: var(--space-4);
}
.history-toggle {
	display: inline-flex;
	align-items: center;
	gap: var(--space-1);
	background: none;
	border: none;
	cursor: pointer;
	font-weight: 600;
	color: var(--color-gray-900);
	font-size: var(--fs-sm);
	padding: 0;
	font-family: inherit;
}
.history-chevron {
	width: 14px;
	height: 14px;
	color: var(--color-gray-500);
	transition: transform 150ms ease;
}
.history-chevron--open {
	transform: rotate(180deg);
}
.history-body {
	margin-top: var(--space-3);
}
.history-empty {
	font-size: var(--fs-xs);
	color: var(--color-gray-600);
}
.history-scroll {
	overflow-x: auto;
}
.history-table {
	width: 100%;
	border-collapse: collapse;
	font-size: var(--fs-xs);
	min-width: 560px;
}
.history-table th,
.history-table td {
	text-align: left;
	padding: var(--space-2);
	border-bottom: 1px solid var(--color-gray-100);
	vertical-align: top;
}
.history-table th {
	color: var(--color-gray-600);
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.03em;
}
.history-field {
	font-weight: 600;
	color: var(--color-gray-900);
}
.history-old {
	color: var(--color-amber-700);
	text-decoration: line-through;
}
.history-new {
	color: var(--color-gray-900);
	font-weight: 600;
}
.history-date {
	white-space: nowrap;
	color: var(--color-gray-500);
}
</style>
