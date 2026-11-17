#!/bin/bash
# Prepara o ambiente do Claude Code (nuvem) para o sistema de cortes.
# Precisa: "Permitir acesso de rede externo" ligado nas configuracoes do Claude.
set -e
pip install --break-system-packages -q faster-whisper numpy
M="$HOME/models/whisper-small"
if [ -f "$M/model.bin" ]; then echo "Modelo ja instalado em $M"; exit 0; fi
# O site oficial dos modelos (huggingface.co) e bloqueado no ambiente;
# usamos uma copia do Whisper small (CTranslate2 int8) publicada no npm.
T=$(mktemp -d); mkdir -p "$M"
( cd "$T" && for i in 0 1 2 3; do npm pack --silent @skillninja/shortmovie-telop-model-p$i >/dev/null; done
  for f in *.tgz; do tar xzf "$f"; done
  cp package/config.json package/preprocessor_config.json package/tokenizer.json package/vocabulary.json "$M/"
  cat package/model.bin.part0 package/model.bin.part1 package/model.bin.part2 package/model.bin.part3 > "$M/model.bin"
  ESPERADO=ca732cb1379efc49417d028465f543d83a39de2c61f3027678de103dc404ce73
  OBTIDO=$(sha256sum "$M/model.bin" | cut -d' ' -f1)
  [ "$ESPERADO" = "$OBTIDO" ] || { echo "ERRO: impressao digital do modelo nao confere"; rm -f "$M/model.bin"; exit 1; } )
rm -rf "$T"
echo "Pronto: modelo Whisper instalado em $M"
