import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid
import os
import zipfile
import io

st.set_page_config(page_title="Kzz AI", page_icon="🤖", layout="wide")

# ========== 配置 ==========
TOKEN = st.secrets.get("TOKEN", os.getenv("TOKEN", ""))
ACCOUNT_ID = st.secrets.get("ACCOUNT_ID", os.getenv("ACCOUNT_ID", ""))

if not TOKEN or not ACCOUNT_ID:
    st.error("⚠️ 请在 Secrets 中配置 TOKEN 和 ACCOUNT_ID")
    st.stop()

# 模型列表
MODELS = {
    "Kimi K2.5": "@cf/moonshotai/kimi-k2.5",
    "GPT-OSS 20B": "@cf/openai/gpt-oss-20b",
    "GPT-OSS 120B": "@cf/openai/gpt-oss-120b",
    "Gemma 3 12B": "@cf/google/gemma-3-12b-it",
    "Gemma 7B": "@cf/google/gemma-7b-it-lora",
    "Gemma 2B": "@cf/google/gemma-2b-it-lora",
    "Gemma 7B HF": "@hf/google/gemma-7b-it",
    "Qwen3 30B": "@cf/qwen/qwen3-30b-a3b-fp8",
    "Qwen QWQ 32B": "@cf/qwen/qwq-32b",
    "Qwen2.5 Coder 32B": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "Qwen1.5 14B": "@cf/qwen/qwen1.5-14b-chat-awq",
    "DeepSeek R1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "GLM-4.7 Flash": "@cf/zai-org/glm-4.7-flash",
}

def needs_system_role(model_id):
    lower = model_id.lower()
    no_system = ["llama", "mistral", "deepseek", "qwen3", "qwq", "tinyllama", "phi"]
    return not any(x in lower for x in no_system)

# ========== 文件上传功能 ==========
def process_file(uploaded_file):
    """处理上传的文件"""
    if uploaded_file is None:
        return None, None
    
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()
    
    # 代码文件类型映射
    code_types = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", 
                  ".html": "HTML", ".css": "CSS", ".java": "Java", 
                  ".cpp": "C++", ".c": "C", ".go": "Go", ".rs": "Rust",
                  ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
                  ".rb": "Ruby", ".sql": "SQL", ".json": "JSON",
                  ".xml": "XML", ".yaml": "YAML", ".yml": "YAML",
                  ".md": "Markdown", ".txt": "Text", ".csv": "CSV"}
    
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode("gbk")
        except:
            return None, "文件编码错误，请上传 UTF-8 或 GBK 编码的文件"
    
    file_type = code_types.get(ext, "Text")
    
    return {
        "name": filename,
        "ext": ext,
        "type": file_type,
        "content": content,
        "size": len(content)
    }, None

def format_file_message(file_info, user_text=""):
    """格式化文件内容为消息"""
    name = file_info["name"]
    content = file_info["content"]
    ftype = file_info["type"]
    ext = file_info["ext"]
    
    # 截断长内容（限制 6000 字符约 1500 tokens）
    max_len = 6000
    if len(content) > max_len:
        content = content[:max_len] + f"\n\n... [已截断，共 {len(file_info['content'])} 字符]"
    
    # 构建提示
    lang = ext.replace(".", "") if ext else "text"
    prompt = f"我上传了一个 {ftype} 文件 `{name}`，内容如下：\n\n"
    prompt += f"```{lang}\n{content}\n```\n\n"
    
    if user_text:
        prompt += f"问题：{user_text}"
    else:
        prompt += "请分析这个文件的内容和结构。"
    
    return prompt

# ========== Session ==========
def init_session():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "pending_file" not in st.session_state:
        st.session_state.pending_file = None
    
    if not st.session_state.sessions:
        create_session("默认会话")

def create_session(name, model="Kimi K2.5"):
    sid = str(uuid.uuid4())[:8]
    model_id = MODELS[model]
    messages = [{"role": "system", "content": "你是智能助手"}] if needs_system_role(model_id) else []
    st.session_state.sessions[sid] = {
        "id": sid, "name": name, "model": model,
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

def switch_model(sid, new_model):
    if sid not in st.session_state.sessions: return
    session = st.session_state.sessions[sid]
    old_id = MODELS[session["model"]]
    new_id = MODELS[new_model]
    
    old_sys = needs_system_role(old_id)
    new_sys = needs_system_role(new_id)
    
    session["model"] = new_model
    if old_sys != new_sys:
        session["messages"] = [{"role": "system", "content": "你是智能助手"}] if new_sys else []
    session["updated_at"] = datetime.now().isoformat()

def delete_session(sid):
    if sid in st.session_state.sessions:
        del st.session_state.sessions[sid]
        if st.session_state.current_id == sid:
            if st.session_state.sessions:
                st.session_state.current_id = list(st.session_state.sessions.keys())[0]
            else:
                create_session("默认会话")

def rename_session(sid, new_name):
    if sid in st.session_state.sessions:
        st.session_state.sessions[sid]["name"] = new_name
        st.session_state.sessions[sid]["updated_at"] = datetime.now().isoformat()

# ========== API ==========
def get_api_url(model_id):
    return f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model_id}"

def extract_response(result):
    if not result or not result.get("success"): return None
    data = result.get("result", {})
    if isinstance(data, dict):
        if "response" in data: return data["response"]
        if "choices" in data and data["choices"]:
            return data["choices"][0].get("message", {}).get("content")
    return str(data)

def call_api(session, text):
    try:
        model_id = MODELS[session["model"]]
        url = get_api_url(model_id)
        
        session["messages"].append({"role": "user", "content": text})
        session["updated_at"] = datetime.now().isoformat()
        
        data = json.dumps({"messages": session["messages"]}).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            if result.get("success"):
                reply = extract_response(result)
                if reply:
                    session["messages"].append({"role": "assistant", "content": reply})
                    session["updated_at"] = datetime.now().isoformat()
                    return reply, None
                else:
                    session["messages"].pop()
                    return None, "解析失败"
            else:
                session["messages"].pop()
                err = result.get("errors", [{}])[0].get("message", "未知错误")
                return None, f"API错误: {err}"
    except Exception as e:
        session["messages"].pop()
        return None, f"请求失败: {str(e)}"

# ========== Export/Import ==========
def export_session(session, fmt):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "json":
        data = {"name": session["name"], "model": session["model"], "messages": session["messages"]}
        return json.dumps(data, ensure_ascii=False, indent=2), f"{session['name']}_{ts}.json"
    elif fmt == "md":
        content = f"# {session['name']}\n\n"
        for msg in session["messages"]:
            if msg["role"] != "system":
                role = "用户" if msg["role"] == "user" else "AI"
                content += f"## {role}\n{msg['content']}\n\n"
        return content, f"{session['name']}_{ts}.md"
    else:
        content = f"会话: {session['name']}\n\n"
        for msg in session["messages"]:
            if msg["role"] != "system":
                content += f"[{msg['role']}] {msg['content']}\n\n"
        return content, f"{session['name']}_{ts}.txt"

def import_session(content):
    try:
        data = json.loads(content)
        if "sessions" in data:
            count = 0
            for sid, sdata in data["sessions"].items():
                new_id = str(uuid.uuid4())[:8]
                st.session_state.sessions[new_id] = {
                    "id": new_id, "name": f"导入_{sdata.get('name', '会话')}",
                    "model": sdata.get("model", "Kimi K2.5"),
                    "messages": sdata.get("messages", []),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                count += 1
            return True, f"导入 {count} 个会话"
        else:
            sid = str(uuid.uuid4())[:8]
            st.session_state.sessions[sid] = {
                "id": sid, "name": f"导入_{data.get('name', '会话')}",
                "model": data.get("model", "Kimi K2.5"),
                "messages": data.get("messages", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            st.session_state.current_id = sid
            return True, "导入 1 个会话"
    except Exception as e:
        return False, str(e)

# ========== UI ==========
init_session()
session = get_session()

# 侧边栏
with st.sidebar:
    st.title("Kzz AI")
    
    if st.button("➕ 新建会话", use_container_width=True, type="primary"):
        create_session(f"会话{len(st.session_state.sessions)+1}")
        st.rerun()
    
    st.divider()
    
    # 文件上传区域
    st.subheader("📎 上传文件")
    uploaded = st.file_uploader(
        "支持代码/文本",
        type=["py", "js", "html", "css", "java", "cpp", "c", "go", "rs", "php", "swift", "kt", "rb", "sql", "json", "xml", "yaml", "yml", "md", "txt", "csv"],
        label_visibility="collapsed"
    )
    
    if uploaded:
        file_info, error = process_file(uploaded)
        if error:
            st.error(error)
        else:
            st.session_state.pending_file = file_info
            st.success(f"✅ {file_info['name']} ({file_info['size']} 字符)")
            if st.button("❌ 清除文件"):
                st.session_state.pending_file = None
                st.rerun()
    
    st.divider()
    
    # 会话列表
    st.subheader(f"📂 会话 ({len(st.session_state.sessions)}个)")
    for s in sorted(st.session_state.sessions.values(), key=lambda x: x["updated_at"], reverse=True):
        c1, c2, c3 = st.columns([8, 1, 1])
        with c1:
            cnt = len([m for m in s["messages"] if m["role"] != "system"])
            label = f"{s['name']} ({cnt})"
            is_cur = s["id"] == st.session_state.current_id
            if st.button(label, key=f"btn_{s['id']}", type="primary" if is_cur else "secondary", use_container_width=True):
                st.session_state.current_id = s["id"]
                st.rerun()
        with c2:
            if st.button("✏️", key=f"ren_{s['id']}"):
                st.session_state[f"editing_{s['id']}"] = True
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"del_{s['id']}"):
                if len(st.session_state.sessions) > 1:
                    delete_session(s["id"])
                    st.rerun()
        
        if st.session_state.get(f"editing_{s['id']}"):
            with st.form(f"form_{s['id']}"):
                new_name = st.text_input("新名称", s["name"], label_visibility="collapsed")
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("✓"):
                        rename_session(s["id"], new_name)
                        del st.session_state[f"editing_{s['id']}"]
                        st.rerun()
                with c2:
                    if st.form_submit_button("✗"):
                        del st.session_state[f"editing_{s['id']}"]
                        st.rerun()
    
    st.divider()
    
    # 导入导出
    with st.expander("📥 导入 / 📤 导出"):
        uploaded_json = st.file_uploader("导入 JSON", type=["json"], label_visibility="collapsed")
        if uploaded_json:
            ok, msg = import_session(uploaded_json.read().decode("utf-8"))
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        
        if session:
            fmt = st.selectbox("格式", ["JSON", "Markdown", "TXT"], key="fmt")
            content, fname = export_session(session, fmt.lower())
            st.download_button("⬇️ 导出", content, fname, use_container_width=True)
    
    total_msgs = sum(len([m for m in s["messages"] if m["role"] != "system"]) for s in st.session_state.sessions.values())
    st.caption(f"💡 {len(st.session_state.sessions)}会话 | {total_msgs}消息")

# 主界面
if session:
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.header(f"💬 {session['name']}")
    with c2:
        cur_model = session["model"]
        opts = list(MODELS.keys())
        sel = st.selectbox("模型", opts, index=opts.index(cur_model), label_visibility="collapsed")
        if sel != cur_model:
            switch_model(session["id"], sel)
            st.rerun()
    with c3:
        st.caption(MODELS[session["model"]].split("/")[-1][:20])
    
    # 显示待上传文件
    if st.session_state.pending_file:
        f = st.session_state.pending_file
        st.info(f"📎 待发送文件: {f['name']} ({f['type']}, {f['size']} 字符) - 在下方输入问题后一起发送")
    
    # 显示消息历史
    for msg in session["messages"]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # 输入框
    placeholder = "输入消息..." if not st.session_state.pending_file else "输入关于文件的问题（可选）..."
    if prompt := st.chat_input(placeholder):
        # 如果有待发送文件，合并发送
        if st.session_state.pending_file:
            full_prompt = format_file_message(st.session_state.pending_file, prompt)
            st.session_state.pending_file = None  # 清除已发送文件
        else:
            full_prompt = prompt
        
        with st.chat_message("user"):
            st.markdown(prompt if not st.session_state.pending_file else f"📎 [带文件] {prompt}")
        
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                reply, err = call_api(session, full_prompt)
                if err:
                    st.error(err)
                else:
                    st.markdown(reply)
                    st.rerun()
    
    # 底部操作
    st.divider()
    c1, c2 = st.columns([2, 4])
    with c1:
        if st.button("🗑️ 清空"):
            mid = MODELS[session["model"]]
            session["messages"] = [{"role": "system", "content": "你是助手"}] if needs_system_role(mid) else []
            session["updated_at"] = datetime.now().isoformat()
            st.session_state.pending_file = None
            st.rerun()
    with c2:
        cnt = len([m for m in session["messages"] if m["role"] != "system"])
        st.caption(f"📊 {cnt} 条消息")
