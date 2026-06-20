import cv2
import mediapipe as mp


class FaceMeshRenderer:
    def __init__(
        self,
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ):
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.face_mesh_api = mp.solutions.face_mesh
        self.face_mesh = self.face_mesh_api.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            refine_landmarks=True,
        )
        self.drawer = mp.solutions.drawing_utils
        self.draw_spec = self.drawer.DrawingSpec(thickness=1, circle_radius=1)
        self.results = None

    def find_face(self, image, draw=True):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.face_mesh.process(image_rgb)
        if self.results.multi_face_landmarks and draw:
            for face_landmarks in self.results.multi_face_landmarks:
                self.drawer.draw_landmarks(
                    image,
                    face_landmarks,
                    self.face_mesh_api.FACEMESH_CONTOURS,
                    self.draw_spec,
                    self.draw_spec,
                )
        return image

    def find_landmarks(self, image, draw=False):
        """Return list of [id, cx, cy, norm_x, norm_y, norm_z] for the first face."""
        landmarks = []
        if not self.results or not self.results.multi_face_landmarks:
            return landmarks

        h, w, _ = image.shape
        first_face = self.results.multi_face_landmarks[0]
        for idx, landmark in enumerate(first_face.landmark):
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            landmarks.append([idx, cx, cy, landmark.x, landmark.y, landmark.z])
            if draw:
                cv2.putText(
                    image,
                    str(idx),
                    (cx, cy),
                    cv2.FONT_HERSHEY_PLAIN,
                    0.4,
                    (255, 0, 0),
                    1,
                )
        return landmarks

    def close(self):
        self.face_mesh.close()

    @property
    def face_count(self):
        """How many faces are currently detected (0, 1, 2 ...)."""
        if self.results and self.results.multi_face_landmarks:
            return len(self.results.multi_face_landmarks)
        return 0

    def findFace(self, image, draw=True):
        return self.find_face(image, draw=draw)

    def findLandmarks(self, image, draw=False):
        return self.find_landmarks(image, draw=draw)
