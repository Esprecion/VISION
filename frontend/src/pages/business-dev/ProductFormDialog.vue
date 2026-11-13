<template>
	<Dialog v-model="show" :options="{ title: dialogTitle }">
		<template #body-content>
			<div class="form-grid">
				<AppTextInput
					v-model="form.product_name"
					label="Product Name"
					required
					placeholder="e.g. Clinic Software License"
				/>
				<AppSelect
					v-model="form.type"
					label="Type"
					required
					:options="typeOptions"
					placeholder="Select type"
				/>
				<AppTextInput v-model="form.description" label="Description" type="text" />
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
				:disabled="!form.product_name || !form.type || isLoading"
				:loading="isLoading"
				@click="submit"
			>
				{{ isEdit ? 'Save Changes' : 'Save Product' }}
			</AppButton>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource, call } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
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
const dialogTitle = computed(() => (isEdit.value ? 'Edit Product' : 'Add Product'))

const form = reactive({
	product_name: '',
	type: '',
	description: '',
})

const typeOptions = [
	{ label: 'Software', value: 'Software' },
	{ label: 'Hardware', value: 'Hardware' },
	{ label: 'Consulting', value: 'Consulting' },
	{ label: 'Support', value: 'Support' },
]

const loading = ref(false)
const loaded = ref(null)
const loadError = ref(null)

const createProduct = createResource({
	url: 'frappe.client.insert',
	method: 'POST',
})
const saveProduct = createResource({
	url: 'frappe.client.save',
	method: 'POST',
})
const activeResource = computed(() => (isEdit.value ? saveProduct : createProduct))
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
	createProduct.reset()
	saveProduct.reset()
	if (!props.editName) return

	loading.value = true
	try {
		const doc = await call('frappe.client.get', {
			doctype: 'Product',
			name: props.editName,
		})
		loaded.value = doc
		form.product_name = doc.product_name || ''
		form.type = doc.type || ''
		form.description = doc.description || ''
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
	if (!form.product_name || !form.type || isLoading.value) return
	const doc = isEdit.value ? { ...loaded.value, ...form } : { doctype: 'Product', ...form }
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
