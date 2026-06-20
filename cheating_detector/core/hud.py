import cv2


def draw_hud(
    image,
    features,
    score,
    label,
    colour,
    fps,
    face_count,
    collect_mode=False,
    current_label=0,
):
    """Draws all on-screen information."""
    h, w = image.shape[:2]
    overlay = image.copy()

    cv2.rectangle(overlay, (0, 0), (w, 110), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.55, image, 0.45, 0, image)

    cv2.putText(
        image,
        f"FPS: {round(fps)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (200, 200, 200),
        1,
    )

    if face_count == 0:
        cv2.putText(
            image,
            "NO FACE DETECTED",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 220),
            2,
        )
    elif face_count > 1:
        cv2.putText(
            image,
            f"{face_count} FACES! (SUSPICIOUS)",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 220),
            2,
        )
    else:
        cv2.putText(
            image,
            "Face OK",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 200, 0),
            1,
        )

    badge_text = f"{label}  {score}"
    (tw, _), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
    bx = w - tw - 20
    cv2.rectangle(image, (bx - 8, 8), (w - 8, 40), colour, -1)
    cv2.putText(
        image,
        badge_text,
        (bx, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
    )

    if features:
        panel_y = h - 160
        cv2.rectangle(image, (0, panel_y), (270, h), (20, 20, 20), -1)
        lines = [
            f"Gaze X : {features['gaze_x']:+.3f}",
            f"Gaze Y : {features['gaze_y']:+.3f}",
            f"Blink/m: {features['blink_rate']:.1f}",
            f"Yaw    : {features['head_yaw']:+.1f} deg",
            f"Pitch  : {features['head_pitch']:+.1f} deg",
            f"Roll   : {features['head_roll']:+.1f} deg",
            f"EAR    : {features['ear']:.3f}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(
                image,
                line,
                (8, panel_y + 20 + i * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

    if collect_mode:
        label_text = f"LABEL: {'0-NORMAL' if current_label == 0 else '1-SUSPICIOUS'}"
        label_colour = (0, 200, 0) if current_label == 0 else (0, 0, 220)
        cv2.putText(
            image,
            label_text,
            (10, h - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            label_colour,
            2,
        )
        cv2.putText(
            image,
            "Press 0=Normal  1=Suspicious  Q=Quit+Save",
            (10, h - 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 180, 180),
            1,
        )
