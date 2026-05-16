import whisper
import argparse
import re
import os
import subprocess

def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms > 999:
        ms = 999
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def prepare_audio(input_audio):
    temp_audio = "temp_ready_audio.wav"
    print("Optimizing audio with FFmpeg...")
    cmd = [
        'ffmpeg', '-y', '-i', input_audio,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        temp_audio
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")
    return temp_audio

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return float(result.stdout.decode().strip())

def load_and_clean_text(file_path: str) -> list:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="cp1250") as f:
            text = f.read()

    text = text.replace('„', '').replace('"', '').replace('"', '').replace('—', ' ')
    text = re.sub(r"\s+", " ", text).strip()
    return text.split()

def extract_word_timestamps(segments: list) -> list:
    words_data = []
    for seg in segments:
        for w in seg.get("words", []):
            word = w["word"].strip()
            if word:
                words_data.append({
                    "start": w["start"],
                    "end": w["end"],
                    "word": word
                })

    # Extend each word's end to the start of the next word
    # This prevents gaps where no subtitle is shown
    for i in range(len(words_data) - 1):
        words_data[i]["end"] = words_data[i + 1]["start"]

    return words_data

def build_word_blocks(whisper_words: list, original_words: list, audio_duration: float) -> list:
    blocks = []
    count = min(len(whisper_words), len(original_words))

    for i in range(count):
        blocks.append({
            "start": whisper_words[i]["start"],
            "end": whisper_words[i]["end"],
            "text": original_words[i]
        })

    # If original has more words than Whisper detected
    if len(original_words) > len(whisper_words) and blocks:
        last = blocks[-1]
        avg_duration = (last["end"] - blocks[0]["start"]) / len(blocks)
        for i in range(len(whisper_words), len(original_words)):
            start = last["end"]
            end = start + avg_duration
            blocks.append({
                "start": start,
                "end": end,
                "text": original_words[i]
            })
            last = blocks[-1]

    # Last word ends exactly when audio ends
    if blocks:
        blocks[-1]["end"] = audio_duration

    return blocks

def create_srt_file(blocks: list, output_name: str):
    lines = []
    for i, block in enumerate(blocks, start=1):
        lines.append(str(i))
        lines.append(f"{format_timestamp(block['start'])} --> {format_timestamp(block['end'])}")
        lines.append(block["text"])
        lines.append("")
    with open(output_name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Word-by-word SRT generator synced to narrator")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--model", default="small")
    args = parser.parse_args()

    output_srt = os.path.splitext(args.audio)[0] + ".srt"

    print("Loading transcript...")
    original_words = load_and_clean_text(args.text)
    print(f"Loaded {len(original_words)} words.")

    optimized_audio = prepare_audio(args.audio)

    print(f"Loading Whisper model: {args.model}...")
    model = whisper.load_model(args.model)

    print("Analyzing audio...")
    result = model.transcribe(
        optimized_audio,
        word_timestamps=True,
        condition_on_previous_text=False
    )

    whisper_words = extract_word_timestamps(result.get("segments", []))
    print(f"Whisper detected {len(whisper_words)} words.")
    print(f"Original text has {len(original_words)} words.")

    if not whisper_words:
        raise RuntimeError("Whisper detected no words. Check your audio file.")

    audio_duration = get_audio_duration(args.audio)
    print(f"Audio duration: {audio_duration:.2f}s")

    blocks = build_word_blocks(whisper_words, original_words, audio_duration)
    create_srt_file(blocks, output_srt)

    if os.path.exists(optimized_audio):
        os.remove(optimized_audio)

    print(f"Success! SRT created: {output_srt}")

if __name__ == "__main__":
    main()