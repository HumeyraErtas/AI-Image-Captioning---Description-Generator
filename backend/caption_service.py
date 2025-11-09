import io
from typing import Tuple
from PIL import Image
import torch
import torch.nn.functional as F
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer


MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Modeli ve tokenizer'ı GLOBAL yükleyip yeniden kullanıyoruz (performans için).
print("Loading model... This may take a while the first time.")
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME).to(DEVICE)
processor = ViTImageProcessor.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Default inference ayarları
GEN_KWARGS_SHORT = {
    "max_length": 16,
    "num_beams": 4,
}
GEN_KWARGS_LONG = {
    "max_length": 64,
    "num_beams": 4,
}


def _load_image(image_bytes: bytes) -> Image.Image:
    """Bytes'tan PIL Image üretir."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return image


def _generate_with_scores(image: Image.Image, gen_kwargs: dict):
    """Token skorlarını da alarak caption üretir."""
    pixel_values = processor(images=[image], return_tensors="pt").pixel_values.to(DEVICE)

    outputs = model.generate(
        pixel_values,
        output_scores=True,
        return_dict_in_generate=True,
        **gen_kwargs,
    )

    sequences = outputs.sequences[0]        # (seq_len,)
    scores = outputs.scores                 # her adım için logits listesi

    # Text decode
    text = tokenizer.decode(sequences, skip_special_tokens=True).strip()

    # Confidence hesaplama (heuristic):
    # Her adımdaki seçilen token'ın olasılığını al, ortalamasını al.
    probs = []
    # İlk score, ilk üretilen token içindir; o yüzden seq[1:] ile eşliyoruz.
    for step, logits in enumerate(scores):
        token_id = sequences[step + 1]  # 0. token genelde BOS/başlangıç gibi
        log_probs = F.log_softmax(logits[0], dim=-1)
        prob = torch.exp(log_probs[token_id]).item()
        probs.append(prob)

    if probs:
        avg_prob = sum(probs) / len(probs)
        confidence = float(avg_prob * 100.0)  # 0-100 aralığına çek
    else:
        confidence = 0.0

    # Güven skorunu 10-99 aralığına sıkıştır (çok uç durumları kırpmak için)
    confidence = max(10.0, min(99.0, confidence))

    return text, confidence


def generate_captions(image_bytes: bytes) -> Tuple[str, str, float]:
    """
    Kısa caption, uzun açıklama ve confidence score döndürür.
    """
    image = _load_image(image_bytes)

    # Kısa açıklama
    short_caption, confidence = _generate_with_scores(image, GEN_KWARGS_SHORT)

    # Uzun açıklama için max_length'i artırıp tekrar üretiyoruz.
    long_caption, _ = _generate_with_scores(image, GEN_KWARGS_LONG)

    return short_caption, long_caption, confidence
