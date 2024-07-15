#!/usr/bin/env python3
import time
import math
import ffmpeg
import argparse
from faster_whisper import WhisperModel

def extract_audio(input_video):
    input_video_name = input_video.replace(".mp4", "")
    extracted_audio = f"audio-{input_video_name}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio, input_video_name

def transcribe(audio):
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info[0]
    print("Transcription language", info[0])
    segments = list(segments)
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    return language, segments

def format_time(seconds):
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"
    return formatted_time

def generate_subtitle_file(input_video_name, language, segments):
    subtitle_file = f"sub-{input_video_name}.{language}.srt"
    text = ""
    for index, segment in enumerate(segments):
        segment_start = format_time(segment.start)
        segment_end = format_time(segment.end)
        text += f"{str(index+1)} \n"
        text += f"{segment_start} --> {segment_end} \n"
        text += f"{segment.text} \n\n"
    with open(subtitle_file, "w") as f:
        f.write(text)
    return subtitle_file

def add_subtitle_to_video(input_video_name, soft_subtitle, subtitle_file, subtitle_language):
    input_video = f"{input_video_name}.mp4"
    video_input_stream = ffmpeg.input(input_video)
    subtitle_input_stream = ffmpeg.input(subtitle_file)
    output_video = f"output-{input_video_name}.mp4"
    subtitle_track_title = subtitle_file.replace(".srt", "")
    if soft_subtitle:
        stream = ffmpeg.output(video_input_stream, subtitle_input_stream, output_video, **{"c": "copy", "c:s": "mov_text"}, **{"metadata:s:s:0": f"language={subtitle_language}", "metadata:s:s:0": f"title={subtitle_track_title}"})
        ffmpeg.run(stream, overwrite_output=True)
    else:
        stream = ffmpeg.output(video_input_stream, output_video, vf=f"subtitles={subtitle_file}")
        ffmpeg.run(stream, overwrite_output=True)

def run(input_video, timing):
    start_time = time.time()
    print("1. Extracting audio")
    phase_start = time.time()
    extracted_audio, input_video_name = extract_audio(input_video)
    if timing:
        print(f"Phase time: {time.time() - phase_start:.2f}s")
    print("2. Transcribing")
    phase_start = time.time()
    language, segments = transcribe(audio=extracted_audio)
    if timing:
        print(f"Phase time: {time.time() - phase_start:.2f}s")
    print("3. Generating subtitles")
    phase_start = time.time()
    subtitle_file = generate_subtitle_file(input_video_name, language, segments)
    if timing:
        print(f"Phase time: {time.time() - phase_start:.2f}s")
    print("4. Final video")
    phase_start = time.time()
    add_subtitle_to_video(input_video_name, soft_subtitle=True, subtitle_file=subtitle_file, subtitle_language=language)
    if timing:
        print(f"Phase time: {time.time() - phase_start:.2f}s")
    if timing:
        print(f"Total time: {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video files to add subtitles.")
    parser.add_argument("input_file", help="Input video file path.")
    parser.add_argument("-t", "--timing", action="store_true", help="Enable timing information for each phase.")
    args = parser.parse_args()

    run(input_video=args.input_file, timing=args.timing)