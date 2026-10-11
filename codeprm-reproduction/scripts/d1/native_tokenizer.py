"""使用本机llama.cpp同版本头文件对应的DLL，只加载GGUF词表，不加载权重。

当前ABI核验基于本机build 631109b34。其他构建必须重新核验，不能静默沿用。
"""
from __future__ import annotations

import ctypes as C
import hashlib
import os
import subprocess
from pathlib import Path


class ModelParams(C.Structure):
    _fields_ = [
        ("devices", C.c_void_p), ("tensor_buft_overrides", C.c_void_p),
        ("n_gpu_layers", C.c_int32), ("split_mode", C.c_int), ("load_mode", C.c_int),
        ("lazy_mode", C.c_int), ("main_gpu", C.c_int32), ("tensor_split", C.c_void_p),
        ("progress_callback", C.c_void_p), ("progress_callback_user_data", C.c_void_p),
        ("kv_overrides", C.c_void_p), ("vocab_only", C.c_bool), ("check_tensors", C.c_bool),
        ("use_extra_bufts", C.c_bool), ("no_host", C.c_bool), ("no_alloc", C.c_bool), ("load_mtp", C.c_bool),
    ]


class NativeTokenizer:
    def __init__(self, model_path, library_directory, *, expected_commit="631109b34"):
        self.model_path = Path(model_path).resolve()
        self.library_directory = Path(library_directory).resolve()
        build = subprocess.run([str(self.library_directory / "llama-server.exe"), "--version"],
                               capture_output=True, text=True, timeout=10)
        self.build_string = build.stdout + build.stderr
        if expected_commit not in self.build_string or C.sizeof(ModelParams) != 80:
            raise RuntimeError("原生DLL构建/ABI未核验，拒绝加载")
        self._dll_path = os.add_dll_directory(str(self.library_directory))
        self.lib = C.CDLL(str(self.library_directory / "libllama.dll"))
        self.messages = []
        def logger(level, text, userdata):
            self.messages.append(text.decode("utf-8", errors="replace"))
            self.messages = self.messages[-16:]
        self._logger = C.CFUNCTYPE(None, C.c_int, C.c_char_p, C.c_void_p)(logger)
        self.lib.llama_log_set.argtypes = [C.c_void_p, C.c_void_p]
        self.lib.llama_log_set(self._logger, None)
        self.lib.llama_model_default_params.restype = ModelParams
        self.lib.llama_model_load_from_file.argtypes = [C.c_char_p, ModelParams]
        self.lib.llama_model_load_from_file.restype = C.c_void_p
        self.lib.llama_model_get_vocab.argtypes = [C.c_void_p]
        self.lib.llama_model_get_vocab.restype = C.c_void_p
        self.lib.llama_model_free.argtypes = [C.c_void_p]
        self.lib.llama_tokenize.argtypes = [C.c_void_p, C.c_char_p, C.c_int32,
                                           C.POINTER(C.c_int32), C.c_int32, C.c_bool, C.c_bool]
        self.lib.llama_tokenize.restype = C.c_int32
        params = self.lib.llama_model_default_params()
        params.vocab_only, params.n_gpu_layers = True, 0
        self.model = self.lib.llama_model_load_from_file(str(self.model_path).encode("utf-8"), params)
        if not self.model:
            raise RuntimeError("词表加载失败：" + "".join(self.messages)[-1000:])
        self.vocab = self.lib.llama_model_get_vocab(self.model)
        if not self.vocab:
            self.close()
            raise RuntimeError("模型词表为空")

    def tokens(self, text):
        data = text.encode("utf-8")
        capacity = len(data) + 16
        output = (C.c_int32 * capacity)()
        count = self.lib.llama_tokenize(self.vocab, data, len(data), output, capacity, True, True)
        if count < 0:
            raise RuntimeError("token输出空间不足，拒绝返回不完整计量")
        return list(output[:count])

    def count(self, text):
        return len(self.tokens(text))

    def identity(self):
        return {"build": self.build_string.strip(), "vocab_only": True,
                "model_path": str(self.model_path), "model_file_bytes": self.model_path.stat().st_size,
                "dll_sha256": hashlib.sha256((self.library_directory / "libllama.dll").read_bytes()).hexdigest(),
                "model_hash_status": "blob名称记录上游digest，本次未重算4.6GB文件哈希"}

    def close(self):
        if getattr(self, "model", None):
            self.lib.llama_model_free(self.model)
            self.model = None
        # The DLL log callback is global. Reset it before this Python callback
        # can be garbage-collected, including when another tokenizer is loaded.
        if getattr(self, "lib", None):
            self.lib.llama_log_set(None, None)
        if getattr(self, "_dll_path", None):
            self._dll_path.close()
            self._dll_path = None


def render_chatml(prompt, system="You are Qwen, created by Alibaba Cloud. You are a helpful assistant."):
    return "<|im_start|>system\n" + system + "<|im_end|>\n<|im_start|>user\n" + prompt + "<|im_end|>\n<|im_start|>assistant\n"
