import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import sys
import io
import re
from finance_crew import run_financial_analysis, GEMINI_MODEL
from chat_manager import get_manager, get_or_create_chat, set_current_chat, get_current_history, REDIS_AVAILABLE


def _style_figure_for_light_background(fig):
    fig.patch.set_facecolor("white")
    for ax in fig.get_axes():
        ax.set_facecolor("white")
        ax.tick_params(colors="black")
        ax.xaxis.label.set_color("black")
        ax.yaxis.label.set_color("black")
        ax.title.set_color("black")
        legend = ax.get_legend()
        if legend:
            frame = legend.get_frame()
            frame.set_facecolor("white")
            frame.set_edgecolor("black")
            for text in legend.get_texts():
                text.set_color("black")


class _YFWrapper:
    def __init__(self, yf_module):
        self._yf = yf_module
        self.downloads = {}

    def download(self, ticker, *args, **kwargs):
        df = self._yf.download(ticker, *args, **kwargs)
        self.downloads[str(ticker)] = df
        return df

    def Ticker(self, ticker):
        return self._yf.Ticker(ticker)

    def __getattr__(self, name):
        return getattr(self._yf, name)


def _soften_causality(text: str) -> str:
    if not text:
        return text
    replacements = [
        (r"\bis often tied to\b", "may be tied to"),
        (r"\bis driven by\b", "may be driven by"),
        (r"\bis caused by\b", "may be influenced by"),
        (r"\bis due to\b", "may be due to"),
        (r"\bleads to\b", "can lead to"),
        (r"\bresults in\b", "can result in"),
    ]
    softened = text
    for pattern, repl in replacements:
        softened = re.sub(pattern, repl, softened, flags=re.IGNORECASE)
    return softened


def _build_validation_output(yf_wrapper) -> str:
    downloads = getattr(yf_wrapper, "downloads", {}) or {}
    if not downloads:
        return ""

    lines = []
    common_index = None
    for ticker, df in downloads.items():
        try:
            if df is None or getattr(df, "empty", True):
                lines.append(f"No data returned for {ticker}. Please verify the ticker.")
                continue
            latest = df.index.max()
            latest_date = latest.date() if hasattr(latest, "date") else latest
            lines.append(f"Latest data date used for {ticker}: {latest_date}")

            if common_index is None:
                common_index = df.index
            else:
                common_index = common_index.intersection(df.index)
        except Exception:
            continue

    if common_index is not None and len(common_index) > 0:
        latest_common = common_index.max()
        latest_common_date = latest_common.date() if hasattr(latest_common, "date") else latest_common
        lines.append(f"Latest common date used for comparison: {latest_common_date}")

    return "Validation:\n" + "\n".join(lines) if lines else ""

# Page config
st.set_page_config(
    page_title="StockAI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# thom.chat inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Dark theme colors from thom.chat */
    :root {
        --background: #1a1a2e;
        --foreground: #e0e0e0;
        --card: #252542;
        --primary: #5b7bb8;
        --primary-hover: #6b8bc8;
        --muted: #3a3a5c;
        --muted-foreground: #a0a0b0;
        --border: #3a3a5c;
        --sidebar: #12121f;
        --sidebar-accent: #1e1e35;
    }
    
    /* Global styles */
    .stApp {
        background: var(--background) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: var(--sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--foreground) !important;
    }
    
    /* Header styling */
    .main-title {
        font-family: 'Georgia', serif !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* New Chat button - thom.chat style */
    .new-chat-btn {
        background: linear-gradient(180deg, rgba(91, 123, 184, 0.3) 0%, rgba(91, 123, 184, 0.1) 100%) !important;
        border: 1px solid rgba(91, 123, 184, 0.5) !important;
        border-radius: 8px !important;
        color: var(--foreground) !important;
        padding: 0.75rem 1rem !important;
        width: 100% !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .new-chat-btn:hover {
        background: linear-gradient(180deg, rgba(91, 123, 184, 0.5) 0%, rgba(91, 123, 184, 0.2) 100%) !important;
        border-color: rgba(91, 123, 184, 0.7) !important;
    }
    
    /* Chat list items */
    .chat-item {
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        margin: 2px 0;
        cursor: pointer;
        transition: background 0.2s ease;
        color: var(--muted-foreground);
        font-size: 0.875rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .chat-item:hover, .chat-item-active {
        background: var(--sidebar-accent) !important;
        color: var(--foreground);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--foreground) !important;
        padding: 1rem !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(91, 123, 184, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--muted-foreground) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--primary-hover) !important;
        transform: translateY(-1px);
    }
    
    /* Message bubbles */
    .user-message {
        background: var(--muted) !important;
        border-radius: 12px 12px 4px 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        margin-left: 2rem;
        color: var(--foreground);
    }
    
    .assistant-message {
        background: var(--card) !important;
        border-radius: 12px 12px 12px 4px;
        padding: 1rem;
        margin: 0.5rem 0;
        margin-right: 2rem;
        color: var(--foreground);
        border: 1px solid var(--border);
    }
    
    /* Welcome screen */
    .welcome-title {
        font-family: 'Georgia', serif !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .welcome-subtitle {
        color: var(--muted-foreground) !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Suggestion cards */
    .suggestion-card {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .suggestion-card:hover {
        border-color: var(--primary) !important;
        transform: translateY(-2px);
    }
    
    /* Info section */
    .info-section {
        background: var(--card);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid var(--border);
    }
    
    .info-title {
        color: var(--primary);
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .info-text {
        color: var(--muted-foreground);
        font-size: 0.75rem;
        line-height: 1.5;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    .status-redis {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }
    
    .status-memory {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
    }
    
    /* Code expander */
    .streamlit-expanderHeader {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--muted-foreground) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Divider */
    hr {
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = get_or_create_chat()

manager = get_manager()

# Sidebar
with st.sidebar:
    st.markdown('<div class="main-title">📈 StockAI</div>', unsafe_allow_html=True)
    
    # New Chat button
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        new_id = manager.create_chat()
        st.session_state.current_chat_id = new_id
        set_current_chat(new_id)
        st.rerun()
    
    st.divider()
    
    # Status badge
    if REDIS_AVAILABLE:
        st.markdown('<span class="status-badge status-redis">🔴 Redis</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-memory">💾 Memory</span>', unsafe_allow_html=True)
    
    # Chat list
    chats = manager.get_all_chats()
    for chat in chats:
        is_active = chat["id"] == st.session_state.current_chat_id
        btn_type = "primary" if is_active else "secondary"
        
        col1, col2 = st.columns([5, 1])
        with col1:
            title = chat.get("title", "New Chat")[:25]
            if st.button(f"💬 {title}", key=f"chat_{chat['id']}", use_container_width=True, type=btn_type):
                st.session_state.current_chat_id = chat["id"]
                set_current_chat(chat["id"])
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{chat['id']}"):
                manager.delete_chat(chat["id"])
                if chat["id"] == st.session_state.current_chat_id:
                    remaining = manager.get_all_chats()
                    st.session_state.current_chat_id = remaining[0]["id"] if remaining else manager.create_chat()
                st.rerun()
    
    st.divider()
    
    # Info section
    st.markdown(f"""
    <div class="info-section">
        <div class="info-title">ℹ️ About</div>
        <div class="info-text">
            <strong>Model:</strong> {GEMINI_MODEL}<br>
            <strong>Data:</strong> Yahoo Finance<br>
            <strong>Features:</strong><br>
            • Multi-chat with memory<br>
            • Indian & US stocks<br>
            • Smart follow-ups
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main content
history = get_current_history()

if not history:
    # Welcome screen
    st.markdown('<div class="welcome-title">Hey there! 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-subtitle">Ask me anything about stocks and I\'ll generate charts for you.</div>', unsafe_allow_html=True)
    
    # Suggestions
    suggestions = [
        ("📈", "Show Tesla stock for 3 months"),
        ("📊", "Compare AAPL and MSFT for 6 months"),
        ("🇮🇳", "Show Reliance stock for 1 year"),
        ("💹", "TCS vs Infosys comparison")
    ]
    
    cols = st.columns(2)
    for i, (icon, text) in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"{icon} {text}", key=f"sug_{i}", use_container_width=True):
                st.session_state.suggestion = text
                st.rerun()
else:
    # Show chat history
    for msg in history:
        st.markdown(f'<div class="user-message"><strong>You:</strong> {msg["query"]}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="assistant-message">', unsafe_allow_html=True)
        
        # Show chart if available
        if msg.get("chart_base64"):
            import base64
            st.image(f"data:image/png;base64,{msg['chart_base64']}")
        
        with st.expander("📝 View Code"):
            st.code(msg["response"], language="python")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Input area
col1, col2 = st.columns([6, 1])

# Check for suggestion
default_value = st.session_state.pop("suggestion", "")

with col1:
    query = st.text_input(
        "Message",
        value=default_value,
        placeholder="Type your message here, e.g., 'Show Tesla stock for 3 months'",
        label_visibility="collapsed"
    )

with col2:
    send_btn = st.button("Send", type="primary", use_container_width=True)

# Process query
if send_btn and query:
    with st.spinner("🤖 Analyzing..."):
        code = run_financial_analysis(query)
        
        # Generate chart
        chart_base64 = None
        try:
            code_mod = code.replace("plt.show()", "")
            plt.close('all')
            
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            
            yf_wrapper = _YFWrapper(__import__("yfinance"))
            exec(code_mod, {
                "plt": plt, "yf": yf_wrapper,
                "pd": __import__("pandas"), "np": __import__("numpy"),
                "datetime": __import__("datetime")
            })

            output = sys.stdout.getvalue()
            sys.stdout, sys.stderr = old_stdout, old_stderr
            validation_output = _build_validation_output(yf_wrapper)
            if validation_output:
                output = (output.strip() + "\n" if output.strip() else "") + validation_output
            output = _soften_causality(output)
            
            if output.strip():
                code = f"{code}\n\n# Output:\n# " + output.strip().replace("\n", "\n# ")
            
            fig = plt.gcf()
            if fig.get_axes():
                buf = io.BytesIO()
                _style_figure_for_light_background(fig)
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white', edgecolor='white')
                buf.seek(0)
                import base64
                chart_base64 = base64.b64encode(buf.read()).decode()
            plt.close('all')
        except Exception as e:
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
            st.error(f"Chart error: {e}")
        
        # Save to history with chart
        history = manager.get_history(st.session_state.current_chat_id)
        history.append({
            "query": query, "response": code, "chart_base64": chart_base64,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
        
        if REDIS_AVAILABLE:
            from chat_manager import redis_client
            import json
            redis_client.set(f"chat:{manager.user_id}:{st.session_state.current_chat_id}", json.dumps(history))
        
        st.rerun()

# Footer
st.markdown(f"""
<div style="text-align: center; color: #a0a0b0; font-size: 0.75rem; margin-top: 1rem;">
    {GEMINI_MODEL} • Web search enabled
</div>
""", unsafe_allow_html=True)
