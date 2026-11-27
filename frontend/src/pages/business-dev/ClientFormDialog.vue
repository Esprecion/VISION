<template>
	<Dialog v-model="show" :options="{ title: dialogTitle }">
		<template #body-content>
			<div class="form-grid">
				<AppButton variant="ghost" size="sm" @click="showImport = true">
					Import from Data
				</AppButton>
				<ImportDialog
					v-model="showImport"
					kind="client"
					@imported="applyImport"
					@unavailable="onImportUnavailable"
				/>
				<AppTextInput
					v-model="form.first_name"
					label="First Name"
					:required="!isEdit"
					placeholder="e.g. Juan"
				/>
				<AppTextInput
					v-model="form.last_name"
					label="Last Name"
					:required="!isEdit"
					placeholder="e.g. Dela Cruz"
				/>
				<AppTextInput
					v-model="form.street_barangay"
					label="Street & Barangay"
					placeholder="e.g. 12 Rizal St., Barangay San Antonio"
				/>
				<AppTextInput
					v-model="form.city_municipality"
					label="City / Municipality"
					placeholder="e.g. Makati City"
				/>
				<AppTextInput v-model="form.province" label="Province" placeholder="e.g. Metro Manila" />
				<AppTextInput v-model="form.postal_code" label="Postal Code" placeholder="e.g. 1203" />
				<AppTextInput v-model="form.country" label="Country" />
				<AppTextInput v-model="form.contact_person" label="Contact Person" />
				<AppTextInput v-model="form.contact_email" type="email" label="Contact Email" />
				<AppTextInput v-model="form.contact_phone" label="Contact Phone" />
				<AppTextInput
					v-model="form.territory"
					label="Territory"
					placeholder="e.g. Metro Manila"
				/>
				<div v-if="errorText" class="error-msg">
					<AlertCircleIcon class="btn-icon" aria-hidden="true" />
					{{ errorText }}
				</div>
			</div>
		</template>
		<template #actions>
			<AppButton
				variant="solid"
				theme="gray"
				:disabled="!canSave || isLoading"
				:loading="isLoading"
				@click="submit"
			>
				{{ isEdit ? 'Save Changes' : 'Save Client' }}
			</AppButton>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource, call } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import ImportDialog from '@/components/ui/ImportDialog.vue'

const props = defineProps({
	modelValue: Boolean,
	editName: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'created', 'updated'])

const show = ref(props.modelValue)
const showImport = ref(false)
const importError = ref('')
watch(
	() => props.modelValue,
	(v) => (show.value = v)
)

const isEdit = computed(() => !!props.editName)
const dialogTitle = computed(() => (isEdit.value ? 'Edit Client' : 'Add Client'))

const form = reactive({
	client_name: '',
	first_name: '',
	last_name: '',
	street_barangay: '',
	city_municipality: '',
	province: '',
	postal_code: '',
	country: 'Philippines',
	contact_person: '',
	contact_email: '',
	contact_phone: '',
	territory: '',
})

const canSave = computed(() =>
	isEdit.value || (!!form.first_name.trim() && !!form.last_name.trim())
)

const loading = ref(false)
const loaded = ref(null)
const loadError = ref(null)

const createClient = createResource({
	url: 'frappe.client.insert',
	method: 'POST',
})
const saveClient = createResource({
	url: 'frappe.client.save',
	method: 'POST',
})
const activeResource = computed(() => (isEdit.value ? saveClient : createClient))
const isLoading = computed(() => loading.value || !!activeResource.value.loading)
const errorText = computed(() => {
	const err = importError.value
		? { message: importError.value }
		: activeResource.value.error || loadError.value
	if (!err) return ''
	const message = err.messages?.[0] || err.message || 'Something went wrong'
	return String(message).replace(/<[^>]+>/g, '')
})

function resetForm() {
	Object.keys(form).forEach((k) => (form[k] = ''))
	form.country = 'Philippines'
	importError.value = ''
}

async function prepare() {
	resetForm()
	loaded.value = null
	loadError.value = null
	createClient.reset()
	saveClient.reset()
	if (!props.editName) return

	loading.value = true
	try {
		const doc = await call('frappe.client.get', {
			doctype: 'Client',
			name: props.editName,
		})
		loaded.value = doc
		form.client_name = doc.client_name || ''
		form.first_name = doc.first_name || ''
		form.last_name = doc.last_name || ''
		form.street_barangay = doc.street_barangay || doc.address || ''
		form.city_municipality = doc.city_municipality || ''
		form.province = doc.province || ''
		form.postal_code = doc.postal_code || ''
		form.country = doc.country || 'Philippines'
		form.contact_person = doc.contact_person || ''
		form.contact_email = doc.contact_email || ''
		form.contact_phone = doc.contact_phone || ''
		form.territory = doc.territory || ''
	} catch (e) {
		loadError.value = e
	} finally {
		loading.value = false
	}
}

watch(show, (v) => {
	emit('update:modelValue', v)
	if (v) prepare()
})

function applyImport(values) {
	importError.value = ''
	Object.keys(form).forEach((key) => {
		if (values[key] !== undefined) form[key] = values[key]
	})
	if (values.client_name && !form.first_name && !form.last_name) {
		const parts = String(values.client_name).trim().split(/\s+/)
		form.first_name = parts.shift() || ''
		form.last_name = parts.join(' ')
	}
	if (values.address && !form.street_barangay) form.street_barangay = values.address
}

function onImportUnavailable() {
	importError.value = 'Import unavailable. Please enter the details manually.'
}

function submit() {
	if (!canSave.value || isLoading.value) return
	const payload = { ...form }
	const fullName = `${form.first_name.trim()} ${form.last_name.trim()}`.trim()
	if (fullName) payload.client_name = fullName
	const doc = isEdit.value
		? { ...loaded.value, ...payload }
		: { doctype: 'Client', ...payload }
	activeResource.value.submit(
		{ doc },
		{
			onSuccess: (saved) => {
				emit(isEdit.value ? 'updated' : 'created', saved)
				show.value = false
			},
		}
	)
}
</script>

<style scoped>
.form-grid {
	display: flex;
	flex-direction: column;
	gap: var(--space-3);
}
.error-msg {
	display: flex;
	align-items: center;
	gap: var(--space-1);
	color: var(--color-red-600);
	font-size: var(--fs-sm);
}
.btn-icon {
	width: 14px;
	height: 14px;
	flex-shrink: 0;
}
</style>
