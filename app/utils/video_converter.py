import subprocess
import os
import cv2

class VideoConverter:
    @staticmethod
    def convert_video_to_h264(input_video):
        """
        Converte um vídeo para o codec H.264 usando ffmpeg, sobrescrevendo o arquivo original.
        """
        try:
            temp_output = input_video + ".tmp.mp4"
            command = [
                "ffmpeg",
                "-i", input_video,
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",
                "-crf", "23",
                temp_output
            ]
            subprocess.run(command, check=True)
            os.replace(temp_output, input_video)
            print("✅ Vídeo convertido com sucesso para H.264.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao converter vídeo para H.264: {e}")
            return False
        
    @staticmethod
    def ensure_max_fps(input_video, max_fps=30):
        """
        Verifica o FPS do vídeo e, se for maior que max_fps, converte para max_fps.
        """
        try:
            cap = cv2.VideoCapture(input_video)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

            if fps <= 0:
                print("⚠️ Não foi possível obter o FPS do vídeo.")
                return False

            print(f"🎞️ FPS atual: {fps}")

            if fps > max_fps:
                print(f"⏬ FPS acima de {max_fps}, convertendo...")
                temp_output = input_video + ".fps_tmp.mp4"
                command = [
                    "ffmpeg",
                    "-i", input_video,
                    "-filter:v", f"fps=fps={max_fps}",
                    "-c:a", "copy",
                    temp_output
                ]
                subprocess.run(command, check=True)
                os.replace(temp_output, input_video)
                print("✅ FPS ajustado com sucesso.")
                return True
            else:
                print("✅ FPS está dentro do limite.")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar/ajustar FPS: {e}")
            return False
        
        