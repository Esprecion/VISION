<template>
	<Dialog v-model="show" :options="{ title: 'Record Details', size: 'lg' }">
		<template #body-content>
			<div v-if="loading" class="detail-loading">
				<AppSkeleton variant="table" :rows="5" :cols="2" />
			</div>
			<div v-else-if="error" class="detail-error">
				{{ errorMessage }}
			</div>
			<div v-else-if="fields.length" class="detail-table-wrap">
				<table class="detail-table">
					<tbody>
						<tr v-for="field in fields" :key="field.label">
							<th>{{ field.label }}</th>
							<td>{{ displayValue(field.value) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else class="detail-empty">No details to display.</div>
			<RecordHistoryPanel
				v-if="record?.doctype && record?.name"
				:doctype="record.doctype"
				:docname="record.name"
			/>
		</template>
		<template #actions="{ close }">
			<div class="detail-actions">
				<AppButton variant="outline" size="md" @click="close"> Close </AppButton>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import AppButton from './AppButton.vue'
import AppSkeleton from './AppSkeleton.vue'
import RecordHistoryPanel from './RecordHistoryPanel.vue'
import { displayValue } from '../../utils/format'

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	record: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])
const errorMessage = 'Unable to load records. Please try again.'

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit('update:modelValue', value),
})

const detail = createResource({
	url: 'my_custom_app.shared.dashboard.get_dashboard_record',
	params: {},
	auto: false,
})

const fields = computed(() => detail.data?.fields || [])
const loading = computed(() => detail.loading)
const error = computed(() => detail.error)

watch(
	() => [props.modelValue, props.record],
	([open, record]) => {
		if (!open || !record) return
		detail.update({ params: { doctype: record.doctype, name: record.name } })
		detail.reload()
	},
	{ immediate: true }
)
</script>

<style scoped>
.detail-loading {
	min-height: 200px;
}
.detail-error,
.detail-empty {
	padding: var(--space-4);
	font-size: var(--fs-sm);
	color: var(--color-gray-600);
}
.detail-error {
	color: var(--color-red-700, var(--color-gray-700));
}
.detail-table-wrap {
	overflow-x: auto;
	margin-bottom: var(--space-4);
}
.detail-table {
	width: 100%;
	border-collapse: collapse;
	font-size: var(--fs-sm);
}
.detail-table th,
.detail-table td {
	padding: var(--space-2);
	border-bottom: 1px solid var(--color-gray-100);
	text-align: left;
	vertical-align: top;
}
.detail-table th {
	width: 40%;
	color: var(--color-gray-500);
	font-weight: 500;
}
.detail-table td {
	color: var(--color-gray-900);
}
.detail-actions {
	display: flex;
	justify-content: flex-end;
}
</style>
