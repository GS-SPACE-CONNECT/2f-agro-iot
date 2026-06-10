"""Sonda de webcam: testa índices x backends do OpenCV e mostra o que abre de verdade."""
import cv2

BACKENDS = [
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF", cv2.CAP_MSMF),
    ("CAP_ANY", cv2.CAP_ANY),
]

print(f"OpenCV {cv2.__version__}")
achou = False
for idx in range(4):
    for nome, be in BACKENDS:
        cap = cv2.VideoCapture(idx, be)
        aberto = cap.isOpened()
        ok, frame = (cap.read() if aberto else (False, None))
        shape = frame.shape if ok and frame is not None else None
        cap.release()
        status = "LEU FRAME" if shape else ("abriu mas nao leu" if aberto else "-")
        print(f"  indice={idx} backend={nome:10s} -> {status} {shape or ''}")
        if shape:
            achou = True
if not achou:
    print("\nNenhuma combinacao funcionou.")
