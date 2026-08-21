import argparse
import time
import os

import cv2
import numpy as np
from ai_edge_litert.interpreter import Interpreter


# ----------------------------------------------------------------------
# 1. Calibration caméra / correction de distorsion
# ----------------------------------------------------------------------
class CameraCalibrator:

    def __init__(self, chessboard_size=(9, 6), square_size_mm=25.0):
        self.chessboard_size = chessboard_size
        self.square_size_mm = square_size_mm
        self.camera_matrix = None
        self.dist_coeffs = None
        self._map1 = None
        self._map2 = None

    def calibrate_from_images(self, image_paths):
        """Calibre la caméra à partir d'une liste de photos de mire en damier."""
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
        objp *= self.square_size_mm

        obj_points = []  # points 3D réels
        img_points = []  # points 2D détectés dans l'image
        img_size = None

        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_size = gray.shape[::-1]

            found, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
            if found:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                obj_points.append(objp)
                img_points.append(corners_refined)

        if len(obj_points) < 5:
            print(f"[Calibration] Seulement {len(obj_points)} mire(s) valide(s) détectée(s) "
                  f"(minimum 5 recommandé) -- calibration ignorée, pas de distorsion appliquée.")
            return False

        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, img_size, None, None
        )
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        print(f"[Calibration] Terminée. Erreur de reprojection: {ret:.4f}")
        return True

    def build_undistort_maps(self, frame_shape):
        """Prépare les maps de correction (plus rapide que undistort() à chaque frame)."""
        if self.camera_matrix is None:
            return
        h, w = frame_shape[:2]
        new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
        )
        self._map1, self._map2 = cv2.initUndistortRectifyMap(
            self.camera_matrix, self.dist_coeffs, None, new_camera_matrix, (w, h), cv2.CV_16SC2
        )

    def undistort(self, frame):
        """Applique la correction de distorsion si une calibration existe, sinon no-op."""
        if self._map1 is None:
            return frame
        return cv2.remap(frame, self._map1, self._map2, interpolation=cv2.INTER_LINEAR)


def adaptive_threshold_preview(frame):
    """
    Seuillage adaptatif (utile pour visualiser les contours/lignes sous
    éclairage inégal -- le seuil de coupure varie localement plutôt que
    d'être un seuil fixe global).
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )
    return thresh


class FaceDetector:
    def __init__(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        if self.cascade.empty():
            raise RuntimeError(f"Impossible de charger le classificateur Haar: {cascade_path}")

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)  # améliore le contraste avant détection
        faces = self.cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        return faces  # liste de (x, y, w, h)


class TFLiteObjectDetector:
    def __init__(self, model_path, labels_path, score_threshold=0.5):
        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_height = self.input_details[0]['shape'][1]
        self.input_width = self.input_details[0]['shape'][2]
        self.input_dtype = self.input_details[0]['dtype']
        self.score_threshold = score_threshold
        self.labels = self._load_labels(labels_path)

    @staticmethod
    def _load_labels(path):
        with open(path, "r") as f:
            return [line.strip() for line in f.readlines()]

    def detect(self, frame):
        h, w, _ = frame.shape

        # Prétraitement : resize + format attendu par le modèle
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.input_width, self.input_height))
        input_data = np.expand_dims(img, axis=0)
        if self.input_dtype == np.float32:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        # Inférence
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]

        results = []
        for i in range(len(scores)):
            if scores[i] >= self.score_threshold:
                ymin, xmin, ymax, xmax = boxes[i]
                x1, y1 = int(xmin * w), int(ymin * h)
                x2, y2 = int(xmax * w), int(ymax * h)
                class_id = int(classes[i])
                label = self.labels[class_id] if class_id < len(self.labels) else f"id_{class_id}"
                results.append({
                    "box": (x1, y1, x2, y2),
                    "label": label,
                    "score": float(scores[i]),
                })
        return results


def run_pipeline(source, model_path, labels_path, display=True, max_frames=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    calibrator = CameraCalibrator()
    # Si des images de calibration existent dans ./calibration_images/, on les utilise.
    calib_dir = os.path.join(script_dir, "calibration_images")
    if os.path.isdir(calib_dir):
        images = [os.path.join(calib_dir, f) for f in os.listdir(calib_dir)
                  if f.lower().endswith((".jpg", ".png"))]
        if images:
            calibrator.calibrate_from_images(images)

    face_detector = FaceDetector()
    object_detector = TFLiteObjectDetector(model_path, labels_path, score_threshold=0.5)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la source vidéo: {source}")

    maps_built = False
    frame_count = 0
    fps_smooth = 0.0
    alpha = 0.9  # lissage exponentiel du FPS affiché

    while True:
        t_start = time.time()
        ret, frame = cap.read()
        if not ret:
            break

        if not maps_built:
            calibrator.build_undistort_maps(frame.shape)
            maps_built = True

        # 1. Correction de distorsion
        frame = calibrator.undistort(frame)

        # 2. Seuillage adaptatif (aperçu diagnostic, pas utilisé pour la détection)
        thresh_preview = adaptive_threshold_preview(frame)

        # 3. Détection de visages (Haar Cascade)
        faces = face_detector.detect(frame)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, "visage", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # 4. Détection d'objets (TFLite)
        objects = object_detector.detect(frame)
        for obj in objects:
            x1, y1, x2, y2 = obj["box"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{obj['label']} {obj['score']:.2f}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 5. FPS
        elapsed = time.time() - t_start
        fps = 1.0 / elapsed if elapsed > 0 else 0.0
        fps_smooth = alpha * fps_smooth + (1 - alpha) * fps if frame_count > 0 else fps
        cv2.putText(frame, f"FPS: {fps_smooth:.1f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        if display:
            cv2.imshow("Vision Pipeline - detection", frame)
            cv2.imshow("Vision Pipeline - seuillage adaptatif", thresh_preview)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_count += 1
        if max_frames and frame_count >= max_frames:
            break

    cap.release()
    if display:
        cv2.destroyAllWindows()

    print(f"[Résumé] {frame_count} frames traitées, FPS moyen final: {fps_smooth:.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de vision: Haar Cascade + TFLite")
    parser.add_argument("--source", default="0", help="Index caméra (0) ou chemin vidéo")
    parser.add_argument("--model", default="detect.tflite", help="Chemin du modèle TFLite")
    parser.add_argument("--labels", default="coco_labels.txt", help="Chemin du fichier de labels")
    parser.add_argument("--no-display", action="store_true", help="Désactive l'affichage (headless)")
    parser.add_argument("--max-frames", type=int, default=None, help="Limite le nombre de frames (test)")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    run_pipeline(
        source=source,
        model_path=args.model,
        labels_path=args.labels,
        display=not args.no_display,
        max_frames=args.max_frames,
    )
