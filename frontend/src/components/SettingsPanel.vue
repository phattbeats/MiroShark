<template>
  <Teleport to="body">
    <div v-if="open" class="settings-overlay" @click.self="$emit('close')">
      <div class="settings-modal">
        <!-- Header -->
        <div class="modal-header">
          <div class="modal-title">
            <span class="title-label">⚙ Settings</span>
          </div>
          <button class="close-btn" @click="$emit('close')">✕</button>
        </div>

        <div class="warning-stripe"></div>

        <!-- Current Setup Summary -->
        <section class="settings-section">
          <div class="section-header">
            <span class="section-label">Current Setup</span>
            <div class="status-badge" :class="testStatus">
              <span class="badge-dot"></span>
              {{ testStatusText }}
            </div>
          </div>

          <div class="setup-grid">
            <div class="setup-row">
              <span class="setup-key">Default model</span>
              <span class="setup-val">{{ currentSettings.llm?.model_name || '—' }}</span>
            </div>
            <div class="setup-row">
              <span class="setup-key">Smart (reports)</span>
              <span class="setup-val">{{ currentSettings.smart?.model_name || inheritMarker }}</span>
            </div>
            <div class="setup-row">
              <span class="setup-key">NER (extraction)</span>
              <span class="setup-val">{{ currentSettings.ner?.model_name || inheritMarker }}</span>
            </div>
            <div class="setup-row">
              <span class="setup-key">Wonderwall (sim loop)</span>
              <span class="setup-val">{{ currentSettings.wonderwall?.model_name || inheritMarker }}</span>
            </div>
            <div class="setup-row">
              <span class="setup-key">Embeddings</span>
              <span class="setup-val">
                {{ currentSettings.embedding?.model_name || '—' }}
              </span>
            </div>
            <div class="setup-row">
              <span class="setup-key">Web search</span>
              <span class="setup-val">{{ currentSettings.web_search_model || inheritMarker }}</span>
            </div>
            <div class="setup-row">
              <span class="setup-key">API key</span>
              <span class="setup-val">
                <span v-if="currentSettings.llm?.has_api_key">
                  {{ currentSettings.llm.api_key_masked }}
                </span>
                <span v-else class="setup-missing">not set</span>
              </span>
            </div>
          </div>
        </section>

        <!-- Preset Picker -->
        <section class="settings-section">
          <div class="section-header">
            <span class="section-label">Preset</span>
          </div>

          <div class="field-row">
            <label class="field-label">Config template</label>
            <div class="select-wrapper">
              <select v-model="form.preset" class="field-select">
                <option value="">Custom — leave fields as they are</option>
                <option
                  v-for="p in presetOptions"
                  :key="p.id"
                  :value="p.id"
                >{{ p.label }}</option>
              </select>
            </div>
            <div class="field-hint">
              Applies the full set of model slots on save. See
              <a href="https://github.com/aaronjmars/MiroShark/blob/main/.env.example"
                 target="_blank" rel="noopener">.env.example</a>
              for the exact values each preset uses.
            </div>
          </div>

          <div v-if="presetNeedsKey" class="field-row">
            <label class="field-label">OpenRouter API key</label>
            <div class="key-input-group">
              <input
                v-model="form.presetApiKey"
                class="field-input"
                :type="showKey ? 'text' : 'password'"
                placeholder="sk-or-v1-..."
              />
              <button class="toggle-key-btn" @click="showKey = !showKey">
                {{ showKey ? '◉' : '◎' }}
              </button>
            </div>
            <div class="field-hint">
              Filled into every slot the preset needs (default, smart, NER, embedding).
              Leave blank to keep your existing keys.
            </div>
          </div>
        </section>

        <!-- LLM Configuration -->
        <section class="settings-section">
          <div class="section-header">
            <span class="section-label">LLM Configuration</span>
          </div>

          <!-- Provider -->
          <div class="field-row">
            <label class="field-label">Provider</label>
            <div class="select-wrapper">
              <select v-model="form.llm.provider" class="field-select">
                <option value="openai">OpenAI-compatible (OpenRouter, Ollama, etc.)</option>
                <option value="claude-code">Claude Code (local CLI)</option>
              </select>
            </div>
          </div>

          <!-- Base URL -->
          <div v-if="form.llm.provider !== 'claude-code'" class="field-row">
            <label class="field-label">Base URL</label>
            <input
              v-model="form.llm.base_url"
              class="field-input"
              type="url"
              placeholder="https://openrouter.ai/api/v1"
            />
          </div>

          <!-- Model -->
          <div v-if="form.llm.provider !== 'claude-code'" class="field-row">
            <label class="field-label">Model</label>
            <div class="model-input-group">
              <div class="select-wrapper model-select-wrapper">
                <select
                  v-if="modelList.length > 0"
                  v-model="form.llm.model_name"
                  class="field-select"
                >
                  <optgroup
                    v-for="tier in modelTiers"
                    :key="tier.label"
                    :label="tier.label"
                  >
                    <option
                      v-for="m in tier.models"
                      :key="m.id"
                      :value="m.id"
                    >{{ m.name }}</option>
                  </optgroup>
                </select>
                <input
                  v-else
                  v-model="form.llm.model_name"
                  class="field-input"
                  type="text"
                  placeholder="e.g. openai/gpt-4o-mini"
                />
              </div>
              <button
                class="load-models-btn"
                :disabled="loadingModels || !isOpenRouter"
                @click="loadOpenRouterModels"
                :title="isOpenRouter ? 'Load available models from OpenRouter' : 'Only available for OpenRouter base URL'"
              >
                <span v-if="loadingModels">...</span>
                <span v-else>↻</span>
              </button>
            </div>
            <div v-if="modelLoadError" class="field-error">{{ modelLoadError }}</div>
          </div>

          <!-- API Key -->
          <div v-if="form.llm.provider !== 'claude-code'" class="field-row">
            <label class="field-label">API Key</label>
            <div class="key-input-group">
              <input
                v-model="form.llm.api_key"
                class="field-input"
                :type="showKey ? 'text' : 'password'"
                :placeholder="currentSettings.llm?.api_key_masked || 'sk-...'"
              />
              <button class="toggle-key-btn" @click="showKey = !showKey">
                {{ showKey ? '◉' : '◎' }}
              </button>
            </div>
            <div v-if="currentSettings.llm?.has_api_key && !form.llm.api_key" class="field-hint">
              Current key: {{ currentSettings.llm.api_key_masked }} — leave blank to keep unchanged
            </div>
          </div>

          <!-- Test Connection -->
          <div v-if="form.llm.provider !== 'claude-code'" class="field-row test-row">
            <button
              class="test-btn"
              :disabled="testing"
              @click="testConnection"
            >
              <span v-if="testing">Testing...</span>
              <span v-else>Test Connection</span>
            </button>
            <div v-if="testResult" class="test-result" :class="testResult.success ? 'ok' : 'fail'">
              <span v-if="testResult.success">
                ✓ {{ testResult.model }} — {{ testResult.latency_ms }}ms
              </span>
              <span v-else>✗ {{ testResult.error }}</span>
            </div>
          </div>
        </section>

        <!-- Advanced: per-slot overrides -->
        <section class="settings-section">
          <button class="advanced-toggle" @click="advancedOpen = !advancedOpen">
            <span class="section-label">
              Advanced slot overrides
            </span>
            <span class="chevron">{{ advancedOpen ? '−' : '+' }}</span>
          </button>

          <div v-if="advancedOpen" class="advanced-body">
            <div class="advanced-hint">
              Each slot falls back to the default LLM config when left empty.
            </div>

            <!-- Smart -->
            <div class="advanced-group">
              <div class="advanced-group-title">Smart — report generation</div>
              <div class="field-row">
                <label class="field-label">Model</label>
                <input
                  v-model="form.smart.model_name"
                  class="field-input"
                  type="text"
                  placeholder="e.g. anthropic/claude-sonnet-4.6"
                />
              </div>
            </div>

            <!-- NER -->
            <div class="advanced-group">
              <div class="advanced-group-title">NER — entity extraction</div>
              <div class="field-row">
                <label class="field-label">Model</label>
                <input
                  v-model="form.ner.model_name"
                  class="field-input"
                  type="text"
                  placeholder="e.g. google/gemini-2.0-flash-001"
                />
              </div>
            </div>

            <!-- Wonderwall -->
            <div class="advanced-group">
              <div class="advanced-group-title">Wonderwall — simulation loop</div>
              <div class="field-row">
                <label class="field-label">Model</label>
                <input
                  v-model="form.wonderwall.model_name"
                  class="field-input"
                  type="text"
                  placeholder="e.g. google/gemini-2.0-flash-lite-001"
                />
              </div>
            </div>

            <!-- Embedding -->
            <div class="advanced-group">
              <div class="advanced-group-title">Embeddings</div>
              <div class="field-row">
                <label class="field-label">Provider</label>
                <div class="select-wrapper">
                  <select v-model="form.embedding.provider" class="field-select">
                    <option value="ollama">Ollama (local)</option>
                    <option value="openai">OpenAI-compatible</option>
                  </select>
                </div>
              </div>
              <div class="field-row">
                <label class="field-label">Model</label>
                <input
                  v-model="form.embedding.model_name"
                  class="field-input"
                  type="text"
                  placeholder="e.g. openai/text-embedding-3-small"
                />
              </div>
            </div>

            <!-- Web Search -->
            <div class="advanced-group">
              <div class="advanced-group-title">Web search (URL import + enrichment)</div>
              <div class="field-row">
                <label class="field-label">Model</label>
                <input
                  v-model="form.web_search_model"
                  class="field-input"
                  type="text"
                  placeholder="e.g. google/gemini-2.0-flash-001:online"
                />
              </div>
            </div>
          </div>
        </section>

        <!-- Neo4j Configuration -->
        <section class="settings-section">
          <div class="section-header">
            <span class="section-label">Graph Database (Neo4j)</span>
          </div>

          <div class="field-row">
            <label class="field-label">URI</label>
            <input
              v-model="form.neo4j.uri"
              class="field-input"
              type="text"
              placeholder="bolt://localhost:7687"
            />
          </div>

          <div class="field-row">
            <label class="field-label">User</label>
            <input
              v-model="form.neo4j.user"
              class="field-input"
              type="text"
              placeholder="neo4j"
            />
          </div>

          <div class="field-row">
            <label class="field-label">Password</label>
            <input
              v-model="form.neo4j.password"
              class="field-input"
              type="password"
              placeholder="Leave blank to keep unchanged"
            />
          </div>
        </section>

        <!-- Footer -->
        <div class="modal-footer">
          <div v-if="saveError" class="save-error">{{ saveError }}</div>
          <div v-if="saveSuccess" class="save-success">✓ Settings saved (runtime — edit .env to persist across restarts)</div>
          <div class="footer-actions">
            <button class="cancel-btn" @click="$emit('close')">Cancel</button>
            <button class="save-btn" :disabled="saving" @click="saveSettings">
              <span v-if="saving">Saving...</span>
              <span v-else>Save Settings →</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { getSettings, updateSettings, testLlmConnection } from '../api/settings'

const props = defineProps({
  open: { type: Boolean, required: true }
})

const emit = defineEmits(['close'])

// Current settings loaded from backend
const currentSettings = ref({})

// Form state
const form = reactive({
  preset: '',
  presetApiKey: '',
  llm: {
    provider: 'openai',
    base_url: '',
    model_name: '',
    api_key: '',
  },
  smart: { model_name: '' },
  ner: { model_name: '' },
  wonderwall: { model_name: '' },
  embedding: { provider: 'ollama', model_name: '' },
  web_search_model: '',
  neo4j: {
    uri: '',
    user: '',
    password: '',
  },
})

// UI state
const showKey = ref(false)
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)
const testing = ref(false)
const testResult = ref(null)
const modelList = ref([])
const loadingModels = ref(false)
const modelLoadError = ref('')
const advancedOpen = ref(false)
const inheritMarker = '— inherits default —'

// Load current settings when panel opens
watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    saveError.value = ''
    saveSuccess.value = false
    testResult.value = null
    form.preset = ''
    form.presetApiKey = ''
    await loadCurrentSettings()
  }
})

const loadCurrentSettings = async () => {
  try {
    // Axios response interceptor already unwraps to the body, so `res`
    // is `{ success, data }` — not the raw axios response.
    const res = await getSettings()
    if (res?.success && res.data) {
      const d = res.data
      currentSettings.value = d
      form.llm.provider = d.llm.provider || 'openai'
      form.llm.base_url = d.llm.base_url || ''
      form.llm.model_name = d.llm.model_name || ''
      form.llm.api_key = '' // never pre-fill
      form.smart.model_name = d.smart?.model_name || ''
      form.ner.model_name = d.ner?.model_name || ''
      form.wonderwall.model_name = d.wonderwall?.model_name || ''
      form.embedding.provider = d.embedding?.provider || 'ollama'
      form.embedding.model_name = d.embedding?.model_name || ''
      form.web_search_model = d.web_search_model || ''
      form.neo4j.uri = d.neo4j?.uri || ''
      form.neo4j.user = d.neo4j?.user || ''
      form.neo4j.password = ''
    }
  } catch (_) {
    // Non-fatal
  }
}

const presetOptions = computed(() => currentSettings.value.available_presets || [])

// `local` preset doesn't need an API key — the others do.
const presetNeedsKey = computed(() =>
  form.preset === 'cheap' || form.preset === 'best'
)

// Whether current base URL is OpenRouter
const isOpenRouter = computed(() =>
  form.llm.base_url.includes('openrouter.ai')
)

// Model tiering thresholds (cost per 1M tokens, prompt side)
const MODEL_TIERS = [
  { label: 'Fast (< $0.50/M)', max: 0.5 },
  { label: 'Standard ($0.50–$5/M)', max: 5 },
  { label: 'Capable (> $5/M)', max: Infinity },
]

const modelTiers = computed(() => {
  if (modelList.value.length === 0) return []
  return MODEL_TIERS.map(tier => ({
    label: tier.label,
    models: modelList.value.filter(m => {
      const price = m.pricing?.prompt ? parseFloat(m.pricing.prompt) * 1_000_000 : 0
      return price <= tier.max && price > (tier === MODEL_TIERS[0] ? 0 : MODEL_TIERS[MODEL_TIERS.indexOf(tier) - 1].max)
    })
  })).filter(t => t.models.length > 0)
})

const loadOpenRouterModels = async () => {
  loadingModels.value = true
  modelLoadError.value = ''
  try {
    const res = await fetch('https://openrouter.ai/api/v1/models')
    const json = await res.json()
    if (json.data) {
      modelList.value = json.data
        .filter(m => m.id && m.name)
        .sort((a, b) => {
          const pa = parseFloat(a.pricing?.prompt || 0) * 1_000_000
          const pb = parseFloat(b.pricing?.prompt || 0) * 1_000_000
          return pa - pb
        })
    }
  } catch (_) {
    modelLoadError.value = 'Could not load model list — check your network connection.'
  } finally {
    loadingModels.value = false
  }
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null
  try {
    // Interceptor unwraps axios to the body directly.
    const res = await testLlmConnection()
    testResult.value = res
  } catch (e) {
    testResult.value = { success: false, error: e.message }
  } finally {
    testing.value = false
  }
}

const testStatus = computed(() => {
  if (!testResult.value) return 'idle'
  return testResult.value.success ? 'ok' : 'fail'
})

const testStatusText = computed(() => {
  if (!testResult.value) return 'Not tested'
  return testResult.value.success ? 'Connected' : 'Failed'
})

const saveSettings = async () => {
  saving.value = true
  saveError.value = ''
  saveSuccess.value = false
  try {
    const payload = {}

    // Preset is applied server-side first; explicit field overrides apply on top.
    if (form.preset) {
      payload.preset = form.preset
      if (form.presetApiKey) payload.preset_api_key = form.presetApiKey
    }

    payload.llm = {
      provider: form.llm.provider,
      base_url: form.llm.base_url,
      model_name: form.llm.model_name,
    }
    if (form.llm.api_key) payload.llm.api_key = form.llm.api_key

    payload.smart = { model_name: form.smart.model_name }
    payload.ner = { model_name: form.ner.model_name }
    payload.wonderwall = { model_name: form.wonderwall.model_name }
    payload.embedding = {
      provider: form.embedding.provider,
      model_name: form.embedding.model_name,
    }
    payload.web_search_model = form.web_search_model

    payload.neo4j = {
      uri: form.neo4j.uri,
      user: form.neo4j.user,
    }
    if (form.neo4j.password) payload.neo4j.password = form.neo4j.password

    const res = await updateSettings(payload)
    if (res?.success && res.data) {
      saveSuccess.value = true
      currentSettings.value = res.data
      form.llm.api_key = ''
      form.presetApiKey = ''
      form.neo4j.password = ''
      setTimeout(() => { saveSuccess.value = false }, 4000)
    } else {
      saveError.value = res?.error || 'Save failed'
    }
  } catch (e) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* ── Modal Overlay ── */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 10, 0.6);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fade-in 0.15s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.settings-modal {
  background: #FAFAFA;
  width: 580px;
  max-width: calc(100vw - 48px);
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  border: 2px solid rgba(10,10,10,0.12);
  position: relative;
  animation: slide-in 0.2s ease-out;
  font-family: 'Space Mono', 'Courier New', monospace;
}

@keyframes slide-in {
  from { transform: translateY(-16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* ── Header ── */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  background: #0A0A0A;
  color: #FAFAFA;
}

.title-label {
  font-family: 'Space Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(250,250,250,0.5);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.1s;
}
.close-btn:hover { color: #FAFAFA; }

/* ── Warning Stripe ── */
.warning-stripe {
  height: 6px;
  background: repeating-linear-gradient(
    -45deg,
    #FF6B1A,
    #FF6B1A 10px,
    #FAFAFA 10px,
    #FAFAFA 20px
  );
}

/* ── Sections ── */
.settings-section {
  padding: 22px;
  border-bottom: 2px solid rgba(10,10,10,0.08);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: rgba(10,10,10,0.4);
}

/* ── Current Setup grid ── */
.setup-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 2px dashed rgba(10,10,10,0.1);
  padding: 12px 14px;
  background: #F5F5F5;
}
.setup-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  font-size: 12px;
  letter-spacing: 0.3px;
}
.setup-key {
  color: rgba(10,10,10,0.5);
  flex-shrink: 0;
}
.setup-val {
  color: #0A0A0A;
  font-weight: 700;
  text-align: right;
  overflow-wrap: anywhere;
}
.setup-aux {
  color: rgba(10,10,10,0.4);
  font-weight: 400;
  margin-left: 4px;
}
.setup-missing {
  color: #FF4444;
  font-weight: 400;
}

/* ── Status Badge ── */
.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.badge-dot {
  width: 7px;
  height: 7px;
  background: rgba(10,10,10,0.2);
  border-radius: 0;
}
.status-badge.ok .badge-dot { background: #43C165; }
.status-badge.fail .badge-dot { background: #FF4444; }
.status-badge.ok { color: #43C165; }
.status-badge.fail { color: #FF4444; }
.status-badge.idle { color: rgba(10,10,10,0.3); }

/* ── Form Fields ── */
.field-row {
  margin-bottom: 14px;
}

.field-label {
  display: block;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(10,10,10,0.5);
  margin-bottom: 6px;
}

.field-input {
  width: 100%;
  border: 2px solid rgba(10,10,10,0.1);
  background: #F5F5F5;
  padding: 8px 11px;
  font-family: 'Space Mono', monospace;
  font-size: 13px;
  color: #0A0A0A;
  outline: none;
  transition: border-color 0.1s;
  box-sizing: border-box;
}
.field-input:focus { border-color: #FF6B1A; background: #FAFAFA; }
.field-input::placeholder { color: rgba(10,10,10,0.3); }

.select-wrapper { position: relative; }
.field-select {
  width: 100%;
  border: 2px solid rgba(10,10,10,0.1);
  background: #F5F5F5;
  padding: 8px 11px;
  font-family: 'Space Mono', monospace;
  font-size: 13px;
  color: #0A0A0A;
  outline: none;
  cursor: pointer;
  appearance: auto;
  transition: border-color 0.1s;
  box-sizing: border-box;
}
.field-select:focus { border-color: #FF6B1A; }

/* ── Model input group ── */
.model-input-group {
  display: flex;
  gap: 6px;
}
.model-select-wrapper { flex: 1; min-width: 0; }

.load-models-btn {
  border: 2px solid rgba(10,10,10,0.1);
  background: #F5F5F5;
  padding: 8px 12px;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.1s;
  flex-shrink: 0;
}
.load-models-btn:hover:not(:disabled) { border-color: #FF6B1A; color: #FF6B1A; }
.load-models-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* ── Key input group ── */
.key-input-group {
  display: flex;
  gap: 6px;
}
.key-input-group .field-input { flex: 1; }

.toggle-key-btn {
  border: 2px solid rgba(10,10,10,0.1);
  background: #F5F5F5;
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.1s;
}
.toggle-key-btn:hover { border-color: #FF6B1A; }

.field-hint {
  margin-top: 5px;
  font-size: 11px;
  color: rgba(10,10,10,0.4);
  letter-spacing: 0.5px;
}
.field-hint a { color: #FF6B1A; text-decoration: underline; }

.field-error {
  margin-top: 5px;
  font-size: 11px;
  color: #FF4444;
}

/* ── Test row ── */
.test-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.test-btn {
  border: 2px solid rgba(10,10,10,0.12);
  background: transparent;
  padding: 8px 16px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.1s;
}
.test-btn:hover:not(:disabled) { border-color: #FF6B1A; color: #FF6B1A; }
.test-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.test-result {
  font-size: 12px;
  letter-spacing: 1px;
}
.test-result.ok { color: #43C165; }
.test-result.fail { color: #FF4444; }

/* ── Advanced ── */
.advanced-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  background: transparent;
  border: none;
  padding: 0 0 10px 0;
  cursor: pointer;
  font-family: 'Space Mono', monospace;
}
.chevron {
  font-size: 16px;
  color: rgba(10,10,10,0.4);
  line-height: 1;
}
.advanced-body {
  margin-top: 4px;
}
.advanced-hint {
  font-size: 11px;
  color: rgba(10,10,10,0.4);
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}
.advanced-group {
  padding: 10px 0;
  border-top: 1px dashed rgba(10,10,10,0.08);
}
.advanced-group:first-child { border-top: none; padding-top: 0; }
.advanced-group-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #0A0A0A;
  margin-bottom: 10px;
}

/* ── Footer ── */
.modal-footer {
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.save-error {
  font-size: 12px;
  color: #FF4444;
  letter-spacing: 0.5px;
}

.save-success {
  font-size: 12px;
  color: #43C165;
  letter-spacing: 1px;
}

.cancel-btn {
  border: 2px solid rgba(10,10,10,0.1);
  background: transparent;
  padding: 10px 20px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  cursor: pointer;
  color: rgba(10,10,10,0.5);
  transition: all 0.1s;
}
.cancel-btn:hover { border-color: rgba(10,10,10,0.3); color: #0A0A0A; }

.save-btn {
  border: 2px solid #0A0A0A;
  background: #0A0A0A;
  color: #FAFAFA;
  padding: 10px 20px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s;
}
.save-btn:hover:not(:disabled) { background: #FF6B1A; border-color: #FF6B1A; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
