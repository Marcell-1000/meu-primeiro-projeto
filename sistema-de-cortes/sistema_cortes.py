#!/usr/bin/env python3
"""Sistema de cortes: acha momentos (picos de volume + frases de reacao),
transcreve a fala e gera clipes verticais 9:16 com titulo e legenda.

Uso:
  analisar:  python3 sistema_cortes.py analisar VIDEO [--max 10]
  cortar:    python3 sistema_cortes.py cortar VIDEO momentos.json [--ids 1,3,5]
             [--cam 287:199:1153:211 --jogo 1000:810:150:45]   (camera em cima + jogo embaixo)
"""
import argparse, json, os, re, subprocess, sys

MODEL = os.environ.get("WHISPER_MODEL", os.path.expanduser("~/models/whisper-small"))
PALAVROES = {"porra": "P*RRA", "caralho": "C*RALHO", "merda": "M*RDA", "puta": "P*TA", "foda": "F*DA", "fdp": "F*P", "cacete": "C*CETE", "buceta": "B*CETA"}
REACOES = r"(meu deus|olha isso|n[aã]o acredito|caramba|nossa|socorro|corre|que isso|mds|eita|vai vai|caraca|ai meu)"


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duracao(video):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video])
    return float(r.stdout.strip())


def volume_por_segundo(video):
    """Volume (LUFS momentaneo) a cada ~0.1s, agrupado por segundo."""
    # volume RMS em blocos de 0.1 s (audio reamostrado a 16 kHz)
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-i", video, "-vn",
            "-ac", "1", "-ar", "16000", "-af",
            "asetnsamples=n=1600,astats=metadata=1:reset=1,"
            "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
            "-f", "null", "-"])
    por_seg, t = {}, None
    for linha in r.stdout.splitlines():
        m = re.search(r"pts_time:([\d.]+)", linha)
        if m:
            t = float(m.group(1)); continue
        m = re.search(r"RMS_level=(-?[\d.]+)", linha)
        if m and t is not None:
            s = int(t)
            por_seg[s] = max(por_seg.get(s, -120.0), float(m.group(1)))
    return por_seg


def transcrever(video, lingua="pt"):
    import numpy as np
    from faster_whisper import WhisperModel
    # decodifica o audio com o ffmpeg (16 kHz, mono) e entrega ao Whisper
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    modelo = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language=lingua, word_timestamps=True, vad_filter=True)
    palavras = []
    for s in segs:
        for w in (s.words or []):
            palavras.append({"i": round(w.start, 2), "f": round(w.end, 2), "t": w.word.strip()})
    return palavras


def texto_entre(palavras, a, b):
    return " ".join(p["t"] for p in palavras if a <= p["i"] < b)


def analisar(video, maximo, dur_clipe):
    total = duracao(video)
    vol = volume_por_segundo(video)
    print("Transcrevendo a fala (pode levar alguns minutos)...", file=sys.stderr)
    palavras = transcrever(video)
    with open("transcricao.json", "w") as f:
        json.dump(palavras, f, ensure_ascii=False)

    valores = sorted(vol.values())
    mediana = valores[len(valores) // 2] if valores else -30
    candidatos = []
    for s, v in vol.items():
        pontos = max(0.0, v - mediana)  # quanto mais alto que o normal
        txt = texto_entre(palavras, s - 1, s + 2).lower()
        reacao = bool(re.search(REACOES, txt))
        if reacao:
            pontos += 6
        if pontos > 4:
            candidatos.append((pontos, s, "GRITO" if v - mediana > 8 else "REAÇÃO"))

    candidatos.sort(reverse=True)
    escolhidos = []
    for pontos, s, tipo in candidatos:
        if all(abs(s - e["pico"]) > dur_clipe for e in escolhidos):
            ini = max(0, s - int(dur_clipe * 0.6))
            fim = min(total, ini + dur_clipe)
            escolhidos.append({"pico": s, "inicio": ini, "fim": fim, "tipo": tipo,
                               "pontos": round(pontos, 1),
                               "fala": texto_entre(palavras, ini, fim)[:200],
                               "titulo": ""})
        if len(escolhidos) >= maximo:
            break
    escolhidos.sort(key=lambda e: e["inicio"])
    for n, e in enumerate(escolhidos, 1):
        e["id"] = n
        sh(["ffmpeg", "-y", "-v", "error", "-ss", str(e["pico"]), "-i", video,
            "-frames:v", "1", "-vf", "scale=480:-2", f"print_{n:02d}.jpg"])
    with open("momentos.json", "w") as f:
        json.dump(escolhidos, f, ensure_ascii=False, indent=2)
    for e in escolhidos:
        mm, ss = divmod(e["pico"], 60)
        print(f'{e["id"]:>2}. {mm:02d}:{ss:02d}  {e["tipo"]:<7} "{e["fala"][:70]}"')


def ass_tempo(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def censurar(txt):
    for p, r in PALAVROES.items():
        txt = re.sub(rf"(?i)\b{p}", r, txt)
    return txt


def gerar_legenda(palavras, ini, fim, titulo, arq, margem_leg=560):
    """Legenda estilo Reels: 3 palavras por vez, grande, centro-baixo; titulo no topo."""
    margem_tit = 60 if margem_leg != 560 else 170
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,DejaVu Sans,88,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,{margem_leg},1
Style: Tit,DejaVu Sans,78,&H0000E5FF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,7,2,8,60,60,{margem_tit},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    dur = fim - ini
    if titulo:
        linhas.append(f"Dialogue: 0,{ass_tempo(0)},{ass_tempo(dur)},Tit,,0,0,0,,{censurar(titulo).upper()}")
    ps = [p for p in palavras if ini <= p["i"] < fim]
    # agrupa ate 3 palavras, quebrando no fim de frase (. ? !) e em pausas longas
    grupos, atual = [], []
    for k, p in enumerate(ps):
        if atual and (p["i"] - atual[-1]["f"] > 0.8):
            grupos.append(atual); atual = []
        atual.append(p)
        if len(atual) == 3 or re.search(r"[.?!…]$", p["t"]):
            grupos.append(atual); atual = []
    if atual:
        grupos.append(atual)
    for n, grupo in enumerate(grupos):
        a = grupo[0]["i"] - ini
        prox = (grupos[n + 1][0]["i"] - ini) if n + 1 < len(grupos) else dur
        b = min(prox, grupo[-1]["f"] - ini + 0.6, dur)  # some na pausa, nao fica "parado"
        txt = censurar(" ".join(p["t"] for p in grupo)).upper().replace("{", "").replace("}", "")
        linhas.append(f"Dialogue: 0,{ass_tempo(max(0, a))},{ass_tempo(max(a + 0.3, b))},Leg,,0,0,0,,{txt}")
    with open(arq, "w") as f:
        f.write(cab + "\n".join(linhas) + "\n")


def cortar(video, arq_momentos, ids, cam=None, jogo=None):
    """cam/jogo = "largura:altura:x:y" (recortes da tela original).
    Com cam e jogo: formato camera em cima + jogo embaixo.
    Sem eles: video inteiro centralizado sobre fundo desfocado."""
    momentos = json.load(open(arq_momentos))
    palavras = json.load(open("transcricao.json")) if os.path.exists("transcricao.json") else []
    os.makedirs("clipes", exist_ok=True)
    for e in momentos:
        if ids and e["id"] not in ids:
            continue
        ass = f"clipes/leg_{e['id']:02d}.ass"
        saida = f"clipes/corte_{e['id']:02d}.mp4"
        if cam and jogo:
            cw, ch = [int(v) for v in cam.split(":")[:2]]
            jw, jh = [int(v) for v in jogo.split(":")[:2]]
            h_cam = round(1080 * ch / cw / 2) * 2
            h_jogo = round(1080 * jh / jw / 2) * 2
            topo = max(200, (1920 - h_cam - h_jogo) // 2)
            divisa = topo + h_cam
            gerar_legenda(palavras, e["inicio"], e["fim"], e.get("titulo", ""), ass,
                          margem_leg=max(40, 1920 - divisa - 60))
            filtro = ("[0:v]split=3[a][b][c];"
                      f"[a]crop={jogo},scale=1080:1920:force_original_aspect_ratio=increase,"
                      "crop=1080:1920,boxblur=30:2,eq=brightness=-0.15[fundo];"
                      f"[b]crop={cam},scale=1080:{h_cam}[cam];"
                      f"[c]crop={jogo},scale=1080:{h_jogo}[jogo];"
                      f"[fundo][cam]overlay=0:{topo}[t1];[t1][jogo]overlay=0:{divisa}[t2];"
                      f"[t2]ass={ass}[v]")
        else:
            gerar_legenda(palavras, e["inicio"], e["fim"], e.get("titulo", ""), ass)
            filtro = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,"
                      "crop=1080:1920,boxblur=25:2[fundo];[b]scale=1080:-2[frente];"
                      f"[fundo][frente]overlay=(W-w)/2:(H-h)/2,ass={ass}[v]")
        r = sh(["ffmpeg", "-y", "-v", "error", "-ss", str(e["inicio"]), "-to", str(e["fim"]),
                "-i", video, "-filter_complex", filtro, "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac",
                "-b:a", "160k", "-movflags", "+faststart", saida])
        print(saida if r.returncode == 0 else f"ERRO no corte {e['id']}: {r.stderr[-300:]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["analisar", "cortar"])
    ap.add_argument("video")
    ap.add_argument("momentos", nargs="?", default="momentos.json")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--dur", type=int, default=30, help="duracao de cada clipe (s)")
    ap.add_argument("--ids", default="")
    ap.add_argument("--cam", help="recorte da camera: largura:altura:x:y")
    ap.add_argument("--jogo", help="recorte do jogo: largura:altura:x:y")
    a = ap.parse_args()
    if a.acao == "analisar":
        analisar(a.video, a.max, a.dur)
    else:
        cortar(a.video, a.momentos, [int(x) for x in a.ids.split(",") if x], a.cam, a.jogo)
