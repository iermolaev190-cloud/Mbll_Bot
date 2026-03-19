API_KEYS = {
    "openrouter": "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",
    "gemini": "AIzaSyCFfh3i2YZX96XsTfY1f9ZRzgGK65Ribss",
}

MODEL_CONFIG = {
    "openrouter": {
        "primary": "liquid/lfm-2-24b-a2b",
        "secondary": "google/gemini-3.1-flash-lite-preview",
        "fast": "bytedance-seed/seed-2.0-lite",
        "creative": "qwen/qwen3.5-9b",

        "free_fallback": [
            "liquid/lfm-2-24b-a2b",
            "bytedance-seed/seed-2.0-lite",
            "google/gemini-3.1-flash-lite-preview",
            "qwen/qwen3.5-flash-02-23",
            "inception/mercury-2",
            "bytedance-seed/seed-2.0-mini",
            "qwen/qwen3.5-9b",
        ],

        "prices": {
            "liquid/lfm-2-24b-a2b": 0.03,
            "bytedance-seed/seed-2.0-lite": 0.25,
            "google/gemini-3.1-flash-lite-preview": 0.25,
            "qwen/qwen3.5-flash-02-23": 0.10,
        }
    },

    "gemini": {
        "primary": "gemini-3.1-flash-lite-preview",
    }
}