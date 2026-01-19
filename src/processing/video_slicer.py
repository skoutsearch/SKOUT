import os
import subprocess
from pathlib import Path


class VideoSlicer:
    def __init__(self, output_dir="data/video_clips/sliced"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def slice_video(
        self,
        source_video: str,
        start_time: float,
        end_time: float,
        output_name: str
    ) -> str:
        """
        Slice a video clip using ffmpeg.

        start_time / end_time are in seconds.
        """
        output_path = Path(self.output_dir) / output_name

        duration = max(0, end_time - start_time)
        if duration <= 0:
            raise ValueError("Invalid clip duration")

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", source_video,
            "-t", str(duration),
            "-c", "copy",
            str(output_path)
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        return str(output_path)
