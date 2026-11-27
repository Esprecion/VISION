<script setup>
import { ref, computed } from 'vue'
import { createResource, call } from 'frappe-ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import AppSearchInput from '@/components/ui/AppSearchInput.vue'
import { displayValue, formatCurrency } from '@/utils/format'
import PlusIcon from '~icons/lucide/plus'
import AlertCircleIcon from '~icons/lucide/alert-circle'

const list = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'Client Payment',
		fields: [
			'name',
			'invoice',
			'client',
			'amount',
			'payment_date',
			'payment_method',
			'reference',
		],
		order_by: 'payment_date desc',
		limit_page_length: 500,
	},
	auto: true,
})

const invoices = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'Invoice',
		fields: ['name', 'client', 'amount', 'paid_amount', 'outstanding_amount'],
		order_by: 'due_date asc',
		limit_page_length: 500,
	},
	auto: true,
})

const search = ref('')
const msg = ref('')
const showForm = ref(false)
const editName = ref(null)
const originalInvoice = ref('')
const originalAmount = ref(0)
const saving = ref(false)
const form = ref({
	invoice: '',
	amount: null,
	payment_date: '',
	payment_method: 'Cash',
	reference: '',
})

const showConfirm = ref(false)
const pendingDelete = ref(null)
const deleting = ref(false)

const rows = computed(() => {
	const q = search.value.trim().toLowerCase()
	return (list.data ?? []).filter((r) =>
		q
			? Object.values(r).some((v) =>
					String(v ?? '')
						.toLowerCase()
						.includes(q)
			  )
			: true
	)
})
const total = computed(() => rows.value.reduce((t, r) => t + Number(r.amount || 0), 0))
const invoiceOptions = computed(() => invoices.data ?? [])
const listError = computed(() =>
	String(list.error?.messages?.[0] || list.error?.message || 'Something went wrong').replace(
		/<[^>]+>/g,
		''
	)
)
const errText = (e) =>
	String(e?.messages?.[0] || e?.message || 'Something went wrong').replace(/<[^>]+>/g, '')

function availableFor(invoice) {
	const balance = Number(invoice?.outstanding_amount || 0)
	if (editName.value && form.value.invoice === invoice?.name) {
		return balance + Number(originalAmount.value || 0)
	}
	return balance
}
const selectedInvoice = computed(() =>
	invoiceOptions.value.find((i) => i.name === form.value.invoice)
)

function resetForm() {
	form.value = {
		invoice: '',
		amount: null,
		payment_date: '',
		payment_method: 'Cash',
		reference: '',
	}
	editName.value = null
	originalInvoice.value = ''
	originalAmount.value = 0
	msg.value = ''
}

function openNew() {
	resetForm()
	showForm.value = true
}

async function openEdit(r) {
	resetForm()
	try {
		const d = await call('frappe.client.get', { doctype: 'Client Payment', name: r.name })
		form.value = {
			invoice: d.invoice || '',
			amount: d.amount || null,
			payment_date: d.payment_date || '',
			payment_method: d.payment_method || 'Cash',
			reference: d.reference || '',
		}
		editName.value = d.name
		originalInvoice.value = d.invoice || ''
		originalAmount.value = Number(d.amount || 0)
		showForm.value = true
	} catch (e) {
		msg.value = errText(e)
	}
}

async function save() {
	msg.value = ''
	if (
		!form.value.invoice ||
		!form.value.amount ||
		!form.value.payment_date ||
		!form.value.payment_method
	) {
		msg.value = 'Please complete all required payment details.'
		return
	}
	if (Number(form.value.amount) > availableFor(selectedInvoice.value)) {
		msg.value = 'The payment cannot exceed the outstanding balance.'
		return
	}
	saving.value = true
	try {
		const doc = {
			doctype: 'Client Payment',
			invoice: form.value.invoice,
			amount: Number(form.value.amount),
			payment_date: form.value.payment_date,
			payment_method: form.value.payment_method,
			reference: form.value.reference,
		}
		if (editName.value) {
			doc.name = editName.value
			await call('frappe.client.save', { doc })
		} else {
			await call('frappe.client.insert', { doc })
		}
		showForm.value = false
		list.reload()
		invoices.reload()
	} catch (e) {
		msg.value = errText(e)
	} finally {
		saving.value = false
	}
}

function askDelete(r) {
	pendingDelete.value = r
	showConfirm.value = true
}

async function doDelete() {
	if (!pendingDelete.value) return
	msg.value = ''
	deleting.value = true
	try {
		await call('frappe.client.delete', {
			doctype: 'Client Payment',
			name: pendingDelete.value.name,
		})
		showConfirm.value = false
		list.reload()
		invoices.reload()
	} catch (e) {
		msg.value = errText(e)
		showConfirm.value = false
	} finally {
		deleting.value = false
		pendingDelete.value = null
	}
}
</script>

<template>
	<div class="page">
		<PageHeader title="Client Payments">
			<template #actions>
				<div class="head-right">
					<AppSearchInput
						v-model="search"
						label="Search payments"
						placeholder="Search payments..."
					/>
					<AppButton variant="solid" theme="gray" @click="openNew">
						<template #prefix><PlusIcon aria-hidden="true" /></template>
						New Payment
					</AppButton>
				</div>
			</template>
		</PageHeader>

		<div class="summary">Showing {{ rows.length }} payments · {{ formatCurrency(total) }}</div>
		<div v-if="msg" class="err" role="alert">
			<AlertCircleIcon aria-hidden="true" />
			<span>{{ msg }}</span>
		</div>

		<div class="card">
			<ErrorState
				v-if="list.error"
				title="Couldn't load payments"
				:message="listError"
				:on-retry="() => list.reload()"
			/>
			<AppSkeleton v-else-if="list.loading" variant="table" :rows="6" :cols="7" />
			<EmptyState
				v-else-if="!rows.length"
				title="No client payments yet"
				description="Record the first payment against an invoice to get started."
			/>
			<div v-else class="table-scroll">
				<table>
					<thead>
						<tr>
							<th>ID</th>
							<th>Invoice</th>
							<th>Client</th>
							<th>Amount</th>
							<th>Date</th>
							<th>Method</th>
							<th>Reference</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="r in rows" :key="r.name">
							<td>{{ r.name }}</td>
							<td>{{ r.invoice }}</td>
							<td>{{ displayValue(r.client) }}</td>
							<td>{{ formatCurrency(r.amount) }}</td>
							<td>{{ displayValue(r.payment_date) }}</td>
							<td>{{ displayValue(r.payment_method) }}</td>
							<td>{{ displayValue(r.reference) }}</td>
							<td class="actions">
								<AppButton variant="outline" size="sm" @click="openEdit(r)"
									>Edit</AppButton
								>
								<AppButton
									variant="outline"
									size="sm"
									theme="red"
									@click="askDelete(r)"
								>
									Delete
								</AppButton>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<div v-if="showForm" class="modal-backdrop">
			<div class="modal" role="dialog" aria-modal="true" aria-label="Client payment form">
				<h2>{{ editName ? 'Edit Payment' : 'New Payment' }}</h2>
				<div v-if="msg" class="err" role="alert">
					<AlertCircleIcon aria-hidden="true" />
					<span>{{ msg }}</span>
				</div>
				<label>
					Invoice
					<select v-model="form.invoice">
						<option value="">Select an invoice</option>
						<option v-for="i in invoiceOptions" :key="i.name" :value="i.name">
							{{ i.name }} · {{ i.client }} · available
							{{ formatCurrency(availableFor(i)) }}
						</option>
					</select>
				</label>
				<label>
					Amount Paid
					<input v-model="form.amount" type="number" min="0" step="0.01" />
				</label>
				<label>
					Payment Date
					<input v-model="form.payment_date" type="date" />
				</label>
				<label>
					Payment Method
					<select v-model="form.payment_method">
						<option value="Cash">Cash</option>
						<option value="Bank Transfer">Bank Transfer</option>
						<option value="Check">Check</option>
						<option value="Online">Online</option>
					</select>
				</label>
				<label>
					Reference
					<input v-model="form.reference" type="text" />
				</label>
				<div class="modal-actions">
					<AppButton variant="outline" @click="showForm = false">Cancel</AppButton>
					<AppButton variant="solid" theme="gray" :loading="saving" @click="save">
						Save
					</AppButton>
				</div>
			</div>
		</div>

		<AppConfirmDialog
			v-model="showConfirm"
			title="Delete payment"
			:message="
				pendingDelete ? `Delete payment ${pendingDelete.name}? This cannot be undone.` : ''
			"
			confirm-label="Delete"
			destructive
			:loading="deleting"
			@confirm="doDelete"
			@cancel="pendingDelete = null"
		/>
	</div>
</template>

<style scoped>
.page {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}
.head-right {
	display: flex;
	gap: 0.5rem;
	align-items: center;
}
.summary {
	color: var(--text-muted, var(--color-gray-600));
	font-size: 0.85rem;
}
.card {
	background: var(--card-bg);
	border: 1px solid var(--card-border);
	border-radius: var(--card-radius);
	box-shadow: var(--card-shadow);
	overflow: hidden;
}
.table-scroll {
	overflow-x: auto;
}
table {
	width: 100%;
	border-collapse: collapse;
	font-size: 0.85rem;
}
th,
td {
	padding: 0.65rem 0.8rem;
	text-align: left;
	border-bottom: 1px solid var(--border, var(--color-gray-200));
}
th {
	font-weight: 600;
}
.actions {
	display: flex;
	gap: 0.4rem;
}
.err {
	display: flex;
	gap: 0.5rem;
	align-items: center;
	color: var(--color-red-700);
	font-size: 0.85rem;
}
.modal-backdrop {
	position: fixed;
	inset: 0;
	background: var(--modal-scrim);
	display: grid;
	place-items: center;
	z-index: 50;
}
.modal {
	background: var(--card-bg);
	border-radius: var(--card-radius);
	box-shadow: var(--shadow-md);
	padding: 1.25rem;
	width: min(28rem, calc(100vw - 2rem));
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}
.modal h2 {
	margin: 0;
	font-size: 1.1rem;
}
.modal label {
	display: flex;
	flex-direction: column;
	gap: 0.3rem;
	font-size: 0.85rem;
}
.modal input,
.modal select {
	padding: 0.5rem;
	border: 1px solid var(--border, var(--color-gray-300));
	border-radius: 0.4rem;
	background: transparent;
}
.modal-actions {
	display: flex;
	justify-content: flex-end;
	gap: 0.5rem;
}
</style>
