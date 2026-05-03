import os
import sys
import json
import time
import threading
import argparse
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext

try:
    import vosk
except ImportError:
    message = "错误：未安装vosk。请使用当前Python环境安装：pip install vosk"
    raise SystemExit(message)

try:
    import sounddevice as sd
except ImportError:
    message = "错误：未安装sounddevice。请使用当前Python环境安装：pip install sounddevice"
    raise SystemExit(message)

DEFAULT_MODEL_PATH = "/Users/zhuguanyu/Documents/vosk-model-small-cn-0.22"
RATE = 16000
CHUNK = 4000


class TextProcessor:
    """文本后处理：提高准确度和添加智能断句"""
    
    # 常见识别错误的词语替换 - 涵盖发音不标准、口音问题
    ERROR_CORRECTIONS = {
        # 标点符号
        '句号': '。',
        '逗号': '，',
        '停顿': '',
        
        # 语气词和口头禅
        '呃': '',
        '嗯': '',
        '啊': '',
        '哦': '',
        '呀': '',
        '哎': '',
        '哈': '',
        '嘿': '',
        '嗯呐': '',
        
        # 常见发音错误 - 南方口音
        '零': '0',
        '幺': '1',
        
        # 敏感词/谐音词纠正
        '西': '西',
        '死': '死',
    }
    
    # 自定义词典 - 用户可以在这里添加特定的纠正规则
    CUSTOM_CORRECTIONS = {}
    
    # 标点词汇映射
    PUNCTUATION_KEYWORDS = {
        '句号': '。',
        '。': '。',
        '逗号': '，',
        '，': '，',
        '问号': '？',
        '？': '？',
        '感叹号': '！',
        '！': '！',
        '分号': '；',
        '；': '；',
        '冒号': '：',
        '：': '：',
    }
    
    @staticmethod
    def load_custom_corrections(filepath):
        """从文件加载自定义纠正规则"""
        import json
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    TextProcessor.CUSTOM_CORRECTIONS = json.load(f)
                print(f"已加载自定义纠正规则：{filepath}")
        except Exception as e:
            print(f"加载自定义纠正规则失败：{e}")
    
    @staticmethod
    def process(text):
        """处理识别文本：仅消除空格，不添加标点"""
        if not text.strip():
            return text
        
        # 只消除空格，保持原始文本
        text = text.replace(' ', '').replace('\u3000', '')
        
        return text.strip()
    
    @staticmethod
    def process_final_result(text):
        """对最终结果进行完整处理：消除空格、修正错误、智能标点"""
        if not text.strip():
            return text
        
        # 1. 消除所有空格
        text = text.replace(' ', '').replace('\u3000', '')
        
        # 2. 替换常见识别错误词语
        for error_word, correction in TextProcessor.ERROR_CORRECTIONS.items():
            text = text.replace(error_word, correction)
        
        # 3. 应用自定义纠正规则
        for custom_word, correction in TextProcessor.CUSTOM_CORRECTIONS.items():
            text = text.replace(custom_word, correction)
        
        # 4. 处理标点符号关键词
        for keyword, punct in TextProcessor.PUNCTUATION_KEYWORDS.items():
            text = text.replace(keyword, punct)
        
        # 5. 智能词语纠正 - 处理特殊情况
        text = TextProcessor._smart_corrections(text)
        
        # 6. 对整个文本进行一次性的精准标点处理
        text = TextProcessor._add_precise_punctuation(text)
        
        return text.strip()
    
    @staticmethod
    def _smart_corrections(text):
        """应用智能纠正规则处理特殊情况"""
        # 处理"的地得"通用情况
        if '地' in text or '得' in text:
            # 在动词后面的通常是"得"，不动词后面是"的"
            # 这里做简化处理：保留原样或根据上下文修正
            pass
        
        # 处理重复字符
        for i in range(len(text) - 1):
            if text[i] == text[i+1]:
                # 检查是否是有意的重复（如"哈哈"、"呵呵"）
                if text[i] not in ['哈', '呵', '嘻', '呀', '啦', '哎', '嘿']:
                    # 可以选择合并或处理
                    pass
        
        return text
    
    @staticmethod
    def _add_intelligent_punctuation(text):
        """在合适的位置自动添加标点符号进行断句"""
        # 如果文本已包含标点符号，直接返回
        if any(p in text for p in ['。', '，', '！', '？', '；', '：']):
            return text
        
        # 中文常见短语分割点 - 在这些词后自动断句
        split_points = [
            '然后', '接着', '随后', '之后', '总之', '但是', '不过', '然而',
            '所以', '因为', '由于', '而且', '另外', '同样', '相反', '反而',
            '首先', '其次', '再者', '最后', '最终', '因此', '于是', '故而',
            '既然', '以至', '以致', '甚至', '假如', '如果', '除非', '倘若'
        ]
        
        # 查找分割点并添加标点
        for phrase in split_points:
            if phrase in text:
                # 在短语后添加逗号，但避免在句末添加
                parts = text.split(phrase)
                if len(parts) == 2 and parts[1].strip():
                    text = parts[0] + phrase + '，' + parts[1]
        
        # 如果文本长度超过20字，在中间添加标点进行断句
        if len(text) > 20:
            # 尽量在自然停顿处添加逗号
            mid = len(text) // 2
            # 向前查找最近的词边界（这里简化处理）
            for i in range(mid, min(mid + 8, len(text))):
                if i > 5:
                    text = text[:i] + '，' + text[i:]
                    break
        
        return text
    
    @staticmethod
    def _add_precise_punctuation(text):
        """对完整文本进行标点处理 - 简化版，仅在明确的关键词后添加"""
        if not text:
            return text
        
        # 如果已包含句号或感叹号，说明已是完整句子，直接返回
        if '。' in text or '！' in text or '？' in text:
            return text
        
        # 只在以下情况添加句号，其他情况保留原文本
        
        # 1. 文本以句尾词结尾时添加句号
        sentence_endings = ['了', '吗', '呢', '吧', '啦']
        for ending in sentence_endings:
            if text.endswith(ending):
                return text + '。'
        
        # 2. 如果没有任何句尾词，长文本在明确的连接词处添加逗号
        sentence_splitters = [
            '然后', '接着', '随后', '之后', '但是', '不过', '然而',
            '所以', '因为', '由于', '而且', '另外'
        ]
        
        for splitter in sentence_splitters:
            if splitter in text:
                # 只在这个词第一次出现时添加逗号
                idx = text.find(splitter)
                if idx > 0:
                    # 在这个词前添加逗号，后继续处理
                    before = text[:idx]
                    after = text[idx:]
                    return before.rstrip() + '，' + after + '。'
        
        # 3. 默认：没有明确标记时，长文本在中间添加逗号
        if len(text) > 12:
            # 在文本中点附近添加一个逗号
            mid = len(text) // 2
            # 找到最近的字符位置
            for i in range(max(4, mid - 2), min(mid + 3, len(text))):
                return text[:i] + '，' + text[i:] + '。'
        
        # 4. 短文本直接添加句号
        if text and not text.endswith(('。', '！', '？', '，')):
            return text + '。'
        
        return text


class SpeechRecognizer:
    """语音识别核心类，供CLI和GUI模式共用"""
    def __init__(self, model_path, rate=RATE, chunk=CHUNK):
        self.model_path = model_path
        self.rate = rate
        self.chunk = chunk
        self.model = None
        self.rec = None
        self.running = False
        self.thread = None
        self.on_result = None
        self.on_partial = None
        self.on_error = None
        self.on_stopped = None

    def check_model_path(self):
        if not os.path.isdir(self.model_path):
            raise FileNotFoundError(f"Vosk模型目录不存在：{self.model_path}")

    def start(self):
        if self.running:
            return
        self.check_model_path()
        self.model = vosk.Model(self.model_path)
        self.rec = vosk.KaldiRecognizer(self.model, self.rate)
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _run_loop(self):
        last_voice_time = time.time()
        try:
            with sd.RawInputStream(samplerate=self.rate, channels=1, dtype="int16", blocksize=self.chunk) as stream:
                while self.running:
                    data, _ = stream.read(self.chunk)
                    if isinstance(data, (bytes, bytearray)):
                        audio_bytes = bytes(data)
                    else:
                        audio_bytes = memoryview(data).tobytes()

                    if self.rec.AcceptWaveform(audio_bytes):
                        result = json.loads(self.rec.Result())
                        text = result.get("text", "")
                        if text.strip():
                            last_voice_time = time.time()
                            # 处理识别文本：提高准确度和添加标点
                            processed_text = TextProcessor.process(text)
                            if self.on_result:
                                self.on_result(processed_text)
                    else:
                        partial = json.loads(self.rec.PartialResult())
                        partial_text = partial.get("partial", "")
                        if partial_text.strip():
                            last_voice_time = time.time()
                        # 处理部分识别结果
                        processed_partial = TextProcessor.process(partial_text)
                        if self.on_partial:
                            self.on_partial(processed_partial)

                    if not self.running:
                        break

                    if time.time() - last_voice_time >= 10:
                        break
        except Exception as error:
            if self.on_error:
                self.on_error(str(error))
        finally:
            self.running = False
            if self.on_stopped:
                self.on_stopped()


# 用于维护
class CLIMode:
    """命令行模式"""
    def __init__(self, model_path):
        self.model_path = model_path
        self.recognizer = None

    def check_model_path(self):
        if not os.path.isdir(self.model_path):
            print(f"错误：Vosk模型目录不存在：{self.model_path}")
            print("请先下载并解压模型到该目录，或修改模型路径。")
            sys.exit(1)

    def run(self):
        """运行CLI模式"""
        self.check_model_path()
        self.recognizer = SpeechRecognizer(self.model_path)
        self.recognizer.on_result = self._on_result
        self.recognizer.on_partial = self._on_partial
        self.recognizer.on_error = self._on_error
        self.recognizer.on_stopped = self._on_stopped

        print("当前Python：", sys.executable)
        print("请说话... (按Ctrl+C停止)")

        try:
            self.recognizer.start()
            while self.recognizer.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n停止录音")
        except Exception as e:
            print("错误：", e)
        finally:
            self.recognizer.stop()

    def _on_result(self, text):
        print("最终结果:", text)

    def _on_partial(self, text):
        print("部分结果:", text, end="\r")

    def _on_error(self, message):
        print(f"识别错误：{message}")

    def _on_stopped(self):
        print("\n语音识别已停止")


# ============= GUI 模式 =============
class SpeechToTextApp:
    """GUI模式"""
    def __init__(self, root, model_path):
        self.root = root
        self.root.title("实时语音转文字")
        self.root.geometry("640x480")
        self.recognizer = None
        self.model_path = model_path

        self.model_path_var = tk.StringVar(value=self.model_path)
        self.status_var = tk.StringVar(value="准备就绪")
        self.partial_var = tk.StringVar(value="")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=12, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Vosk 模型路径：").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(frame, textvariable=self.model_path_var, width=60).grid(row=0, column=1, sticky=tk.W)
        tk.Button(frame, text="打开模型目录", command=self._open_model_folder).grid(row=0, column=2, padx=(8, 0))

        self.start_button = tk.Button(frame, text="开始识别", width=12, command=self._start_recognition)
        self.start_button.grid(row=1, column=0, pady=12, sticky=tk.W)

        self.stop_button = tk.Button(frame, text="停止识别", width=12, command=self._stop_recognition, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=1, pady=12, sticky=tk.W)

        tk.Label(frame, textvariable=self.status_var, fg="blue").grid(row=1, column=2, sticky=tk.W, padx=(12, 0))

        tk.Label(frame, text="部分识别结果：").grid(row=2, column=0, columnspan=3, sticky=tk.W)
        tk.Label(frame, textvariable=self.partial_var, fg="darkgreen").grid(row=3, column=0, columnspan=3, sticky=tk.W)

        tk.Label(frame, text="识别文本：").grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(12, 0))
        self.text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=78, height=18)
        self.text_widget.grid(row=5, column=0, columnspan=3, sticky=tk.NSEW)
        self.text_widget.configure(state=tk.DISABLED)

        frame.grid_rowconfigure(5, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def _open_model_folder(self):
        path = self.model_path_var.get().strip()
        if os.path.isdir(path):
            os.system(f'open "{path}"')
        else:
            messagebox.showwarning("路径错误", "当前模型目录不存在，请检查路径。")

    def _start_recognition(self):
        path = self.model_path_var.get().strip()
        if not path:
            messagebox.showwarning("路径错误", "请先输入模型目录路径。")
            return

        self.recognizer = SpeechRecognizer(path)
        self.recognizer.on_result = self._on_result
        self.recognizer.on_partial = self._on_partial
        self.recognizer.on_error = self._on_error
        self.recognizer.on_stopped = self._on_stopped

        try:
            self.recognizer.start()
        except FileNotFoundError as error:
            messagebox.showerror("模型加载失败", str(error))
            return
        except Exception as error:
            messagebox.showerror("启动失败", str(error))
            return

        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set("正在识别，请说话...")
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        self.partial_var.set("")

    def _stop_recognition(self):
        if self.recognizer:
            self.recognizer.stop()
        self._set_idle_state()

    def _on_result(self, text):
        self.root.after(0, lambda: self._append_text(text))

    def _on_partial(self, text):
        self.root.after(0, lambda: self.partial_var.set(text))

    def _on_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("识别错误", message))

    def _on_stopped(self):
        self.root.after(0, self._set_idle_state)

    def _append_text(self, text):
        self.text_widget.configure(state=tk.NORMAL)
        # 对最终结果进行强力处理：消除空格并智能断句
        processed_text = TextProcessor.process_final_result(text)
        self.text_widget.insert(tk.END, processed_text + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        self.partial_var.set("")
        self.status_var.set("识别中，等待新语音...")

    def _set_idle_state(self):
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("已停止")

    def _on_close(self):
        if self.recognizer and self.recognizer.running:
            self.recognizer.stop()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="实时语音转文字（支持CLI和GUI模式）")
    parser.add_argument("--cli", action="store_true", help="使用CLI模式（默认为GUI模式）")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help=f"Vosk模型路径（默认：{DEFAULT_MODEL_PATH}）")
    parser.add_argument("--corrections", type=str, help="自定义纠正规则文件（JSON格式）")
    
    args = parser.parse_args()
    
    # 加载自定义纠正规则
    if args.corrections:
        TextProcessor.load_custom_corrections(args.corrections)
    else:
        # 尝试加载默认的自定义纠正文件
        default_corrections_file = os.path.join(os.path.dirname(__file__), "corrections.json")
        TextProcessor.load_custom_corrections(default_corrections_file)

    if args.cli:
        # CLI模式
        cli = CLIMode(args.model)
        cli.run()
    else:
        # GUI模式（默认）
        root = tk.Tk()
        app = SpeechToTextApp(root, args.model)
        root.mainloop()


if __name__ == "__main__":
    main()
