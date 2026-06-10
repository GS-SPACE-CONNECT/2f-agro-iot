# 🎬 Roteiro do Vídeo — Olho na Folha (50 pts)

**Duração alvo:** 3:00–3:30 (máx 4 min) · **Grave em 1080p horizontal** · microfone perto · fale com calma.
**Regra de ouro:** mostre a **TELA REAL rodando** (não slide). É o que vale os 50 pontos.

> 📌 **Estratégia desta gravação:** o **foco do projeto é a detecção de pragas**
> (modelo YOLOv8 treinado e testado — mostramos a evidência). A **demonstração ao
> vivo é do modo fogo**, que roda de forma confiável com uma vela. Os dois usam o
> mesmo script, então a demo ao vivo do fogo já evidencia **FPS**, **robustez** e
> **tratamento de exceções** que a rubrica pede.
>
> ✅ **Checklist da rubrica:** contexto · arquitetura · script rodando ao vivo ·
> **FPS na tela** · robustez (iluminação, ruído, "pegadinha" de cor).
>
> 🗣️ Para gravar lendo direto, use **[falas-video.txt](falas-video.txt)** (teleprompter puro).
> Este arquivo é a versão de produção (com deixas de tela e tempos).

---

## 0:00 – 0:25 · Abertura + contexto

**[FALA]** o pitch de abertura (ver `falas-video.txt`): 70% do alimento vem do
pequeno produtor → 2F-AGRO → o Olho na Folha detecta praga na folha em tempo real.

**[TELA]** título "2F-AGRO · Olho na Folha" ou o repositório aberto.

## 0:25 – 1:05 · Proposta + exemplo + o modelo de pragas (foco)

**[FALA]** a proposta com um **exemplo concreto** (ver `falas-video.txt`): aponta a
câmera pra um pé de tomate com manchas → "requeima, 95%" em 2 segundos. Depois explique
que por baixo é um **YOLOv8 treinado no PlantVillage** (6 classes) → HUD com confiança e
FPS → API C# com **fila offline**. **Diga que o modelo foi treinado e testado, e
reconheceu as 6 classes.**

**[TELA]** o **diagrama Mermaid** do README e, como **evidência dos testes de praga**,
uma destas opções (escolha a mais fácil):

- as imagens de `assets/samples/` com os rótulos, **ou**
- um print do resultado do teste `tools/conferir_amostras.py` (acertos nas 6 classes), **ou**
- rode por uns segundos `python olho_na_folha.py --source assets/samples/` (passa o
  modelo pelas amostras e mostra a classe detectada — prova o modelo funcionando).

## 1:05 – 1:20 · Ponte pra demo ao vivo

**[FALA]** "Além da detecção de pragas, que é o foco, o Olho na Folha tem um segundo
modo — e é esse que vamos mostrar rodando ao vivo agora: a **detecção de queimada**."
Conecte com o **Programa Queimadas do INPE** (satélite) → a câmera é a contraparte no chão.

## 1:30 – 2:40 · DEMO AO VIVO — fogo (o coração)

**[TELA]** rode `testar_fogo.bat` (ou `python olho_na_folha.py --fogo`) e mostre, nesta ordem:

1. **A janela abrindo** e o **FPS** no canto → *fale "olha o FPS, ~30 quadros por segundo"*.
2. **Acenda uma vela/isqueiro** (ou um vídeo de queimada no celular) → a barra vira
   **vermelha**, **"FOGO DETECTADO"**, e o **retângulo** marca a chama. *Fale a confiança.*
3. **A pegadinha:** aponte pra algo **laranja parado** (capa, cadeira) → continua
   **"Sem fogo"**. Explique: separa fogo de coisa parada pela **cintilação** (chama tremula).
4. **🔆 Robustez:** mexa na **luz** e **balance** a câmera → continua acompanhando sem travar.

## 2:40 – 3:05 · Robustez de engenharia (Script — 30 pts)

**[FALA]** o stream tem **tratamento de exceções**: webcam cai → reconecta; frame
corrompido → pula; API some → enfileira. Não quebra. Modular e com `requirements.txt` fixo.

**[TELA]** scroll rápido no `olho_na_folha.py` mostrando os `try/except` por frame e o
`try/finally` que **sempre libera a câmera**.

## 3:05 – 3:30 · Fechamento

**[FALA]**
> "Esse é o Olho na Folha — a camada de bolso do 2F-AGRO, levando visão computacional
> pra mão de quem alimenta o Brasil."
>
> **"Lançamos satélites no espaço. Está na hora de eles olharem pra cá também."**
>
> "Obrigado!"

**[TELA]** créditos com **nome completo dos integrantes** (abaixo) · FIAP 3ES · GS 2026.1.

---

## 🎥 Comandos prontos pra gravar

No Windows, o jeito mais rápido é o atalho — **dois cliques**:

- `testar_fogo.bat` → demo de **fogo** ao vivo (a demonstração principal)
- `testar_camera.bat` → modo **pragas** ao vivo (caso queira mostrar também)

Ou pela linha de comando:

```bash
# ambiente (Windows): .\.venv-iot-test\Scripts\Activate.ps1
# ambiente (Linux/Mac): source .venv/bin/activate

# Demo ao vivo — fogo:
python olho_na_folha.py --fogo

# Evidência do modelo de pragas (passa pelas amostras reais):
python olho_na_folha.py --source assets/samples/
```

---

## ✅ Antes de gravar (checklist de 1 minuto)

- [ ] **Ensaiar 1x cronometrado** — passar de 4 min leva desconto.
- [ ] Fechar apps que usam a webcam (OBS, Teams, navegador) antes de abrir a demo.
- [ ] Ter à mão: uma **chama** (vela/isqueiro ou vídeo) e a **evidência de pragas** (print/amostras).
- [ ] Conferir que o **FPS aparece** na tela (exigência explícita da rubrica).
- [ ] Mostrar a **pegadinha de cor** (laranja parado = sem fogo) — é o que prova robustez.
- [ ] **Legendas embutidas** + música de fundo baixa (≈10%) elevam o profissionalismo.
- [ ] Créditos no fim com **nome completo dos integrantes** (rubrica exige).

---

## 👥 Créditos (nome completo dos integrantes)

| Nome completo | RM | GitHub |
| --- | --- | --- |
| João Victor Franco | 556790 | [@jota0802](https://github.com/jota0802) |
| Bruno Leão | 555563 | [@brnleao](https://github.com/brnleao) |
| Ruan Melo | 557599 | [@DevRuanVieira](https://github.com/DevRuanVieira) |
| Rodrigo Jimenez | 558148 | [@roji-menez](https://github.com/roji-menez) |
| Lucca Borges | 554608 | [@lucksza](https://github.com/lucksza) |

FIAP · 3ES · Global Solution 2026.1 · **IoT / Physical Computing**
