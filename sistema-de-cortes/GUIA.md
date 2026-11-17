# Sistema de Cortes de Lives

Transforma lives (ex.: GTA 6) em cortes verticais para Reels, TikTok e Shorts:
acha os gritos e reações, transcreve a fala, coloca título e legenda.

```
[Mac] grava a live em blocos de 20 min  →  [Claude] acha os momentos  →  você aprova  →  [Claude] entrega os cortes
```

> ⚠️ Só publique cortes de lives **suas** ou de streamers que **autorizam** cortes.

---

## Arquivos

| Arquivo | Onde roda | Para que serve |
|---|---|---|
| `gravar_live.command` | No seu Mac | Grava tela + som em blocos de 20 min (720p) |
| `sistema_cortes.py` | No Claude (nuvem) | Acha momentos, transcreve, corta, legenda |
| `instalar.sh` | No Claude (nuvem) | Instala o Whisper (transcrição) numa sessão nova |

---

## Parte 1: Preparar o Mac (só uma vez)

1. **BlackHole 2ch**, o "cano" que leva o som do computador para a gravação:
   baixe em `https://existential.audio/downloads/BlackHole2ch-0.7.1.pkg` e instale.
   (Impressão digital: começa com `57b540f2`.)
2. **Configuração de Áudio e MIDI** → `+` → **Criar Dispositivo de Saída Múltipla**:
   marque **Saída Integrada** e **BlackHole 2ch**; principal = Saída Integrada;
   marque **Corrigir Ruído** na linha do BlackHole.
3. **ffmpeg**: em `https://evermeet.cx/ffmpeg/`, clique em **Download as ZIP** (abaixo do botão da versão
   estável), descompacte e deixe o arquivo `ffmpeg` em **Downloads**.
4. Coloque o `gravar_live.command` em **Downloads** e libere os dois no **Terminal**:
   ```
   cd ~/Downloads && xattr -c ffmpeg gravar_live.command; chmod +x ffmpeg gravar_live.command
   ```
5. **Preferências do Sistema → Segurança e Privacidade → Privacidade → Gravação de Tela** → marque **Terminal**.

**Dicas para o Mac**
- O Terminal fica em: Finder → `Command + Shift + U` → Terminal.
- Com a Saída Múltipla ligada, as teclas de volume não funcionam. Para baixar só o som dos
  alto-falantes **sem baixar a gravação**: Configuração de Áudio e MIDI → **Saída Integrada** →
  aba Saída → ajuste o volume ali. Deixe o volume do player da live **no máximo**.

---

## Parte 2: Gravar uma live

1. **Preferências do Sistema → Som → Saída** → **Dispositivo de Saída Múltipla**.
2. Abra a live no Chrome, em **tela cheia** (tecla `F` no YouTube), volume do player no máximo.
3. No Terminal:
   ```
   cd ~/Downloads && ./gravar_live.command
   ```
4. A cada 20 min, aparece um bloco novo em **Filmes → Lives** (~360 MB).
5. Para parar: `Control + C` no Terminal.
6. Ao terminar: **Som → Saída → Saída Integrada** (as teclas de volume voltam a funcionar).

---

## Parte 3: Fazer os cortes (no Claude)

Numa sessão nova do Claude Code com este repositório:

1. Ative **Configurações → Recursos → Permitir acesso de rede externo**.
2. Peça: *"rode o instalar.sh do sistema-de-cortes"* (só uma vez por sessão).
3. Anexe um bloco da live e peça: *"analise este bloco e me mostre os momentos"*.

O Claude roda:
```
python3 sistema_cortes.py analisar bloco.mp4 --max 10 --dur 30
```
e mostra a lista (horário, GRITO/REAÇÃO, fala, print). Você aprova e escolhe os títulos. Depois:
```
python3 sistema_cortes.py cortar bloco.mp4 momentos.json --ids 1,3,5 \
        --cam LARGURA:ALTURA:X:Y --jogo LARGURA:ALTURA:X:Y
```
- `--cam` e `--jogo` = onde ficam a câmera do streamer e o jogo na tela. O Claude descobre
  olhando um print. Sem eles, o vídeo inteiro fica centralizado sobre um fundo desfocado.
- Exemplo usado no teste (tela 1440×900, live em tela cheia):
  `--cam 287:199:1153:211 --jogo 1000:810:150:45`

**O que sai:** vídeo 1080×1920, câmera em cima, jogo embaixo, título amarelo no topo,
legenda palavra por palavra na divisa, palavrões censurados (`P*RRA`).

---

## Limites conhecidos

- O Claude não ouve música e efeitos sonoros: ele mede o **volume** (gritos) e lê a **fala** (transcrição).
- A transcrição pode errar palavras ("Fale" em vez de "Fala"). Sempre revise antes de postar.
- O YouTube não é acessível do ambiente do Claude: a live precisa ser gravada ou enviada como arquivo.
- O MacBook Air (dual-core 1,8 GHz) grava bem, mas é lento demais para transcrever. Por isso
  os cortes são feitos no Claude.

## Próximas fases

- **Fase 2:** postagem com fila de aprovação (agendador para TikTok, Reels e Shorts).
