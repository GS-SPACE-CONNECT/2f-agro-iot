# 🎬 Roteiro do Vídeo — Olho na Folha (50 pts)

**Duração alvo:** 3:00–3:30 (máx 4 min) · **Grave em 1080p** · fale com calma.
**Dica:** ensaie 1x cronometrado. Mostre a TELA REAL rodando (não slide).

> Checklist da rubrica que o vídeo PRECISA mostrar: ✅ contexto · ✅ arquitetura ·
> ✅ script rodando ao vivo · ✅ **FPS na tela** · ✅ robustez (luz/oclusão).

---

## 0:00 – 0:25 · Abertura + contexto

> "Oi, somos a equipe do **2F-AGRO**. Esse é o módulo de **IoT / Visão Computacional**,
> o **Olho na Folha**. O pequeno produtor aponta a câmera pra uma folha suspeita e,
> em tempo real, o sistema diz qual praga ou doença está atacando — sem internet
> rápida, sem laboratório."

**[TELA]** Logo/título do projeto ou o repositório aberto.

## 0:25 – 1:00 · Arquitetura

> "Por baixo: a webcam manda o frame pro **YOLOv8 de classificação**, que treinamos
> em cima do dataset PlantVillage com 6 classes de pragas. O resultado aparece na
> tela com a confiança e o **FPS**, e — quando a confiança passa de 70% — o
> diagnóstico é enviado pra nossa **API de alertas em C#**. Se a API estiver fora do
> ar, ele guarda numa fila offline e reenvia depois."

**[TELA]** Mostre o **diagrama Mermaid** do README (pipeline). Aponte o fluxo:
webcam → modelo → HUD → API/fila.

## 1:00 – 1:20 · Por que classificação (mostra maturidade)

> "Uma decisão técnica importante: usamos **classificação**, não detecção por caixas.
> O PlantVillage é um dataset de classificação, então essa escolha treina mais rápido
> e fica mais robusta — exatamente o que a aplicação em tempo real precisa."

**[TELA]** Trecho da spec/README com a "Nota honesta de escopo".

## 1:20 – 2:30 · DEMO AO VIVO (o coração — capriche)

> "Vamos ver rodando."

**[TELA]** Rode `python olho_na_folha.py` (ou `--source assets/samples/`). Mostre:

1. **A janela abrindo** e o **FPS** no canto superior direito → *fale "olha o FPS aqui"*.
2. Aproxime uma **folha doente** (impressa ou na planta) → a classe muda e a barra
   de confiança sobe. Leia em voz alta: *"detectou ferrugem com 92%"*.
3. Mostre uma **folha saudável** → status fica **verde** e não dispara alerta.
4. **Robustez — iluminação:** diminua/aumente a luz (ou afaste/aproxime) e mostre
   que continua classificando.
5. **Robustez — oclusão:** tampe parte da folha com o dedo → mostre que não trava.
6. (Opcional) terminal com o **mock da API** recebendo o POST do diagnóstico.

## 2:30 – 3:00 · Robustez de engenharia + fechamento

> "No código tem tratamento de exceções em todo o stream: se a webcam cai, ele
> reconecta; se um frame vem corrompido, ele pula; se a API some, ele enfileira.
> O programa não quebra. Tudo modularizado e com `requirements.txt` fixo."

**[TELA]** Rápido scroll no `olho_na_folha.py` mostrando os `try/except` e o `finally`.

> "Esse é o Olho na Folha — a camada de bolso do 2F-AGRO, levando visão computacional
> pra mão do agricultor. Obrigado!"

**[TELA]** Créditos: **João Victor Franco (RM 556790)** e **Lucca Saraiva Borges (RM 554608)** · FIAP 3ES · GS 2026.1.

---

### Comandos prontos pra gravar

```bash
source .venv/bin/activate

# Demo principal (webcam):
python olho_na_folha.py

# Se a webcam falhar na hora, use as imagens de amostra:
python olho_na_folha.py --source assets/samples/

# (Opcional) mostrar a API recebendo — em 2 terminais:
python tools/mock_api.py 5000
python olho_na_folha.py --api-url http://localhost:5000/api/diagnostico
```
