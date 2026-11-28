<template>
  <div class="card video-card" :style="{ aspectRatio }">
    <video
      v-show="cameraActive && !previewUrl"
      ref="cameraVideo"
      class="media mirrored"
      autoplay
      muted
      playsinline
    />
    <video v-if="previewUrl" class="media mirrored" :src="previewUrl" controls muted playsinline />
    <p v-if="!cameraActive" class="camera-placeholder">
      Active la caméra pour enregistrer ton signe.
    </p>

    <div v-if="isRecording" class="recording-indicator">● REC</div>
    <div v-if="isPreparing" class="camera-error">Préparation de la caméra…</div>
    <div v-if="errorMessage" class="camera-error">{{ errorMessage }}</div>
  </div>
</template>
<script setup lang="ts">
import { ref, onBeforeUnmount } from "vue"
import { createLandmarkExtractor } from "@/lib/landmarkExtractor"
import type { LandmarkCapture, LandmarkFrame } from "@/types/landmarks"

const emit = defineEmits<{
  "recording-ready": [capture: LandmarkCapture]
  "recording-error": [message: string]
}>()

const cameraVideo = ref<HTMLVideoElement | null>(null)
const cameraActive = ref(false)
const isRecording = ref(false)
const isPreparing = ref(false)
const errorMessage = ref("")
const previewUrl = ref("")
const aspectRatio = ref("1 / 1")
let stream: MediaStream | null = null
let extractor: Awaited<ReturnType<typeof createLandmarkExtractor>> | null = null
let cameraSession = 0
let frameCallback: number | null = null
let frames: LandmarkFrame[] = []
let timestamps: number[] = []
let recorder: MediaRecorder | null = null

async function activateCamera(): Promise<boolean> {
  if (isPreparing.value) return false
  if (extractor && stream) return true
  const session = ++cameraSession
  isPreparing.value = true
  errorMessage.value = ""
  try {
    const acquired = await navigator.mediaDevices.getUserMedia({ video: true })
    if (session !== cameraSession) {
      acquired.getTracks().forEach((track) => track.stop())
      return false
    }
    stream = acquired
    if (!cameraVideo.value) throw new Error("Caméra indisponible.")
    cameraVideo.value.srcObject = stream
    cameraActive.value = true
    await cameraVideo.value.play()
    aspectRatio.value = `${cameraVideo.value.videoWidth} / ${cameraVideo.value.videoHeight}`
    if (session !== cameraSession) return false
    const ready = await createLandmarkExtractor()
    if (session !== cameraSession) {
      ready.close()
      return false
    }
    extractor = ready
    isPreparing.value = false
    return true
  } catch {
    if (session === cameraSession) {
      stopCamera()
      errorMessage.value = "Impossible de préparer la caméra et les détecteurs."
    }
    return false
  }
}

function stopFrames() {
  isRecording.value = false
  if (frameCallback !== null) cameraVideo.value?.cancelVideoFrameCallback(frameCallback)
  frameCallback = null
}

function cancelRecording() {
  stopFrames()
  if (recorder) {
    recorder.onstop = null
    recorder.ondataavailable = null
    recorder.onerror = null
    if (recorder.state !== "inactive") recorder.stop()
    recorder = null
  }
  frames = []
  timestamps = []
}

function clearPreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ""
}

function recordingError(message: string) {
  cancelRecording()
  errorMessage.value = message
  emit("recording-error", message)
}

function stopCamera() {
  cameraSession += 1
  cancelRecording()
  clearPreview()
  stream?.getTracks().forEach((track) => track.stop())
  stream = null
  if (cameraVideo.value) cameraVideo.value.srcObject = null
  extractor?.close()
  extractor = null
  cameraActive.value = false
  isPreparing.value = false
}

function captureTick(_now: number, metadata: { mediaTime: number }) {
  frameCallback = null
  if (!isRecording.value || !cameraVideo.value || !extractor) return
  try {
    const timestamp = metadata.mediaTime * 1000
    frames.push(extractor.detect(cameraVideo.value, timestamp))
    timestamps.push(timestamp)
    frameCallback = cameraVideo.value.requestVideoFrameCallback(captureTick)
  } catch {
    recordingError("Impossible d'extraire les points. Recommencez la capture.")
  }
}

function startRecording() {
  if (!extractor || !cameraVideo.value || !stream || recorder) return false
  clearPreview()
  frames = []
  timestamps = []
  errorMessage.value = ""
  try {
    const current = new MediaRecorder(stream)
    const chunks: Blob[] = []
    recorder = current
    current.ondataavailable = (event) => {
      if (event.data.size) chunks.push(event.data)
    }
    current.onerror = () => recordingError("Impossible d'enregistrer la vidéo.")
    current.onstop = () => {
      if (recorder !== current) return
      recorder = null
      const duration = timestamps.at(-1)! - timestamps[0]!
      if (frames.length < 5 || !(duration > 0) || !chunks.length) {
        recordingError("Capture trop courte. Recommencez le geste.")
        return
      }
      previewUrl.value = URL.createObjectURL(new Blob(chunks, { type: current.mimeType }))
      emit("recording-ready", {
        points: frames.map((frame) => frame.points),
        valid: frames.map((frame) => frame.valid),
        fps: ((frames.length - 1) * 1000) / duration,
      })
      frames = []
      timestamps = []
    }
    current.start()
    isRecording.value = true
    frameCallback = cameraVideo.value.requestVideoFrameCallback(captureTick)
    return true
  } catch {
    recordingError("Impossible d'enregistrer la vidéo dans ce navigateur.")
    return false
  }
}

function stopRecording() {
  if (!isRecording.value) return
  stopFrames()
  recorder?.stop()
}

onBeforeUnmount(stopCamera)
defineExpose({ activateCamera, stopCamera, cancelRecording, startRecording, stopRecording })
</script>
<style scoped>
.video-card {
  background-color: var(--color-lightgray);
  width: 80%;
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;

  .media {
    width: 100%;
    height: 100%;
    object-fit: cover;
    &.mirrored {
      transform: scaleX(-1);
    }
  }

  .camera-placeholder {
    padding: 20px;
    text-align: center;
  }

  .camera-error {
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    background-color: rgba(17, 0, 3, 0.7);
    color: white;
    font-size: 13px;
    text-align: center;
    padding: 6px 10px;
    border-radius: 10px;
  }

  .recording-indicator {
    position: absolute;
    top: 12px;
    right: 12px;
    background-color: rgba(17, 0, 3, 0.7);
    color: #ff4d4d;
    font-size: 12px;
    font-weight: bold;
    padding: 4px 8px;
    border-radius: 10px;
  }
}
</style>
