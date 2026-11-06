<template>
	<Dialog v-model="show" :options="{ title: dialogTitle }">
		<template #body-content>
			<div class="form-grid">
				<AppTextInput
					v-model="form.client_name"
					label="Client Name"
					required
					placeholder="e.g. Acme Corp"
				/>
				<AppTextInput v-model="form.address" label="Address" />
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
				:disabled="!form.client_name || isLoading"
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

const props = defineProps({
	modelValue: Boolean,
	editName: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'created', 'updated'])

const show = ref(props.modelValue)
watch(
	() => props.modelValue,
	(v) => (show.value = v)
)

const isEdit = computed(() => !!props.editName)
const dialogTitle = computed(() => (isEdit.value ? 'Edit Client' : 'Add Client'))

const form = reactive({
	client_name: '',
	address: '',
	contact_person: '',
	contact_email: '',
	contact_phone: '',
	territory: '',
})

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
	const err = activeResource.value.error || loadError.value
	if (!err) return ''
	const message = err.messages?.[0] || err.message || 'Something went wrong'
	return String(message).replace(/<[^>]+>/g, '')
})

function resetForm() {
	Object.keys(form).forEach((k) => (form[k] = ''))
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
		form.address = doc.address || ''
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

function submit() {
	if (!form.client_name || isLoading.value) return
	const doc = isEdit.value ? { ...loaded.value, ...form } : { doctype: 'Client', ...form }
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
