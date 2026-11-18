<template>
	<Dialog v-model="show" :options="{ title: dialogTitle, size: 'lg' }">
		<template #body-content>
			<div class="import-body">
				<div v-if="isData" class="field">
					<label>Source text</label>
					<textarea
						v-model="sourceText"
						rows="7"
						placeholder="Paste the source data here..."
					></textarea>
				</div>

				<div class="field">
					<label>{{ isData ? 'Or upload a document' : 'Receipt image or PDF *' }}</label>
					<input
						ref="fileInput"
						type="file"
						:accept="acceptedFiles"
						@change="onFileChange"
					/>
				</div>

				<div v-if="error" class="error-msg">{{ error }}</div>
			</div>
		</template>
		<template #actions>
			<AppButton variant="ghost" @click="show = false">Cancel</AppButton>
			<AppButton variant="solid" theme="gray" :loading="loading" @click="submit">
				Import
			</AppButton>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Dialog, call } from 'frappe-ui'
import AppButton from '@/components/ui/AppButton.vue'

const props = defineProps({
	modelValue: Boolean,
	mode: { type: String, default: 'data' },
	kind: { type: String, default: 'client' },
	title: { type: String, default: 'Import from Data' },
})
const emit = defineEmits(['update:modelValue', 'imported', 'unavailable'])

const show = ref(props.modelValue)
const sourceText = ref('')
const file = ref(null)
const fileInput = ref(null)
const error = ref('')
const loading = ref(false)

const isData = computed(() => props.mode !== 'receipt')
const dialogTitle = computed(() => props.title)
const acceptedFiles = computed(() =>
	isData.value ? '.txt,.md,.csv,.json,.pdf,.docx,.doc' : '.png,.jpg,.jpeg,.webp,.pdf'
)

watch(
	() => props.modelValue,
	(v) => (show.value = v)
)
watch(show, (v) => {
	emit('update:modelValue', v)
	if (v) reset()
})

function reset() {
	sourceText.value = ''
	file.value = null
	error.value = ''
	loading.value = false
	if (fileInput.value) fileInput.value.value = ''
}

function extensionOf(name) {
	const value = String(name || '')
	return value.includes('.') ? '.' + value.split('.').pop().toLowerCase() : ''
}

function onFileChange(event) {
	file.value = event.target.files?.[0] || null
	error.value = ''
}

function readFile(selected) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = () => resolve(String(reader.result || '').split(',')[1] || '')
		reader.onerror = () => reject(reader.error)
		reader.readAsDataURL(selected)
	})
}

function messageOf(err) {
	return String(err?.messages?.[0] || err?.message || err || '')
}

function validate() {
	if (isData.value) {
		if (!sourceText.value.trim() && !file.value) {
			error.value = 'Please provide text or a supported file.'
			return false
		}
		if (file.value && !acceptedFiles.value.split(',').includes(extensionOf(file.value.name))) {
			error.value = 'Please provide text or a supported file.'
			return false
		}
		return true
	}
	if (!file.value || !acceptedFiles.value.split(',').includes(extensionOf(file.value.name))) {
		error.value = 'Please upload a receipt as an image or PDF.'
		return false
	}
	return true
}

async function submit() {
	error.value = ''
	if (!validate() || loading.value) return

	loading.value = true
	try {
		const payload = {
			source_text: sourceText.value.trim() || null,
			file_name: file.value?.name || null,
			file_content: file.value ? await readFile(file.value) : null,
		}
		const values = isData.value
			? await call('my_custom_app.shared.ai_imports.extract_record_fields', {
					kind: props.kind,
					...payload,
			  })
			: await call('my_custom_app.shared.ai_imports.extract_expense_fields', payload)
		if (!values || !Object.keys(values).length) {
			error.value = isData.value
				? 'No details could be found in the data.'
				: 'No details could be read from the receipt.'
			return
		}
		emit('imported', values)
		show.value = false
	} catch (err) {
		const message = messageOf(err)
		if (message.toLowerCase().includes('ai provider unavailable')) {
			emit('unavailable')
			show.value = false
			return
		}
		error.value = message || 'Import unavailable. Please enter the details manually.'
	} finally {
		loading.value = false
	}
}
</script>

<style scoped>
.import-body {
	display: flex;
	flex-direction: column;
	gap: var(--space-4);
}
.field {
	display: flex;
	flex-direction: column;
	gap: var(--space-1);
}
.field label {
	font-size: var(--fs-sm);
	font-weight: 600;
}
textarea,
input[type='file'] {
	width: 100%;
	padding: var(--space-2);
	border: 1px solid var(--color-gray-300);
	border-radius: var(--radius-md, 6px);
	font: inherit;
}
textarea {
	resize: vertical;
}
.error-msg {
	color: var(--color-red-600);
	font-size: var(--fs-sm);
}
</style>
