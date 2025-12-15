import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import io
from phos.config import get_preset, PRESETS
from phos.core import FilmRenderer, standardize
from phos.utils import load_raw_image

# 设置页面配置 
st.set_page_config(
    page_title="Phos_refactor (v1.0.0)",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def process_image(uploaded_file, preset_name, iso, tone_style, exposure_ev, halation_intensity):
    start_time = time.time()
    
    # Determine file type
    filename = uploaded_file.name.lower()
    is_raw = any(filename.endswith(ext) for ext in ['.arw', '.cr2', '.nef', '.dng'])
    
    if is_raw:
        with st.spinner('正在显影 RAW 底片...'):
            # Load Raw (Returns RGB)
            # Need to seek 0 because st.file_uploader might have been read partly or just to be safe
            uploaded_file.seek(0)
            image = load_raw_image(uploaded_file)
            if image is not None:
                # Convert RGB (from rawpy) to BGR (for opencv/phos pipeline)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    else:
        # Standard Image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if image is None:
        st.error("无法读取图像文件 (如果是 RAW 文件，请确保格式支持)")
        return None, 0, ""

    # Initialize Renderer
    preset = get_preset(preset_name)
    renderer = FilmRenderer(preset)
    
    # Standardize
    with st.spinner('正在标准化图像尺寸...'):
        image = standardize(image)
    
    # Process
    with st.spinner('正在进行光化学模拟 (计算光照/光晕/颗粒)...'):
        film = renderer.process(image, iso, tone_style, exposure_ev, halation_intensity)
    
    process_time = time.time() - start_time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_filename = f"phos_{preset_name}_{timestamp}.jpg"
    
    return film, process_time, output_filename

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.header("Phos_refactor")
        st.subheader("基于计算光学的胶片模拟")
        st.caption("ver_1.0.0 (Refactored)")
        
        st.divider()
        st.text("🎞️ 胶片设置")
        
        # 胶片类型选择
        preset_names = list(PRESETS.keys())
        film_type = st.selectbox(
            "请选择胶片:",
            preset_names,
            index=0,
            help=f"选择要模拟的胶片类型。\n\n当前选择: {get_preset(preset_names[0]).description}" # Dynamic help? Streamlit help is static on render usually.
        )
        
        # Show description of selected film
        current_preset = get_preset(film_type)
        st.info(f"**{film_type}**: {current_preset.description}")

        iso_option = st.select_slider(
            "感光度 (ISO):",
            options=[50, 100, 200, 400, 800, 1600, 3200],
            value=400,
            help="模拟胶片颗粒感。ISO 越高，颗粒越粗糙 (Granularity)。"
        )
        
        tone_style = st.selectbox(
            "Tone Mapping (Gamma 映射):",
            ["filmic", "reinhard"],
            format_func=lambda x: "ACES Standard (电影工业标准)" if x == "filmic" else "Reinhard (传统数码)",
            index=0
        )

        exposure_ev = st.slider(
            "曝光补偿 (EV)",
            min_value=-3.0,
            max_value=3.0,
            value=0.0,
            step=0.1,
            help="调整画面整体曝光。在处理 RAW 文件时特别有用，因为线性空间下未显影的 RAW 通常看起来较暗。"
        )
        
        halation_intensity = st.slider(
            "光晕强度 (Halation)",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="调整光晕的扩散强度。模拟镜头镀膜和底片抗光晕层的效果。"
        )

        st.success(f"已就绪: {film_type}") 
        
        # File Uploader
        uploaded_file = st.file_uploader(
            "选择一张照片 (支持 JPG, PNG, ARW, CR2, NEF, DNG)",
            type=["jpg", "jpeg", "png", "arw", "cr2", "nef", "dng"],
            help="上传一张照片开始冲洗"
        )

    # --- Main Area ---
    if uploaded_file is not None:
        result = process_image(uploaded_file, film_type, iso_option, tone_style, exposure_ev, halation_intensity)
        
        if result and result[0] is not None:
            film_img, p_time, out_path = result
            
            st.image(film_img, caption=f"处理完成 ({p_time:.2f}s)", use_container_width=True)
            st.toast(f"成片显影完成! 用时 {p_time:.2f}秒")
            
            # Prepare Download
            # Convert OpenCV (BGR/Gray) to PIL (RGB/L)
            if len(film_img.shape) == 2:
                film_pil = Image.fromarray(film_img) # Grayscale, no mode needed usually
            else:
                # Renderer returns RGB format
                film_pil = Image.fromarray(film_img)
                
            buf = io.BytesIO()
            film_pil.save(buf, format="JPEG", quality=95)
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 下载成片",
                data=byte_im,
                file_name=out_path,
                mime="image/jpeg"
            )

if __name__ == "__main__":
    main()
