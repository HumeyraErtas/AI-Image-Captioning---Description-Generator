import os
import io
from datetime import datetime

import requests
import streamlit as st
from PIL import Image

# Eğer istersen .env'den de okuyabilirsin
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")


def call_health():
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None


def upload_and_caption_image(image_file):
    files = {"image": (image_file.name, image_file.getvalue(), image_file.type)}
    resp = requests.post(f"{API_BASE_URL}/api/caption", files=files)

    if resp.status_code != 200:
        st.error(f"API error: {resp.status_code} - {resp.text}")
        return None

    return resp.json()


def fetch_history(limit=20):
    resp = requests.get(f"{API_BASE_URL}/api/history", params={"limit": limit})
    if resp.status_code != 200:
        st.error(f"Tarihçe alınırken hata: {resp.status_code} - {resp.text}")
        return []

    return resp.json().get("items", [])


def main():
    st.set_page_config(
        page_title="AI Image Captioning & Description Generator",
        layout="wide",
        page_icon="🖼️",
    )

    st.title("🖼️ AI Image Captioning & Description Generator")
    st.write("**Computer Vision + NLP** projesi – görselden kısa ve uzun açıklama üretir, confidence skoru hesaplar ve sonuçları SQLite veritabanına kaydeder.")

    # Sidebar
    st.sidebar.header("Navigasyon")
    page = st.sidebar.radio("Sayfa", ["Yeni Görsel Yükle", "Geçmiş Analizler", "Sistem Durumu"])

    # Sistem durumu sayfası
    if page == "Sistem Durumu":
        st.subheader("Sistem Durumu")
        health = call_health()
        if health:
            st.success(f"Backend çalışıyor: {health}")
        else:
            st.error("Backend'e ulaşılamıyor. Flask API'yi başlattığından emin ol.")
        return

    # Yeni görsel yükleme sayfası
    if page == "Yeni Görsel Yükle":
        st.subheader("Yeni Görsel Yükle ve Açıklama Üret")

        uploaded_file = st.file_uploader(
            "Bir görsel seç (JPG veya PNG)",
            type=["jpg", "jpeg", "png"]
        )

        if uploaded_file is not None:
            # Görseli ekranda göster
            image = Image.open(uploaded_file)
            st.image(image, caption="Yüklenen Görsel", use_column_width=True)

            if st.button("🔍 Açıklama Üret"):
                with st.spinner("AI modeli çalışıyor, lütfen bekleyin..."):
                    result = upload_and_caption_image(uploaded_file)

                if result:
                    st.success("Caption başarıyla üretildi!")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 📝 Kısa Açıklama")
                        st.write(result["short_caption"])
                    with col2:
                        st.markdown("### 📄 Uzun Betimleme")
                        st.write(result["long_caption"])

                    st.markdown("### 🎯 Confidence Skoru")
                    st.metric(
                        label="Model Confidence",
                        value=f"{result['confidence']:.1f} %"
                    )

                    st.markdown("### 💾 Kayıt Bilgisi")
                    created_at = result.get("created_at")
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace("Z", ""))
                            st.write(f"Kaydedildi: {dt}")
                        except Exception:
                            st.write(f"Kaydedildi: {created_at}")
                    st.write(f"Görsel dosyası: `{result['image_filename']}`")

        return

    # Geçmiş analizler sayfası
    if page == "Geçmiş Analizler":
        st.subheader("Geçmiş Analizler")

        limit = st.slider("Kaç kayıt görmek istiyorsun?", min_value=5, max_value=50, value=20, step=5)

        with st.spinner("Veritabanından kayıtlar çekiliyor..."):
            items = fetch_history(limit=limit)

        if not items:
            st.info("Henüz hiç kayıt yok. Önce bir görsel yükleyip analiz et.")
            return

        for item in items:
            with st.expander(f"ID #{item['id']}  |  {item['short_caption'][:40]}..."):
                cols = st.columns([1, 2])
                with cols[0]:
                    # Görseli backend'den çek
                    try:
                        img_resp = requests.get(f"{API_BASE_URL}{item['image_url']}", stream=True)
                        if img_resp.status_code == 200:
                            img = Image.open(io.BytesIO(img_resp.content))
                            st.image(img, caption=f"ID #{item['id']}", use_column_width=True)
                        else:
                            st.warning("Görsel alınamadı.")
                    except Exception as e:
                        st.warning(f"Görsel alınırken hata: {e}")

                with cols[1]:
                    st.markdown("**Kısa Açıklama:**")
                    st.write(item["short_caption"])

                    st.markdown("**Uzun Betimleme:**")
                    st.write(item["long_caption"])

                    st.markdown("**Confidence:**")
                    st.metric("Model Confidence", f"{item['confidence']:.1f} %")

                    st.markdown("**Tarih:**")
                    created_at = item.get("created_at")
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace("Z", ""))
                            st.write(dt)
                        except Exception:
                            st.write(created_at)


if __name__ == "__main__":
    main()
