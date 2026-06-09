# Spec · Olho na Folha (2f-agro-iot)

**Data:** 2026-06-06 · **Matéria:** IoT / Physical Computing (100 pts) · **GS 2026.1**
**Owners:** João Victor Franco (RM 556790, @jota0802), Lucca Saraiva Borges (RM 554608, @lucksza)

## Problema

O pequeno produtor não tem como identificar rápido uma praga numa folha. O módulo
"Olho na Folha" do 2F-AGRO resolve isso: câmera apontada pra folha → praga
identificada em tempo real → alerta enviado pra API de recomendações.

## Decisão de arquitetura: classificação, não detecção

A spec do hub e as issues sugeriam "fine-tuning YOLOv8 **detection** convertendo o
PlantVillage pra boxes". Isso é uma **armadilha**: o PlantVillage é um dataset de
**classificação** (uma folha centralizada por imagem, sem caixas). Forçar boxes
ensinaria o modelo a só desenhar uma caixa na imagem inteira.

Como a nota está no **vídeo (50)** e no **script robusto (30)** — não na sofisticação
do modelo — adotamos **YOLOv8-cls (classificação)**:

- casa 1:1 com o formato do PlantVillage (pasta-por-classe);
- treina em minutos (inclusive em CPU);
- inferência estável → demo fluida e FPS alto;
- a própria spec diz "classifica praga/doença em tempo real".

## Componentes (cada um com uma responsabilidade)

| Módulo | Responsabilidade | Depende de |
| --- | --- | --- |
| `src/config.py` | constantes, threshold, mapa de classes PT-BR | — |
| `src/classifier.py` | carrega YOLOv8-cls e infere `(classe, conf)` | ultralytics |
| `src/camera.py` | fonte de frames (webcam/vídeo/imagens) + reconexão | opencv |
| `src/overlay.py` | HUD: classe + barra de confiança + FPS | opencv |
| `src/api_client.py` | POST /diagnostico + fila offline + throttle | requests |
| `olho_na_folha.py` | orquestra o loop em tempo real | todos acima |

## Fluxo de dados

`webcam → frame → classifier → (classe, conf) → overlay (FPS) → janela`
e, em paralelo, `se conf ≥ 0.70 e não-saudável → api_client.enviar() → POST/fila`.

## Tratamento de erros (rubrica — obrigatório)

- Webcam indisponível → mensagem clara + saída limpa (não stacktrace cru).
- Frame corrompido → pula sem derrubar o stream.
- Falha de inferência num frame → loga e continua.
- API fora/timeout → captura, enfileira offline, **stream nunca cai**.
- `try/finally` global libera câmera e fecha janelas sempre.

## 6 classes

`mancha_bacteriana_tomate`, `requeima_tomate`, `oidio_mofo_branco`,
`podridao_negra_uva`, `ferrugem_milho`, `saudavel`.
(Café não existe no PlantVillage → substituído por ferrugem do milho; ver README.)

## Modelo & treino

- Base: `yolov8n-cls.pt` (ImageNet) → fine-tuning nas 6 classes.
- Dataset: PlantVillage (color), 600 imgs/classe, split 80/20.
- Local: CPU (~20 épocas). Escala: Colab GPU (`train/colab_treino.ipynb`).
- Saída versionada: `models/2fagro-folha-cls-v1.pt`.

## Testes

- `tests/smoke_test.py` — headless, valida config/overlay/api/camera/classifier.
- Demo headless: `olho_na_folha.py --source assets/samples/ --headless --save out/`.
- `tools/mock_api.py` — exercita o caminho de envio sem o backend C#.

## Critérios de aceite

1. `pip install -r requirements.txt` instala sem conflito (testado).
2. `python olho_na_folha.py` abre a webcam e mostra classe + conf + **FPS**.
3. Programa não cai com webcam ausente, frame ruim ou API offline.
4. Modelo classifica corretamente ≥3 classes nas imagens de amostra.
