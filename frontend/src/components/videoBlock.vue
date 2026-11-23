<template>
  <div class="video-block">
    <h2 v-if="showTitle" class="word-title">{{ word.string }}</h2>
    <div v-if="showSuccess" class="success-view">
      <div class="success-icon" aria-hidden="true" />
      <p class="success-message">
        Bravo tu sais dire
        <strong>{{ word.string }} !</strong>
      </p>
      <BigButton type="primary" @click="emit('success-continue')">Je continue</BigButton>
    </div>
    <template v-else>
      <VideoCard
        ref="videoCardRef"
        @recording-ready="onRecordingReady"
        @recording-error="onRecordingError"
      />
      <p v-if="isChecking" class="capture-result">Analyse en cours…</p>
      <p v-else-if="aiError" class="capture-result" role="alert">{{ aiError }}</p>
      <p v-else-if="aiResult" class="capture-result">{{ aiResult.message }}</p>
    </template>
  </div>
</template>
<script setup lang="ts">
import { ref, shallowRef, onBeforeUnmount } from "vue"
import VideoCard from "./cards/videoCard.vue"
import BigButton from "./buttons/bigButton.vue"
import type { LandmarkCapture } from "@/types/landmarks"
import type { AIWordResponse } from "@/types/word"
import { ApiClass } from "@/api/api"

const props = withDefaults(
  defineProps<{
    word: {
      id?: number
      string: string
    }
    showTitle?: boolean
    showSuccess?: boolean
  }>(),
  {
    showTitle: true,
    showSuccess: false,
  },
)

const emit = defineEmits<{
  "validation-success": []
  "success-continue": []
  "recording-error": []
  "recording-ready": []
}>()

const videoCardRef = ref<InstanceType<typeof VideoCard> | null>(null)
const capture = shallowRef<LandmarkCapture | null>(null)
const isChecking = ref(false)
const aiError = ref("")
const aiResult = ref<AIWordResponse | null>(null)
let request: AbortController | null = null

function onRecordingReady(recorded: LandmarkCapture) {
  capture.value = recorded
  emit("recording-ready")
}

async function confirmRecording() {
  if (!capture.value || isChecking.value) return
  const controller = new AbortController()
  request = controller
  const timeout = setTimeout(() => controller.abort(), 30000)
  isChecking.value = true
  aiError.value = ""
  try {
    aiResult.value = await ApiClass.tryWord(capture.value, props.word.string, controller.signal)
    if (aiResult.value.is_valid) emit("validation-success")
  } catch (error) {
    aiError.value = controller.signal.aborted
      ? "L'analyse a pris trop de temps. Réessayez."
      : error instanceof Error
        ? error.message
        : "Impossible d'analyser l'enregistrement."
  } finally {
    clearTimeout(timeout)
    isChecking.value = false
    request = null
  }
}

function onRecordingError() {
  capture.value = null
  emit("recording-error")
}

async function activateCamera() {
  return (await videoCardRef.value?.activateCamera()) ?? false
}

function stopCamera() {
  request?.abort()
  capture.value = null
  videoCardRef.value?.stopCamera()
}

function cancelRecording() {
  videoCardRef.value?.cancelRecording()
}

function startRecording() {
  capture.value = null
  aiError.value = ""
  aiResult.value = null
  return videoCardRef.value?.startRecording() ?? false
}

function stopRecording() {
  videoCardRef.value?.stopRecording()
}

onBeforeUnmount(() => request?.abort())

defineExpose({
  activateCamera,
  stopCamera,
  cancelRecording,
  startRecording,
  stopRecording,
  confirmRecording,
})
</script>
<style scoped>
.video-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;

  .word-title {
    font-size: 18px;
    font-weight: bold;
    color: var(--color-black);
  }

  .success-view {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
    padding-top: 22px;
  }

  .success-icon {
    width: 270px;
    height: 250px;
    background-image: url("@/assets/icons/success-page-logo.svg");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
  }

  .success-message {
    color: var(--color-darkpurple);
    font-size: var(--font-size-h2);
    font-weight: var(--font-weight-bold);
    text-align: center;
    line-height: 1.25;

    strong {
      display: block;
      font-size: var(--font-size-title);
    }
  }

  .capture-result {
    text-align: center;
  }
}
</style>
