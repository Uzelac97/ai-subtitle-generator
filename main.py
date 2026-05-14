import whisper
import argparse
import re
import os
import subprocess

def load_and_clean_text(file_path: str) -> list:
    """Loads text from a file and removes special characters for better matching."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Remove special quotes and dashes that might confuse the Whisper model
    text = text.replace('„', '').replace('“', '').replace('"', '').replace('—', ' ')
    text = re.sub(r"\s+", " ", text).strip()
    return text.split()

def format_timestamp(seconds: float) -> str:
    """Converts seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms > 999: ms = 999
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def prepare_audio(input_audio):
    """Uses FFmpeg to convert audio to 16kHz mono WAV for maximum timing precision."""
    temp_audio = "temp_ready_audio.wav"
    print("🛠 Optimizing audio with FFmpeg...")
    cmd = [
        'ffmpeg', '-y', '-i', input_audio,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        temp_audio
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return temp_audio

def extract_word_timestamps(segments: list) -> list:
    """Extracts word-level timestamps and fills gaps to prevent flickering."""
    words_data = []
    for seg in segments:
        words = seg.get("words", [])
        if words:
            for w in words:
                clean_word = re.sub(r'[^\w\s]', '', w["word"].strip())
                if clean_word:
                    words_data.append({
                        "start": w["start"],
                        "end": w["end"],
                        "word": clean_word
                    })
    
    # Smooth out timestamps to ensure subtitles don't flicker between words
    for i in range(len(words_data) - 1):
        if words_data[i+1]["start"] - words_data[i]["end"] < 0.15:
            words_data[i]["end"] = words_data[i+1]["start"]
    return words_data

def align_text_with_timestamps(whisper_words: list, original_text: list) -> list:
    """Maps the original script words onto the Whisper-detected timestamps."""
    count = min(len(whisper_words), len(original_text))
    aligned_blocks = []
    for i in range(count):
        aligned_blocks.append({
            "start": whisper_words[i]["start"],
            "end": whisper_words[i]["end"],
            "text": original_text[i]
        })
    return aligned_blocks

def create_srt_file(blocks: list, output_name: str):
    """Generates the final SRT file."""
    lines = []
    for i, block in enumerate(blocks, start=1):
        lines.append(str(i))
        lines.append(f"{format_timestamp(block['start'])} --> {format_timestamp(block['end'])}")
        lines.append(block["text"])
        lines.append("")
    with open(output_name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Audio + Text to Word-Level SRT Generator")
    parser.add_argument("--audio", required=True, help="Path to the input audio file")
    parser.add_argument("--text", required=True, help="Path to the transcript text file")
    parser.add_argument("--model", default="small", help="Whisper model size (tiny, base, small, medium, large)")
    args = parser.parse_args()

    output_srt = os.path.splitext(args.audio)[0] + ".srt"
    script_text = load_and_clean_text(args.text)
    
    optimized_audio = prepare_audio(args.audio)
    
    print(f"🔄 Loading Whisper model: {args.model}...")
    model = whisper.load_model(args.model)

    print("🎵 Analyzing audio and synchronizing text...")
    result = model.transcribe(
        optimized_audio, 
        word_timestamps=True,
        condition_on_previous_text=False
    )

    whisper_words = extract_word_timestamps(result.get("segments", []))
    final_blocks = align_text_with_timestamps(whisper_words, script_text)

    create_srt_file(final_blocks, output_srt)
    
    if os.path.exists(optimized_audio):
        os.remove(optimized_audio)

    print(f"✅ Success! SRT created: {output_srt}")

if __name__ == "__main__":
    main()