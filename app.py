import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid
import os
import re

# 页面配置
st.set_page_config(
    page_title="Kzz AI", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== MDUI 风格自定义 CSS ==========
st.markdown("""
<style>
    :root {
        --primary-color: #6200ee;
        --primary-light: #9d46ff;
        --primary-dark: #0a00b6;
        --secondary-color: #03dac6;
        --background: #f5f5f5;
        --surface: #ffffff;
        --error: #b00020;
        --on-primary: #ffffff;
        --on-surface: #212121;
        --divider: rgba(0,0,0,0.12);
    }

    .stApp {
        background-color: var(--background);
    }

    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--divider);
    }

    .stButton > button {
        border-radius: 4px;
        text-transform: none;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transition: all 0.2s;
    }

    .stButton > button:hover {
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background-color: var(--primary-color);
        color: var(--on-primary);
    }

    .stButton > button[kind="secondary"] {
        background-color: transparent;
        color: var(--primary-color);
        border: 1px solid rgba(0,0,0,0.12);
    }

    .chat-message {
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
        border-bottom-right-radius: 4px;
    }

    .ai-message {
        background: var(--surface);
        color: var(--on-surface);
        margin-right: 20%;
        border: 1px solid var(--divider);
        border-bottom-left-radius: 4px;
    }

    .timestamp {
        font-size: 11px;
        color: rgba(255,255,255,0.7);
        margin-top: 4px;
    }

    .ai-message .timestamp {
        color: rgba(0,0,0,0.38);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== 配置 ==========
TOKEN = st.secrets.get("TOKEN", os.getenv("TOKEN", ""))
ACCOUNT_ID = st.secrets.get("ACCOUNT_ID", os.getenv("ACCOUNT_ID", ""))

if not TOKEN or not ACCOUNT_ID:
    st.error("⚠️ 请在 Secrets 中配置 TOKEN 和 ACCOUNT_ID")
    st.stop()

MODELS = {
    "Kimi K2.5": "@cf/moonshotai/kimi-k2.5",
    "GPT-OSS 120B": "@cf/openai/gpt-oss-120b",
    "GPT-OSS 20B": "@cf/openai/gpt-oss-20b",
    "DeepSeek R1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "Qwen2.5 Coder": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "Qwen3 30B": "@cf/qwen/qwen3-30b-a3b-fp8",
    "Gemma 3 12B": "@cf/google/gemma-3-12b-it",
    "GLM-4.7 Flash": "@cf/zai-org/glm-4.7-flash",
    "Qwen1.5 14B": "@cf/qwen/qwen1.5-14b-chat-awq",
    "Gemma 7B": "@cf/google/gemma-7b-it-lora",
}

def needs_system_role(model_id):
    lower = model_id.lower()
    no_system = ["deepseek", "qwen3", "qwq", "mistral", "llama"]
    return not any(x in lower for x in no_system)

def generate_title(text):
    """自动生成标题"""
    if not text:
        return "新对话"
    text = text.strip()

    # 尝试提取代码中的函数名或类名
    if "def " in text:
        match = re.search(r"def\s+(\w+)", text)
        if match:
            return f"函数 {match.group(1)}"
    if "class " in text:
        match = re.search(r"class\s+(\w+)", text)
        if match:
            return f"类 {match.group(1)}"

    # 前20个字符
    title = text[:20].replace(chr(10), " ").strip()
    if len(text) > 20:
        title += "..."

    # 过滤特殊字符
    title = re.sub(r"[<>`\r\n]", "", title)
    return title if title else "新对话"

def process_file(uploaded_file):
    if uploaded_file is None:
        return None, None
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode("gbk")
        except:
            return None, "编码错误"

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    code_types = {".py": "Python", ".js": "JS", ".html": "HTML", ".java": "Java", 
                  ".cpp": "C++", ".go": "Go", ".rs": "Rust", ".md": "Markdown", ".txt": "Text"}

    return {
        "name": uploaded_file.name,
        "ext": ext,
        "type": code_types.get(ext, "Text"),
        "content": content,
        "size": len(content)
    }, None

def format_file_message(file_info, user_text=""):
    name = file_info["name"]
    content = file_info["content"]
    ftype = file_info["type"]

    max_len = 5000
    if len(content) > max_len:
        content = content[:max_len] + f"\n... [截断，共 {len(file_info['content'])} 字符]"

    lang = file_info["ext"].replace(".", "") if file_info["ext"] else "text"
    prompt = f"文件 `{name}` ({ftype}):\n```{lang}\n{content}\n```"
    if user_text:
        prompt += f"\n\n问题：{user_text}"
    return prompt

def init_session():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "pending_file" not in st.session_state:
        st.session_state.pending_file = None
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = None
    if "show_new" not in st.session_state:
        st.session_state.show_new = False

    if not st.session_state.sessions:
        create_session("开始对话")

def create_session(name, model="Kimi K2.5"):
    sid = str(uuid.uuid4())[:8]
    model_id = MODELS[model]
    messages = []
    if needs_system_role(model_id):
        messages.append({"role": "system", "content": "你是智能助手", "time": datetime.now().isoformat()})

    st.session_state.sessions[sid] = {
        "id": sid,
        "name": name,
        "model": model,
        "messages": messages,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    st.session_state.current_id = sid
    return sid

def get_session():
    cid = st.session_state.current_id
    if cid and cid in st.session_state.sessions:
        return st.session_state.sessions[cid]
    if st.session_state.sessions:
        first = list(st.session_state.sessions.keys())[0]
        st.session_state.current_id = first
        return st.session_state.sessions[first]
    return None

def delete_session(sid):
    if sid in st.session_state.sessions:
        del st.session_state.sessions[sid]
        if st.session_state.current_id == sid:
            if st.session_state.sessions:
                st.session_state.current_id = list(st.session_state.sessions.keys())[0]
            else:
                create_session("新会话")

def rename_session(sid, new_name):
    if sid in st.session_state.sessions and new_name.strip():
        st.session_state.sessions[sid]["name"] = new_name.strip()
        st.session_state.sessions[sid]["updated_at"] = datetime.now().isoformat()

def switch_model(sid, new_model):
    if sid not in st.session_state.sessions:
        return
    session = st.session_state.sessions[sid]
    old_id = MODELS[session["model"]]
    new_id = MODELS[new_model]

    old_sys = needs_system_role(old_id)
    new_sys = needs_system_role(new_id)

    session["model"] = new_model
    if old_sys != new_sys:
        if new_sys:
            session["messages"] = [{"role": "system", "content": "你是智能助手", "time": datetime.now().isoformat()}]
        else:
            session["messages"] = []
    session["updated_at"] = datetime.now().isoformat()

@st.cache_data(ttl=3600)
def get_api_url(model):
    return f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model}"

def call_api(session, text, auto_title=False):
    try:
        model_id = MODELS[session["model"]]
        url = get_api_url(model_id)

        now = datetime.now().isoformat()
        session["messages"].append({"role": "user", "content": text, "time": now})

        # 自动重命名
        if auto_title and session["name"] in ["开始对话", "新会话", "默认会话"]:
            user_msgs = [m for m in session["messages"] if m["role"] == "user"]
            if len(user_msgs) == 1:
                session["name"] = generate_title(text)

        # 构建 payload（去掉 time 字段）
        payload_msgs = [{"role": m["role"], "content": m["content"]} for m in session["messages"]]
        data = json.dumps({"messages": payload_msgs}).encode()

        req = urllib.request.Request(
            url, data=data,
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            if result.get("success"):
                reply = result.get("result", {}).get("response")
                if not reply and "choices" in result.get("result", {}):
                    reply = result["result"]["choices"][0]["message"]["content"]

                if reply:
                    session["messages"].append({
                        "role": "assistant", 
                        "content": reply,
                        "time": datetime.now().isoformat()
                    })
                    session["updated_at"] = datetime.now().isoformat()
                    return reply, None
                else:
                    session["messages"].pop()
                    return None, "空响应"
            else:
                session["messages"].pop()
                err = result.get("errors", [{}])[0].get("message", "未知错误")
                return None, f"API错误: {err}"
    except Exception as e:
        session["messages"].pop()
        return None, str(e)

def export_session(session, fmt):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        data = {
            "version": "2.0",
            "name": session["name"],
            "model": session["model"],
            "created_at": session.get("created_at", ""),
            "messages": session["messages"]
        }
        return json.dumps(data, ensure_ascii=False, indent=2), f"{session['name']}_{ts}.json"
    elif fmt == "md":
        content = f"# {session['name']}\n\n"
        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            time_str = ""
            if "time" in msg:
                try:
                    dt = datetime.fromisoformat(msg["time"])
                    time_str = f" *{dt.strftime('%H:%M')}*"
                except:
                    pass
            role = "**用户**" if msg["role"] == "user" else "**AI**"
            content += f"{role}{time_str}:\n{msg['content']}\n\n---\n\n"
        return content, f"{session['name']}_{ts}.md"
    else:
        content = f"会话: {session['name']}\n\n"
        for msg in session["messages"]:
            if msg["role"] != "system":
                content += f"[{msg['role']}] {msg.get('time', '')}\n{msg['content']}\n\n"
        return content, f"{session['name']}_{ts}.txt"

def import_session(file_content):
    try:
        data = json.loads(file_content)

        if "sessions" in data:
            count = 0
            for sid, sdata in data["sessions"].items():
                new_id = str(uuid.uuid4())[:8]
                msgs = sdata.get("messages", [])
                for m in msgs:
                    if "time" not in m:
                        m["time"] = datetime.now().isoformat()
                st.session_state.sessions[new_id] = {
                    "id": new_id,
                    "name": sdata.get("name", f"导入_{count+1}"),
                    "model": sdata.get("model", "Kimi K2.5"),
                    "messages": msgs,
                    "created_at": sdata.get("created_at", datetime.now().isoformat()),
                    "updated_at": datetime.now().isoformat()
                }
                count += 1
            return True, f"导入 {count} 个会话"

        sid = str(uuid.uuid4())[:8]
        msgs = data.get("messages", [])
        for m in msgs:
            if "time" not in m:
                m["time"] = datetime.now().isoformat()

        st.session_state.sessions[sid] = {
            "id": sid,
            "name": data.get("name", "导入的会话"),
            "model": data.get("model", "Kimi K2.5"),
            "messages": msgs,
            "created_at": data.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        st.session_state.current_id = sid
        return True, "导入 1 个会话"
    except Exception as e:
        return False, f"导入失败: {str(e)}"

# ========== UI ==========
init_session()
session = get_session()

with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0; text-align: center;">
        <h2 style="color: #6200ee; margin: 0;">🤖 Kzz AI</h2>
        <p style="color: rgba(0,0,0,0.6); font-size: 12px;">智能对话助手</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ 新建对话", use_container_width=True, type="primary"):
        st.session_state.show_new = True
        st.rerun()

    if st.session_state.show_new:
        with st.form("new_session"):
            name = st.text_input("名称（可选）", placeholder="留空自动生成")
            cols = st.columns([1, 1])
            with cols[0]:
                if st.form_submit_button("✓ 创建", use_container_width=True):
                    create_session(name if name else "新对话")
                    st.session_state.show_new = False
                    st.rerun()
            with cols[1]:
                if st.form_submit_button("✗ 取消", use_container_width=True):
                    st.session_state.show_new = False
                    st.rerun()

    st.divider()

    with st.expander("📎 上传文件"):
        uploaded = st.file_uploader(
            "选择",
            type=["py", "js", "html", "java", "cpp", "go", "rs", "md", "txt", "json"],
            label_visibility="collapsed"
        )
        if uploaded:
            info, err = process_file(uploaded)
            if err:
                st.error(err)
            else:
                st.session_state.pending_file = info
                st.success(f"✓ {info['name']}")
                if st.button("清除"):
                    st.session_state.pending_file = None
                    st.rerun()

    st.divider()

    st.subheader(f"📂 会话列表 ({len(st.session_state.sessions)})")

    sessions_sorted = sorted(
        st.session_state.sessions.values(),
        key=lambda x: x["updated_at"],
        reverse=True
    )

    for idx, s in enumerate(sessions_sorted):
        is_active = s["id"] == st.session_state.current_id
        msg_count = len([m for m in s["messages"] if m["role"] != "system"])

        cols = st.columns([6, 1, 1])

        with cols[0]:
            btn_type = "primary" if is_active else "secondary"
            label = f"{s['name'][:15]}{'...' if len(s['name']) > 15 else ''} ({msg_count})"

            if st.button(label, key=f"sess_btn_{s['id']}_{idx}", 
                      type=btn_type, use_container_width=True):
                st.session_state.current_id = s["id"]
                st.rerun()

        with cols[1]:
            if st.button("✏️", key=f"rename_{s['id']}_{idx}", help="重命名"):
                st.session_state.edit_mode = s["id"]
                st.rerun()

        with cols[2]:
            can_delete = len(st.session_state.sessions) > 1
            if st.button("🗑️", key=f"delete_{s['id']}_{idx}",
                       disabled=not can_delete):
                if can_delete:
                    delete_session(s["id"])
                    st.rerun()

        if st.session_state.edit_mode == s["id"]:
            with st.form(f"rename_form_{s['id']}"):
                new_name = st.text_input("新名称", value=s["name"], label_visibility="collapsed")
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.form_submit_button("保存", use_container_width=True):
                        rename_session(s["id"], new_name)
                        st.session_state.edit_mode = None
                        st.rerun()
                with c2:
                    if st.form_submit_button("取消", use_container_width=True):
                        st.session_state.edit_mode = None
                        st.rerun()

    st.divider()

    with st.expander("💾 导入/导出"):
        st.markdown("**📥 导入**")
        import_file = st.file_uploader("选 JSON", type=["json"], key="import_uploader", label_visibility="collapsed")
        if import_file:
            content = import_file.read().decode("utf-8")
            success, msg = import_session(content)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        if session:
            st.markdown("**📤 导出**")
            fmt = st.selectbox("格式", ["JSON", "Markdown", "TXT"], key="export_fmt")
            content, fname = export_session(session, fmt.lower())
            st.download_button("下载", content, fname, use_container_width=True)

    total_msgs = sum(len([m for m in s["messages"] if m["role"] != "system"]) 
                    for s in st.session_state.sessions.values())
    st.caption(f"💡 {len(st.session_state.sessions)} 会话，{total_msgs} 消息")

if session:
    st.markdown(f"<h3>💬 {session['name']}</h3>", unsafe_allow_html=True)

    cols = st.columns([3, 1])
    with cols[0]:
        cur = session["model"]
        opts = list(MODELS.keys())
        sel = st.selectbox("模型", opts, index=opts.index(cur), label_visibility="collapsed")
        if sel != cur:
            switch_model(session["id"], sel)
            st.rerun()
    with cols[1]:
        st.caption(f"📊 {len([m for m in session['messages'] if m['role']!='system'])} 条")

    if st.session_state.pending_file:
        f = st.session_state.pending_file
        st.info(f"📎 已就绪: {f['name']} ({f['size']} 字符)")

    for msg in session["messages"]:
        if msg["role"] == "system":
            continue

        is_user = msg["role"] == "user"
        css_class = "user-message" if is_user else "ai-message"

        time_str = ""
        if "time" in msg:
            try:
                dt = datetime.fromisoformat(msg["time"])
                time_str = dt.strftime("%m-%d %H:%M")
            except:
                pass

        with st.chat_message(msg["role"]):
            st.markdown(f"""
            <div class="chat-message {css_class}">
                {msg['content']}
                <div class="timestamp">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)

    placeholder = "输入消息..." + (" (将附带文件)" if st.session_state.pending_file else "")
    if prompt := st.chat_input(placeholder):
        if st.session_state.pending_file:
            full_prompt = format_file_message(st.session_state.pending_file, prompt)
            st.session_state.pending_file = None
        else:
            full_prompt = prompt

        with st.chat_message("user"):
            st.markdown(f"""
            <div class="chat-message user-message">
                {prompt}
                <div class="timestamp">{datetime.now().strftime('%m-%d %H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                reply, err = call_api(session, full_prompt, auto_title=True)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.markdown(f"""
                    <div class="chat-message ai-message">
                        {reply}
                        <div class="timestamp">{datetime.now().strftime('%m-%d %H:%M')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()

    st.divider()
    if st.button("🗑️ 清空对话", use_container_width=True):
        mid = MODELS[session["model"]]
        session["messages"] = [{"role": "system", "content": "你是助手", "time": datetime.now().isoformat()}] if needs_system_role(mid) else []
        session["updated_at"] = datetime.now().isoformat()
        st.rerun()
else:
    st.error("没有活动会话")
