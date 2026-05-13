import cv2
import mediapipe as mp

mpHands = mp.solutions.hands
draw = mp.solutions.drawing_utils

camera = cv2.VideoCapture(0)

hands = mpHands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7
)


def dedos_levantados(pontos):
    total = 0

    # polegar
    if pontos[4].x < pontos[3].x:
        total += 1

    # indicador, medio, anelar e mindinho
    dedos = [8, 12, 16, 20]

    for dedo in dedos:
        if pontos[dedo].y < pontos[dedo - 2].y:
            total += 1

    return total


while True:
    ok, img = camera.read()

    if not ok:
        print("Erro ao acessar camera")
        break

    img = cv2.flip(img, 1)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    resultado = hands.process(rgb)

    if resultado.multi_hand_landmarks:

        for mao in resultado.multi_hand_landmarks:

            draw.draw_landmarks(
                img,
                mao,
                mpHands.HAND_CONNECTIONS
            )

            pontos = mao.landmark

            qtd_dedos = dedos_levantados(pontos)

            cv2.putText(
                img,
                f"Dedos: {qtd_dedos}",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            if qtd_dedos == 5:
                cv2.putText(
                    img,
                    "Mao aberta",
                    (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

                print("Detectou mao aberta")

    cv2.imshow("Camera", img)

    tecla = cv2.waitKey(1)

    if tecla == 27:
        break

camera.release()
cv2.destroyAllWindows()