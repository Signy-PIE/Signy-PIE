import {
  FaceLandmarker,
  FilesetResolver,
  HandLandmarker,
  PoseLandmarker,
} from "@mediapipe/tasks-vision"
import type { HandLandmarkerResult, NormalizedLandmark } from "@mediapipe/tasks-vision"
import type { LandmarkFrame, LandmarkPoint } from "@/types/landmarks"

const FACE_INDICES = [
  61, 291, 13, 14, 78, 308, 70, 105, 300, 334, 33, 133, 362, 263, 1, 4, 5, 10, 152, 234, 454,
]

export function assembleFrame(
  pose: NormalizedLandmark[],
  hands: Pick<HandLandmarkerResult, "landmarks" | "handedness">,
  face: NormalizedLandmark[],
): LandmarkFrame {
  const points: LandmarkPoint[] = Array.from({ length: 96 }, () => [0, 0, 0])
  const valid = Array<boolean>(96).fill(false)
  const fill = (offset: number, landmarks: NormalizedLandmark[]) => {
    landmarks.forEach((point, i) => {
      points[offset + i] = [point.x, point.y, point.z]
      valid[offset + i] = true
    })
  }

  fill(42, pose)
  let sides = hands.handedness.map((items) => (items[0]?.categoryName === "Left" ? 0 : 1))
  const leftWrist = pose[15]
  const rightWrist = pose[16]
  if (leftWrist && rightWrist) {
    const costs = hands.landmarks.map((hand) =>
      [leftWrist, rightWrist].map((wrist) =>
        Math.hypot(hand[0]!.x - wrist.x, hand[0]!.y - wrist.y),
      ),
    )
    if (costs.length === 2) {
      const [first, second] = costs as [[number, number], [number, number]]
      sides = first[0] + second[1] <= first[1] + second[0] ? [0, 1] : [1, 0]
    } else if (costs.length === 1) {
      sides = [costs[0]![0]! <= costs[0]![1]! ? 0 : 1]
    }
  }
  hands.landmarks.forEach((hand, i) => fill(sides[i]! * 21, hand))
  if (face.length)
    fill(
      75,
      FACE_INDICES.map((index) => face[index]!),
    )
  return { points, valid }
}

export async function createLandmarkExtractor() {
  const vision = await FilesetResolver.forVisionTasks("/mediapipe/wasm")
  const resources: { close(): void }[] = []
  try {
    const pose = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: "/mediapipe/models/pose.task" },
      runningMode: "VIDEO",
    })
    resources.push(pose)
    const hands = await HandLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: "/mediapipe/models/hand.task" },
      runningMode: "VIDEO",
      numHands: 2,
    })
    resources.push(hands)
    const face = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: "/mediapipe/models/face.task" },
      runningMode: "VIDEO",
    })
    resources.push(face)
    const canvas = document.createElement("canvas")
    const context = canvas.getContext("2d")
    if (!context) throw new Error("Impossible de lire les images de la caméra.")
    return {
      detect(video: HTMLVideoElement, timestamp: number): LandmarkFrame {
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight
        }
        context.drawImage(video, 0, 0)
        const p = pose.detectForVideo(canvas, timestamp)
        const h = hands.detectForVideo(canvas, timestamp)
        const f = face.detectForVideo(canvas, timestamp)
        return assembleFrame(p.landmarks[0] ?? [], h, f.faceLandmarks[0] ?? [])
      },
      close() {
        resources.forEach((resource) => resource.close())
      },
    }
  } catch (error) {
    resources.forEach((resource) => resource.close())
    throw error
  }
}
