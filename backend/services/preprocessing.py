"""Prétraitement des points MediaPipe : NumPy uniquement."""
from pathlib import Path
import argparse
import json
import numpy as np

BASE = Path(__file__).resolve().parents[1] / "assets"
FRAMES, N_POINTS, INPUT_DIM = 90, 96, 350
PRETRAITEMENT = "mediapipe96-geometrie175-v1"


# Conserve la période où une main est détectée, avec une marge avant et après.
def trim_sequence(points, valid, fps, margin_s=0.5):
    present = (valid[:, 0] | valid[:, 21]).astype(float)
    if not present.any():
        raise ValueError("Aucune main détectée")
    window = min(len(present), max(3, round(0.3 * fps)))
    smoothed = np.convolve(present, np.ones(window) / window, mode="same")
    active = np.flatnonzero(smoothed >= 0.25)
    if not len(active):
        active = np.flatnonzero(present)
    margin = round(margin_s * fps)
    start = max(0, int(active[0]) - margin)
    end = min(len(points), int(active[-1]) + margin + 1)
    return points[start:end], valid[start:end]


# Centre et ajuste les coordonnées XY selon les épaules, puis masque les points absents.
def normalize(points, valid):
    points = points.copy()
    left, right = 42 + 11, 42 + 12
    widths = np.linalg.norm(points[:, left, :2] - points[:, right, :2], axis=1)
    good = valid[:, left] & valid[:, right] & (widths > 0.02)
    if not good.any():
        raise ValueError("Épaules non exploitables")
    scale = np.median(widths[good])
    centers = (points[:, left, :2] + points[:, right, :2]) / 2
    idx = np.arange(len(points))
    origin = np.column_stack([np.interp(idx, idx[good], centers[good, axis]) for axis in range(2)])
    points[:, :, :2] = (points[:, :, :2] - origin[:, None, :]) / scale
    points[~valid] = 0  # Z conserve son repère MediaPipe propre à chaque détecteur
    return points


# Rééchantillonne les points aux instants demandés en respectant leur présence.
def temporal_sample(points, valid, positions):
    T = len(points)

    positions = np.clip(positions, 0, T - 1)

    left = np.floor(positions).astype(int)
    right = np.minimum(left + 1, T - 1)
    nearest = np.rint(positions).astype(int)

    alpha = (positions - left)[:, None, None]

    interp = (1 - alpha) * points[left] + alpha * points[right]

    new_valid = valid[nearest]
    both_valid = valid[left] & valid[right]

    output = np.where(
        both_valid[..., None],
        interp,
        points[nearest]
    )

    output[~new_valid] = 0

    return output.astype(np.float32), new_valid


GROUPS = ("local", "angles", "distances", "vitesse", "relations")

FINGERS = ((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12),
           (13, 14, 15, 16), (17, 18, 19, 20))

TRIPLES = np.array([(offset + c[i], offset + c[i + 1], offset + c[i + 2])
                    for offset in (0, 21) for c in FINGERS for i in (0, 1)])

PAIRS = np.array([(o + tip, o) for o in (0, 21) for tip in (4, 8, 12, 16, 20)] +
                 [(o + a, o + b) for o in (0, 21) for a, b in
                  ((4, 8), (8, 12), (12, 16), (16, 20))])

PAIR_HAND = np.array([0] * 5 + [1] * 5 + [0] * 4 + [1] * 4)

MOTION_POINTS = [0, 4, 8, 12, 16, 20, 21, 25, 29, 33, 37, 41, 55, 56, 57, 58]

RELATIONS = np.array([(0, 89), (21, 89), (0, 53), (21, 54),
                      (0, 21), (0, 55), (21, 56)])

# Calcule les caractéristiques géométriques et leurs masques de présence.
def build_features(points, valid, blocks=GROUPS):
    """Returns (T, 175) geometry and the matching boolean observation mask."""
    T = len(points)
    pieces, observed = [], []

    # Ajoute un groupe de caractéristiques en mettant à zéro les valeurs non observées.
    def add(values, mask):
        mask = np.broadcast_to(mask, values.shape)
        pieces.append(np.where(mask, values, 0).reshape(T, -1).astype(np.float32))
        observed.append(mask.reshape(T, -1).copy())

    hand_scales, hand_ok = [], []
    for offset in (0, 21):
        d = np.linalg.norm(points[:, offset + 9, :2] - points[:, offset, :2], axis=1)
        good = valid[:, offset + 9] & valid[:, offset] & (d > 1e-4)
        hand_ok.append(bool(good.any()))
        hand_scales.append(float(np.median(d[good])) if good.any() else 1.0)

    for block in blocks:
        if block == "local":
            for hand, offset in enumerate((0, 21)):
                xy = (points[:, offset:offset + 21, :2] -
                      points[:, offset:offset + 1, :2]) / hand_scales[hand]
                ok = valid[:, offset:offset + 21] & valid[:, offset:offset + 1] & hand_ok[hand]
                add(xy, ok[..., None])

        elif block == "angles":
            a, b, c = TRIPLES.T
            u = points[:, a, :2] - points[:, b, :2]
            w = points[:, c, :2] - points[:, b, :2]
            nu, nw = np.linalg.norm(u, axis=-1), np.linalg.norm(w, axis=-1)
            cosine = np.clip(np.sum(u * w, axis=-1) / np.maximum(nu * nw, 1e-8), -1, 1)
            ok = valid[:, a] & valid[:, b] & valid[:, c] & (nu > 1e-4) & (nw > 1e-4)
            add(cosine, ok)

        elif block == "distances":
            a, b = PAIRS.T
            d = np.linalg.norm(points[:, a, :2] - points[:, b, :2], axis=-1)
            scales = np.array(hand_scales)[PAIR_HAND]
            ok = valid[:, a] & valid[:, b] & np.array(hand_ok)[PAIR_HAND]
            add(d / scales, ok)

        elif block == "vitesse":
            pos = points[:, MOTION_POINTS, :2]
            m = valid[:, MOTION_POINTS]
            velocity = np.zeros_like(pos)
            velocity[1:] = pos[1:] - pos[:-1]
            ok = np.zeros_like(m)
            ok[1:] = m[1:] & m[:-1]
            add(velocity, ok[..., None])

        elif block == "relations":
            a, b = RELATIONS.T
            xy = points[:, a, :2] - points[:, b, :2]
            values = np.concatenate([xy, np.linalg.norm(xy, axis=-1, keepdims=True)], axis=-1)
            ok = valid[:, a] & valid[:, b]
            add(values, ok[..., None])
        else:
            raise ValueError(f"Unknown feature block: {block}")

    return np.concatenate(pieces, axis=1), np.concatenate(observed, axis=1)

# Standardise les caractéristiques et leur ajoute les masques de présence.
def encode_features(points, valid, mean, std):
    values, observed = build_features(points, valid)
    x = np.where(observed, np.clip((values - mean) / std, -6, 6), 0)
    return np.concatenate((x, observed.astype(np.float32)), axis=1).astype(np.float32)


# Lit les métadonnées et vérifie leur compatibilité avec le prétraitement.
def charger_metadata(path=BASE / "metadata.json"):
    metadata = json.loads(Path(path).read_text(encoding="utf-8"))
    if (metadata["pretraitement"] != PRETRAITEMENT
            or metadata["entree"] != [1, FRAMES, INPUT_DIM]):
        raise ValueError("Les métadonnées ne correspondent pas au prétraitement.")
    mean, std = (np.asarray(metadata[key], dtype=np.float32) for key in ("mean", "std"))
    if (mean.shape != (175,) or std.shape != (175,)
            or not np.isfinite([mean, std]).all() or (std <= 0).any()):
        raise ValueError("Statistiques de standardisation invalides.")
    return metadata


# Valide les points MediaPipe et produit le tenseur float32 de forme (1, 90, 350).
def pretraiter_points(points, valid, fps, metadata=BASE / "metadata.json"):
    """Convertit les points bruts (T, 96, 3) en float32 (1, 90, 350)."""
    points = np.asarray(points, dtype=np.float32)
    valid = np.asarray(valid)
    if points.ndim != 3 or points.shape[1:] != (N_POINTS, 3) or len(points) < 5:
        raise ValueError("Il faut au moins 5 images de 96 points à 3 coordonnées.")
    if valid.shape != points.shape[:2] or valid.dtype != np.bool_:
        raise ValueError("Il faut 96 booléens de présence par image.")
    if not np.isfinite(points).all() or not np.isfinite(fps) or fps <= 0:
        raise ValueError("Coordonnées ou cadence de capture invalides.")
    metadata = metadata if isinstance(metadata, dict) else charger_metadata(metadata)
    mean, std = (np.asarray(metadata[key], dtype=np.float32) for key in ("mean", "std"))
    points, valid = trim_sequence(points, valid, fps)
    points = normalize(points, valid)
    points, valid = temporal_sample(points, valid, np.linspace(0, len(points) - 1, FRAMES))
    return encode_features(points, valid, mean, std)[None]


# Convertit une capture JSON en fichier NumPy depuis la ligne de commande.
def main():
    parser = argparse.ArgumentParser(description="Préparer les points MediaPipe pour ONNX.")
    parser.add_argument("capture", type=Path, help="Fichier JSON contenant points, valid et fps")
    parser.add_argument("--metadata", type=Path, default=BASE / "metadata.json")
    parser.add_argument("--sortie", type=Path)
    args = parser.parse_args()
    sortie = args.sortie or args.capture.with_name(f"{args.capture.stem}_entree.npy")
    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8"))
        entree = pretraiter_points(capture["points"], capture["valid"], capture["fps"], args.metadata)
        sortie.parent.mkdir(parents=True, exist_ok=True)
        np.save(sortie, entree, allow_pickle=False)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        parser.exit(1, f"Prétraitement impossible : {error}\n")
    print(f"Entrée sauvegardée : {sortie} · {entree.shape} · {entree.dtype}")


if __name__ == "__main__":
    main()
