"""
FastAPI Backend for Financial Analyst UI
Uses mem0 for semantic memory instead of Redis
"""
import os
import sys
import io
import base64
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import our modules
from finance_crew import run_financial_analysis, get_memories, clear_memory


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Financial Analyst API starting...")
    print("Using mem0 for semantic memory")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Financial Analyst API",
    description="API for stock analysis with mem0 semantic memory",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    query: str
    user_id: str = "default_user"


@app.get("/")
def root():
    return {"status": "ok", "message": "Financial Analyst API v2.0 (mem0)"}


@app.get("/memories/{user_id}")
def get_user_memories(user_id: str):
    """Get all memories for a user"""
    memories = get_memories(user_id)
    return {"memories": memories, "user_id": user_id}


@app.delete("/memories/{user_id}")
def clear_user_memories(user_id: str):
    """Clear all memories for a user"""
    clear_memory(user_id)
    return {"status": "cleared", "user_id": user_id}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """Analyze a stock query and return chart"""
    user_id = request.user_id
    
    # Run analysis with mem0 context
    code = run_financial_analysis(request.query, user_id=user_id)
    
    if code.startswith("Error:"):
        return {"code": code, "chart_base64": None, "user_id": user_id}
    
    # Try to execute and capture chart
    chart_base64 = None
    try:
        code_modified = code.replace("plt.show()", "")
        plt.close('all')
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        yf_wrapper = _YFWrapper(__import__("yfinance"))
        exec(code_modified, {
            "plt": plt,
            "yf": yf_wrapper,
            "pd": __import__("pandas"),
            "np": __import__("numpy"),
            "datetime": __import__("datetime"),
        })
        
        # Get captured output
        output = sys.stdout.getvalue()
        errors = sys.stderr.getvalue()

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        validation_output = _build_validation_output(yf_wrapper)
        if validation_output:
            output = (output.strip() + "\n" if output.strip() else "") + validation_output

        output = _soften_causality(output)
        
        # If there was printed output, append it as a comment to the code
        if output.strip():
            code = f"{code}\n\n# Output:\n# " + output.strip().replace("\n", "\n# ")
        
        # Save figure to base64
        fig = plt.gcf()
        if fig.get_axes():
            buf = io.BytesIO()
            _style_figure_for_light_background(fig)
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white', edgecolor='white')
            buf.seek(0)
            chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close('all')
        
    except Exception as e:
        # Better error reporting including stdout so far
        if 'old_stdout' in locals():
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        else:
            output = ""

        error_msg = str(e)
        if error_msg == "0":
            error_msg = "Indexing error (Tip: Use .iloc[0] instead of [0] for stock data)"
            
        code = f"# Error executing: {error_msg}\n\n{code}"
        if output.strip():
            code = f"{code}\n\n# Output before error:\n# " + output.strip().replace("\n", "\n# ")
    
    return {
        "code": code,
        "chart_base64": chart_base64,
        "user_id": user_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
