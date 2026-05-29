import streamlit as st
import tempfile
import os
from app.core.pipeline import run_pipeline
from app.db.cache import init_db

# ── Page config — must be the very first Streamlit call ──
st.set_page_config(
    page_title="Medicine Explainer",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Initialise database ──
init_db()

# ── Styling ──────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 18px !important;
    }
    .big-title {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        padding-top: 1rem;
        color: #1a365d !important;
    }
    .subtitle {
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 1.5rem;
        color: #4a5568 !important;
    }
    .medicine-card {
        background-color: #1a365d !important;
        border-left: 5px solid #63b3ed;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff !important;
    }
    .medicine-card h3 {
        color: #ffffff !important;
        margin-bottom: 0.5rem;
    }
    .medicine-card p {
        color: #ffffff !important;
    }
    .warning-box {
        background-color: #744210 !important;
        border: 1px solid #f6ad55;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #fefcbf !important;
    }
    .disclaimer-box {
        background-color: #1a365d !important;
        border: 2px solid #63b3ed;
        padding: 1.2rem;
        border-radius: 8px;
        margin-top: 2rem;
        color: #ffffff !important;
    }
    .disclaimer-box strong {
        color: #90cdf4 !important;
        font-size: 1.1rem;
    }
    .disclaimer-box span {
        color: #e2e8f0 !important;
    }
    .stButton > button {
        font-size: 1.1rem !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown(
    '<div class="big-title">💊 Medicine Explainer</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">'
    'Upload a prescription or medicine pack — '
    'we explain it in plain English.'
    '</div>',
    unsafe_allow_html=True
)

# ── Safety banner ─────────────────────────────────────────────
st.info(
    "ℹ️ This tool provides general information only. "
    "It does NOT diagnose conditions or recommend treatment. "
    "Always consult your doctor or pharmacist.",
    icon="🏥"
)

st.divider()

# ── Input section ─────────────────────────────────────────────
input_mode = st.radio(
    "**How would you like to provide medicine information?**",
    options=["📷 Upload an image", "⌨️ Type a medicine name"],
    horizontal=True
)

result = None

# ── Image upload path ─────────────────────────────────────────
if input_mode == "📷 Upload an image":

    uploaded_file = st.file_uploader(
        "**Upload prescription or medicine pack image**",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        help="Take a clear photo in good lighting for best results"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(
                uploaded_file,
                caption="Your uploaded image",
                use_column_width=True
            )

        with col2:
            st.markdown("**Tips for better results:**")
            st.markdown(
                "📸 Good lighting\n\n"
                "📐 Keep image flat\n\n"
                "🔍 Text in focus\n\n"
                "📱 Avoid shadows"
            )

        if st.button(
            "🔍 Analyse Prescription",
            type="primary",
            use_container_width=True
        ):
            with st.spinner(
                "Reading your prescription... "
                "this may take 20–40 seconds"
            ):
                suffix = "." + uploaded_file.name.split(".")[-1]
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix
                ) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                result = run_pipeline(image_path=tmp_path)
                os.unlink(tmp_path)

# ── Typed name path ───────────────────────────────────────────
elif input_mode == "⌨️ Type a medicine name":

    medicine_input = st.text_input(
        "**Enter medicine name**",
        placeholder="e.g. Paracetamol, Amoxicillin, Metformin...",
        max_chars=100
    )

    if medicine_input:
        if st.button(
            "🔍 Explain Medicine",
            type="primary",
            use_container_width=True
        ):
            with st.spinner(f"Looking up {medicine_input}..."):
                result = run_pipeline(typed_name=medicine_input)

# ── Results section ───────────────────────────────────────────
if result:
    st.divider()
    st.markdown("## 📋 Results")

    # ── Error state ──
    if result.error:
        st.warning(f"⚠️ {result.error}")

    # ── OCR confidence banner (image path only) ──
    if result.ocr_result:
        ocr = result.ocr_result
        conf_pct = round(ocr.confidence * 100)

        if not ocr.is_reliable:
            st.markdown(
                '<div class="warning-box">'
                '⚠️ <strong>Image quality is low.</strong> '
                f'Confidence: {conf_pct}%. '
                'Results may be inaccurate. '
                'Please show the original prescription '
                'to your pharmacist.'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.success(
                f"✅ Image read successfully — "
                f"confidence: {ocr.confidence_label} ({conf_pct}%)"
            )

        with st.expander("📄 View extracted text from image"):
            st.code(ocr.raw_text)

    # ── No medicines found ──
    if result.medicines == [] and not result.error:
        st.warning(
            "⚠️ No medicine names could be identified. "
            "Please check the image quality or "
            "type the medicine name manually."
        )

    # ── Medicine cards ────────────────────────────────────────
    for med_result in result.medicines:
        med = med_result.extracted_medicine
        exp = med_result.explanation

        confidence_emoji = {
            "confirmed": "✅",
            "probable":  "🔶",
            "uncertain": "⚠️"
        }.get(med.confidence, "❓")

        st.markdown(
            f'<div class="medicine-card">'
            f'<h3>{confidence_emoji} {med.name}</h3>'
            f'</div>',
            unsafe_allow_html=True
        )

        if med.confidence == "uncertain":
            st.warning(
                "⚠️ This name could not be confirmed. "
                "Please verify with your pharmacist."
            )

        st.markdown(exp.explanation)
        st.markdown(exp.safety_footer)

        st.caption(
            f"ℹ️ Source: {exp.model_used} "
            f"{'· from cache' if exp.was_cached else '· fresh response'}"
        )

        st.divider()

    # ── Always-visible disclaimer ─────────────────────────────
    if result.medicines:
        st.markdown(
            '<div class="disclaimer-box">'
            '<strong style="color:#1a365d; font-size:1.1rem;">🏥 Always confirm with a healthcare professional</strong>'
            '<br><br>'
            '<span style="color:#2d3748;">'
            'This information is for general awareness only. '
            'It does not replace advice from your doctor or pharmacist. '
            'Do not start, stop, or change any medication '
            'based on this information.'
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center; color:#718096; font-size:0.85rem;'>"
    "Medicine Explainer &nbsp;·&nbsp; "
    "For informational purposes only &nbsp;·&nbsp; "
    "Not a substitute for medical advice"
    "</div>",
    unsafe_allow_html=True
)