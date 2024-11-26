import os
import sys
import subprocess
import logging
from typing import List


class VideoProcessor:

    def __init__(
        self,
        input_folder: str,
        output_folder: str = None,
        output_format: str = "mp4",
        log_level: str = "INFO",
    ):
        """
        视频处理器初始化

        参数:
        - input_folder: 输入视频文件夹路径
        - output_folder: 输出文件夹路径，默认为输入文件夹下的 'converted'
        - output_format: 目标输出视频格式，默认为 'mp4'
        - log_level: 日志级别，默认为 'INFO'
        """

        # 输入输出路径处理
        self.input_folder = os.path.abspath(input_folder)
        self.output_folder = output_folder or os.path.join(input_folder, "converted")
        os.makedirs(self.output_folder, exist_ok=True)

        # 配置参数
        self.output_format = output_format
        self.supported_formats = ["mp4", "avi", "mkv", "mov", "wmv"]

        # 设置日志

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def _get_video_files(self) -> List[str]:
        """获取支持的视频文件列表"""
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
        return [
            os.path.join(self.input_folder, f)
            for f in os.listdir(self.input_folder)
            if os.path.splitext(f)[1].lower() in video_extensions
        ]

    def convert_video(
        self, input_path: str, output_path: str, target_fps: int = 30
    ) -> bool:
        """
        使用FFmpeg转换单个视频文件，并统一帧率

        参数:
        - input_path: 输入视频路径
        - output_path: 输出视频路径
        - target_fps: 目标帧率，默认30fps

        返回:
        - 是否成功转换
        """
        try:
            # 首先获取输入视频的信息
            probe_command = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                input_path,
            ]

            probe_result = subprocess.run(probe_command, capture_output=True)
            if probe_result.returncode != 0:
                self.logger.error(f"无法获取视频信息: {input_path}")
                return False

            # 添加帧率控制参数
            command = [
                "ffmpeg",
                "-i",
                input_path,
                "-vsync",
                "1",  # 帮助保持视频同步
                "-r",
                str(target_fps),  # 设置输出帧率
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-ar",
                "44100",  # 统一音频采样率
                "-b:a",
                "192k",  # 统一音频比特率
                "-max_muxing_queue_size",
                "1024",  # 增加复用队列大小
                output_path,
            ]

            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"成功转换: {input_path}")
                return True
            else:
                self.logger.error(f"转换失败: {input_path}")
                self.logger.error(result.stderr)
                return False

        except Exception as e:
            self.logger.error(f"转换过程异常: {e}")
            return False

    def merge_videos(self, output_filename: str = "merged_video.mp4") -> bool:
        try:
            video_files = self._get_video_files()

            if not video_files:
                self.logger.warning("没有找到可处理的视频文件")
                return False

            # 创建临时转换文件列表
            converted_files = []
            for video in video_files:
                output_path = os.path.join(
                    self.output_folder,
                    f"{os.path.splitext(os.path.basename(video))[0]}_converted.{self.output_format}",
                )
                if self.convert_video(
                    video, output_path, target_fps=30
                ):  # 统一使用30fps
                    converted_files.append(output_path)

            # 创建文件列表文本
            list_file_path = os.path.join(self.output_folder, "video_list.txt")
            with open(list_file_path, "w", encoding="utf-8") as f:
                for file in converted_files:
                    f.write(f"file '{file}'\n")

            # 最终合并
            merged_path = os.path.join(self.output_folder, output_filename)
            merge_command = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file_path,
                "-c",
                "copy",
                "-vsync",
                "2",  # 添加视频同步参数
                merged_path,
            ]

            result = subprocess.run(merge_command, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"成功合并视频: {merged_path}")
                return True
            else:
                self.logger.error("视频合并失败")
                self.logger.error(result.stderr)
                return False

        except Exception as e:
            self.logger.error(f"合并过程异常: {e}")
            return False


def main():
    if len(sys.argv) < 2:
        print("使用方法: python video_merger.py <输入文件夹路径>")
        sys.exit(1)

    input_folder = sys.argv[1]
    processor = VideoProcessor(input_folder)
    processor.merge_videos()


if __name__ == "__main__":
    main()
