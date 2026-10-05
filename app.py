import streamlit as st
from datetime import datetime
from scraper import scrape_latest_articles
from cleaner import clean_text
from summarizer import summarize_article
from error_log import log_error, load_errors, clear_errors


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="ZapRead",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HELPERS
# ============================================================
def format_date(iso_string):
    """Convert '2026-10-05T08:14:24-07:00' to 'October 5, 2026 · 8:14 AM'."""
    if not iso_string or iso_string == "N/A":
        return "Unknown date"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%B %d, %Y · %I:%M %p").lstrip("0").replace(" 0", " ")
    except (ValueError, TypeError):
        return iso_string


def render_paragraphs(content):
    """
    Renders content preserving paragraph breaks.
    Splits on double newlines and writes each paragraph separately.
    """
    if not content or content == "N/A":
        st.write("No content available.")
        return

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for para in paragraphs:
        st.write(para)


# ============================================================
# SESSION STATE
# ============================================================
if "article_options" not in st.session_state:
    st.session_state.article_options = {}
if "article" not in st.session_state:
    st.session_state.article = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "view" not in st.session_state:
    st.session_state.view = "original"
if "last_requested_url" not in st.session_state:
    st.session_state.last_requested_url = None


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("ZapRead ⚡")
st.sidebar.caption("🤖 AI Article Summarizer")
st.sidebar.markdown("---")

st.sidebar.subheader("📰 Select an Article")

# --- Load headlines on demand ---
if st.sidebar.button("🔄 Load Latest Articles", use_container_width=True):
    with st.spinner("Fetching latest articles..."):
        try:
            articles = scrape_latest_articles(
                num_articles=3,
                articles_url="https://techcrunch.com/",
            )
            if articles:
                st.session_state.article_options = {
                    f"{a['Title'][:60]}...": a["URL"]
                    for a in articles
                    if a.get("URL") and a["URL"] != "N/A"
                }
                st.sidebar.success(f"✅ Loaded {len(st.session_state.article_options)} articles.")
            else:
                st.sidebar.warning("No articles found.")
                log_error(
                    context="streamlit_app.load_articles",
                    error_type="html_structure",
                    message="Scraper returned no articles.",
                )
        except Exception as e:
            st.sidebar.error(f"Could not fetch articles: {e}")
            log_error(
                context="streamlit_app.load_articles",
                error_type="connection",
                message=str(e),
            )

# --- Dropdown ---
option_labels = ["-- Select an article --"] + list(st.session_state.article_options.keys())
selected_label = st.sidebar.selectbox("Latest TechCrunch Articles", option_labels)
st.sidebar.markdown("**— OR —**")

# --- Custom URL ---
custom_url = st.sidebar.text_input("Custom URL", placeholder="https://techcrunch.com/...")

# --- Summary length slider ---
summary_length = st.sidebar.slider(
    "Summary Length (words)",
    min_value=50,
    max_value=500,
    value=200,
    step=10,
)

st.sidebar.markdown("---")

# --- Error Log Viewer ---
with st.sidebar.expander("🐞 Error Log", expanded=False):
    errors = load_errors()
    if not errors:
        st.write("No errors logged. 🎉")
    else:
        st.write(f"**{len(errors)}** error(s) logged.")
        for e in errors[-5:][::-1]:
            st.markdown(
                f"**{e['error_type']}** · `{e['context']}`  \n"
                f"_{e['timestamp'][:19]}_  \n"
                f"{e['message']}  \n"
                f"---"
            )
        if st.button("🗑️ Clear error log"):
            clear_errors()
            st.rerun()


# ============================================================
# HELPERS (fetch + reset)
# ============================================================
def fetch_article(url):
    """Fetch a single article and return cleaned article dict (or None)."""
    articles = scrape_latest_articles(num_articles=1, articles_url=url)
    if not articles:
        return None
    meta = articles[0]
    if not meta.get("Content") or meta["Content"] == "N/A":
        return None
    cleaned_content = clean_text(meta["Content"])
    return {
        "Title": meta.get("Title", "Untitled"),
        "URL": meta.get("URL", url),
        "Author": meta.get("Author", "N/A"),
        "Published Date": meta.get("Published Date", "N/A"),
        "Content": cleaned_content,
        "Word Count": len(cleaned_content.split()),
    }


def reset_state():
    st.session_state.article = None
    st.session_state.summary = None
    st.session_state.view = "original"
    st.session_state.last_requested_url = None


# ============================================================
# DETECT SELECTION CHANGE -> TRIGGER SCRAPE
# ============================================================
requested_url = None

if custom_url.strip():
    if not custom_url.strip().startswith("http"):
        st.error("❌ Custom URL must start with http:// or https://")
        log_error(
            context="streamlit_app.input_validation",
            error_type="bad_input",
            message=f"Invalid URL entered: {custom_url.strip()}",
        )
        requested_url = None
    else:
        requested_url = custom_url.strip()
elif selected_label != "-- Select an article --":
    requested_url = st.session_state.article_options.get(selected_label)

if requested_url and requested_url != st.session_state.last_requested_url:
    reset_state()
    st.session_state.last_requested_url = requested_url

    with st.spinner("🌐 Scraping and cleaning article..."):
        article_data = fetch_article(requested_url)

    if article_data:
        st.session_state.article = article_data
    else:
        st.error("❌ Failed to fetch or clean the article. Please check the URL.")
        log_error(
            context="streamlit_app.fetch_article",
            error_type="scrape_failure",
            message="fetch_article returned None.",
            url=requested_url,
        )


# ============================================================
# MAIN AREA
# ============================================================
st.write("## Welcome to ⚡ ZapRead!")
st.write("🧠 Scrape the noise. Clean the text. Get the gist.")
st.markdown("---")

if not st.session_state.article:
    st.info(
        "👈 Please select an article from the dropdown or enter a custom URL "
        "in the sidebar to get started."
    )
else:
    article = st.session_state.article

    # ---- Article header ----
    st.subheader(article["Title"])
    st.caption(
        f"By **{article['Author']}** · {format_date(article['Published Date'])} · "
        f"{article['Word Count']} words"
    )
    st.markdown(f"[🔗 Read original]({article['URL']})")
    st.markdown("---")

    # ---- CSS to style radio buttons as tabs ----
    st.markdown("""
    <style>
    div[role="radiogroup"] {
        gap: 12px;
        flex-direction: row;
        margin-bottom: 1rem;
    }
    div[role="radiogroup"] > label {
        background: #f0f2f6;
        padding: 10px 28px;
        border-radius: 8px;
        margin: 0 !important;
        cursor: pointer;
        border: 1px solid #ddd;
        transition: all 0.15s ease;
    }
    div[role="radiogroup"] > label:hover {
        background: #e6e9ef;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background: #ff4b4b;
        border-color: #ff4b4b;
    }
    div[role="radiogroup"] > label:has(input:checked) p {
        color: white !important;
        font-weight: 600;
    }
    div[role="radiogroup"] input {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---- View switcher (radio tabs) ----
    view_choice = st.radio(
        "View",
        options=["📄 Original Content", "🤖 AI Summary"],
        horizontal=True,
        label_visibility="collapsed",
        index=0 if st.session_state.view == "original" else 1,
        key="view_radio",
    )
    new_view = "original" if "Original" in view_choice else "summary"
    if new_view != st.session_state.view:
        st.session_state.view = new_view
        st.rerun()

    st.markdown("---")

    # ============================================================
    # ORIGINAL CONTENT VIEW
    # ============================================================
    if st.session_state.view == "original":
        st.subheader("📄 Original Content")
        render_paragraphs(article["Content"])

    # ============================================================
    # AI SUMMARY VIEW
    # ============================================================
    elif st.session_state.view == "summary":
        if not st.session_state.summary:
            with st.spinner("🚀 Generating summary..."):
                try:
                    st.session_state.summary = summarize_article(
                        article["Content"],
                        target_length=summary_length,
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
                    log_error(
                        context="streamlit_app.summarize",
                        error_type="inference",
                        message=str(e),
                        url=article["URL"],
                    )
                    st.session_state.summary = ""

        if st.session_state.summary:
            st.subheader("🤖 AI Summary")

            # ---- Summary statistics ----
            summary_words = len(st.session_state.summary.split())
            original_words = article["Word Count"]
            compression = (
                f"{100 - int(summary_words / original_words * 100)}% smaller"
                if original_words else "N/A"
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("Summary Words", summary_words)
            col2.metric("Original Words", original_words)
            col3.metric("Compression", compression)

            # ---- Summary content in a bordered container ----
            with st.container(border=True):
                render_paragraphs(st.session_state.summary)

    # ============================================================
    # EXPORT
    # ============================================================
    st.markdown("---")
    st.subheader("📤 Export")

    summary_section = st.session_state.summary or "(summary not generated yet)"

    export_text = f"""ZapRead Export
==============

Title: {article['Title']}
Author: {article['Author']}
Published: {article['Published Date']}
URL: {article['URL']}
Word Count: {article['Word Count']}

--- AI SUMMARY ---
{summary_section}

--- ORIGINAL CONTENT ---
{article['Content']}
"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download as Text (.txt)",
            data=export_text,
            file_name=f"zapread_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download as Markdown (.md)",
            data=export_text,
            file_name=f"zapread_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )