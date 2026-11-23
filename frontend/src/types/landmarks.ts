export type LandmarkPoint = [number, number, number]

export type LandmarkFrame = {
  points: LandmarkPoint[]
  valid: boolean[]
}

export type LandmarkCapture = {
  points: LandmarkPoint[][]
  valid: boolean[][]
  fps: number
}
