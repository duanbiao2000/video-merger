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
        # 设置日志
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # 输入输出路径处理
        self.input_folder = os.path.abspath(input_folder)
        self.output_folder = output_folder or os.path.join(input_folder, "converted")
        os.makedirs(self.output_folder, exist_ok=True)

        # 配置参数
        self.output_format = output_format
        self.supported_formats = ["mp4", "avi", "mkv", "mov", "wmv"]

        # FFmpeg 转换配置
        self.ffmpeg_params = {
            "mp4": [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
            ],
            "avi": [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
            ],
            "mkv": [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
            ],
        }

    def _get_video_files(self) -> List[str]:
        """获取支持的视频文件列表"""
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
        return [
            os.path.join(self.input_folder, f)
            for f in os.listdir(self.input_folder)
            if os.path.splitext(f)[1].lower() in video_extensions
        ]

    def convert_video(self, input_path: str, output_path: str) -> bool:
        """
        使用FFmpeg转换单个视频文件

        参数:
        - input_path: 输入视频路径
        - output_path: 输出视频路径

        返回:
        - 是否成功转换
        """
        try:
            ext = os.path.splitext(output_path)[1][1:]
            params = self.ffmpeg_params.get(ext, self.ffmpeg_params["mp4"])

            command = ["ffmpeg", "-i", input_path] + params + [output_path]

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
        """
        合并所有视频文件

        参数:
        - output_filename: 输出文件名

        返回:
        - 是否成功合并
        """
        try:
            # 获取视频文件列表
            video_files = self._get_video_files()

            if not video_files:
                self.logger.warning("没有找到可处理的视频文件")
                return False

            # 创建临时转换文件列表
            converted_files = []
            for video in video_files:
                output_path = os.path.join(
                    self.output_folder,
                    # 获取视频文件名，去掉扩展名，并添加转换后的文件扩展名
                    f"{os.path.splitext(os.path.basename(video))[0]}_converted.{self.output_format}",
                )
                if self.convert_video(video, output_path):
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
