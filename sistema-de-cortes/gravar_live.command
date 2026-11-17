#!/bin/bash
# =============================================================
#  GRAVADOR AUTOMÁTICO DE LIVES (MacBook Air / macOS 12)
#  - Grava a tela + o som do BlackHole 2ch
#  - Salva em blocos de 20 minutos, em 720p (arquivos leves)
#  - Usa o chip de vídeo do Mac (não trava o processador)
#  - Impede o Mac de dormir enquanto grava
#  PARAR: clique nesta janela e aperte  Control + C
# =============================================================

MINUTOS_POR_BLOCO=20
PASTA="$HOME/Movies/Lives"
QUALIDADE_VIDEO="2500k"     # 720p a 2,5 Mbps ≈ 390 MB por bloco de 20 min
AUDIO="BlackHole 2ch"

# ---------- encontrar o ffmpeg ----------
FFMPEG=""
for c in "$(command -v ffmpeg)" "$HOME/ffmpeg" "$HOME/Downloads/ffmpeg" "/usr/local/bin/ffmpeg"; do
  if [ -n "$c" ] && [ -x "$c" ]; then FFMPEG="$c"; break; fi
done
if [ -z "$FFMPEG" ]; then
  echo ""
  echo "❌ Não encontrei o programa 'ffmpeg'."
  echo "   Coloque o arquivo 'ffmpeg' na sua pasta Downloads e rode de novo."
  echo ""
  read -n 1 -s -r -p "Aperte qualquer tecla para fechar..."
  exit 1
fi

# ---------- encontrar a tela ----------
LISTA="$("$FFMPEG" -hide_banner -f avfoundation -list_devices true -i "" 2>&1)"
TELA="$(echo "$LISTA" | grep -o 'Capture screen [0-9]*' | head -1)"
if [ -z "$TELA" ]; then
  echo "❌ Não encontrei a tela para gravar."
  echo "   Libere o Terminal em: Preferências do Sistema → Segurança e Privacidade"
  echo "   → Privacidade → Gravação de Tela  (marque 'Terminal') e rode de novo."
  read -n 1 -s -r -p "Aperte qualquer tecla para fechar..."
  exit 1
fi
if ! echo "$LISTA" | grep -q "$AUDIO"; then
  echo "❌ Não encontrei o '$AUDIO'. Confira se o BlackHole está instalado."
  read -n 1 -s -r -p "Aperte qualquer tecla para fechar..."
  exit 1
fi

# ---------- escolher o compressor (chip de vídeo, se existir) ----------
if "$FFMPEG" -hide_banner -encoders 2>/dev/null | grep -q h264_videotoolbox; then
  CODEC=(-c:v h264_videotoolbox -b:v "$QUALIDADE_VIDEO" -maxrate 3500k -bufsize 7000k)
else
  echo "ℹ️  Chip de vídeo indisponível; usando o processador (pode esquentar)."
  CODEC=(-c:v libx264 -preset ultrafast -b:v "$QUALIDADE_VIDEO" -maxrate 3500k -bufsize 7000k)
fi

mkdir -p "$PASTA"
echo ""
echo "🎥 GRAVANDO!"
echo "   Tela:   $TELA"
echo "   Som:    $AUDIO"
echo "   Blocos: a cada $MINUTOS_POR_BLOCO minutos"
echo "   Pasta:  $PASTA"
echo ""
echo "   ⚠️  Lembre: Saída de som = 'Dispositivo de Saída Múltipla'"
echo "   ⏹  Para PARAR: aperte  Control + C  nesta janela."
echo ""

# caffeinate = não deixa o Mac dormir enquanto o ffmpeg roda
caffeinate -dims "$FFMPEG" -hide_banner -loglevel warning -stats \
  -f avfoundation -pixel_format uyvy422 -capture_cursor 0 -framerate 30 -i "$TELA:$AUDIO" \
  -vf "scale=-2:720,fps=30" \
  "${CODEC[@]}" \
  -force_key_frames "expr:gte(t,n_forced*2)" \
  -c:a aac -b:a 128k -ar 48000 \
  -f segment -segment_time $((MINUTOS_POR_BLOCO * 60)) -reset_timestamps 1 \
  -segment_format mp4 -segment_format_options movflags=+frag_keyframe+empty_moov+default_base_moof \
  -strftime 1 "$PASTA/live_%Y-%m-%d_%Hh%Mm%Ss.mp4"

echo ""
echo "✅ Gravação encerrada. Os blocos estão em: $PASTA"
open "$PASTA"
read -n 1 -s -r -p "Aperte qualquer tecla para fechar..."
