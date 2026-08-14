"""Nexus-Clipper FFmpeg Render Engine"""

import asyncio, shutil, json
from utils.logger import get_logger
log = get_logger("pipeline_ffmpeg")

class FFmpegEngine:
    def __init__(self):
        self.ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        self.ffprobe = shutil.which("ffprobe") or "ffprobe"

    async def probe(self, filepath):
        try:
            cmd = [self.ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(filepath)]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            return {"success": True, "metadata": json.loads(stdout)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_clip(self, input_path, start, duration, output_path):
        cmd = [self.ffmpeg, "-y", "-ss", str(start), "-i", str(input_path), "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", str(output_path)]
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            return {"success": True, "output": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def concat_clips(self, clip_list, output_path):
        list_file = str(Path(output_path).parent / "concat.txt")
        Path(list_file).write_text("\n".join(f"file '{c}'" for c in clip_list))
        cmd = [self.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", str(output_path)]
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            return {"success": True, "output": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def apply_evasion(self, input_path, output_path, params):
        speed = params.get("speed_shift",1.05)
        sat = params.get("saturation",1.15)
        contrast = params.get("contrast",1.1)
        hflip = params.get("hflip",False)
        vf = f"setpts={1/speed}*PTS,eq=saturation={sat}:contrast={contrast}"
        if hflip: vf = f"hflip,{vf}"
        cmd = [self.ffmpeg, "-y", "-i", str(input_path), "-vf", vf, "-af", f"atempo={speed}", "-c:v", "libx264", str(output_path)]
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            return {"success": True, "output": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

ffmpeg_engine = FFmpegEngine()
