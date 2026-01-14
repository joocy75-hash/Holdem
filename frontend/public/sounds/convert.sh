#!/bin/bash

# WAV → WebM(Opus) 128kbps 변환 스크립트
# 사용법: ./convert.sh [input.wav] 또는 ./convert.sh (raw 폴더 전체 변환)

RAW_DIR="./raw"
OUTPUT_DIRS=("ui" "actions" "cards" "chips" "notifications" "bgm")

convert_file() {
    local input="$1"
    local output_dir="$2"
    local filename=$(basename "$input" .wav)
    local output="${output_dir}/${filename}.webm"

    if [ ! -f "$input" ]; then
        echo "❌ 파일을 찾을 수 없음: $input"
        return 1
    fi

    echo "🔄 변환 중: $input → $output"
    ffmpeg -i "$input" -c:a libopus -b:a 128k -vn -y "$output" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ 완료: $output"
    else
        echo "❌ 변환 실패: $input"
        return 1
    fi
}

# 단일 파일 변환 (인자로 파일과 출력 디렉토리 지정)
if [ $# -ge 2 ]; then
    convert_file "$1" "$2"
    exit $?
fi

# 단일 파일 변환 (출력 디렉토리 선택)
if [ $# -eq 1 ]; then
    echo "출력 디렉토리를 선택하세요:"
    select dir in "${OUTPUT_DIRS[@]}"; do
        if [ -n "$dir" ]; then
            convert_file "$1" "./$dir"
            exit $?
        fi
    done
fi

# raw 폴더 전체 변환
if [ -d "$RAW_DIR" ]; then
    echo "📁 raw 폴더의 모든 WAV 파일을 변환합니다."
    echo "출력 디렉토리를 선택하세요:"
    select dir in "${OUTPUT_DIRS[@]}"; do
        if [ -n "$dir" ]; then
            for wav in "$RAW_DIR"/*.wav; do
                [ -f "$wav" ] && convert_file "$wav" "./$dir"
            done
            echo "🎉 모든 변환 완료!"
            exit 0
        fi
    done
else
    echo "사용법:"
    echo "  ./convert.sh input.wav output_dir  # 단일 파일 변환"
    echo "  ./convert.sh input.wav             # 단일 파일 (디렉토리 선택)"
    echo "  ./convert.sh                       # raw 폴더 전체 변환"
    echo ""
    echo "출력 디렉토리: ${OUTPUT_DIRS[*]}"
fi
