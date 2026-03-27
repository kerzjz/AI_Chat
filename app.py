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
    "Llama 4 Scout": "@cf/meta/llama-4-scout-17b-16e-instruct",
    "Llama 3.3 70B": "@cf/meta/llama-3.3-70b-instruct",
    "Llama 3.3 70B Fast": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "Llama 3.2 11B Vision": "@cf/meta/llama-3.2-11b-vision-instruct",
    "Llama 3.2 3B": "@cf/meta/llama-3.2-3b-instruct",
    "Llama 3.2 1B": "@cf/meta/llama-3.2-1b-instruct",
    "Llama 3.1 8B": "@cf/meta/llama-3.1-8b-instruct",
    "Llama 3.1 8B AWQ": "@cf/meta/llama-3.1-8b-instruct-awq",
    "Llama 3.1 8B FP8": "@cf/meta/llama-3.1-8b-instruct-fp8",
    "Llama 3 8B": "@cf/meta/llama-3-8b-instruct",
    "Llama 3 8B AWQ": "@cf/meta/llama-3-8b-instruct-awq",
    "Llama 2 7B FP16": "@cf/meta/llama-2-7b-chat-fp16",
    "Llama 2 7B INT8": "@cf/meta/llama-2-7b-chat-int8",
    "Llama Guard 3 8B": "@cf/meta/llama-guard-3-8b",
    "Kimi K2.5": "@cf/moonshotai/kimi-k2.5",
    "GPT-OSS 20B": "@cf/openai/gpt-oss-20b",
    "GPT-OSS 120B": "@cf/openai/gpt-oss-120b",
    "Gemma 3 12B": "@cf/google/gemma-3-12b-it",
    "Gemma 7B": "@cf/google/gemma-7b-it-lora",
    "Gemma 2B": "@cf/google/gemma-2b-it-lora",
    "Gemma 7B HF": "@hf/google/gemma-7b-it",
    "Qwen3 30B": "@cf/qwen/qwen3-30b-a3b-fp8",
    "Qwen3 Embedding": "@cf/qwen/qwen3-embedding-0.6b",
    "Qwen QWQ 32B": "@cf/qwen/qwq-32b",
    "Qwen2.5 Coder 32B": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "Qwen1.5 14B": "@cf/qwen/qwen1.5-14b-chat-awq",
    "DeepSeek R1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "Mistral 7B": "@cf/mistral/mistral-7b-instruct-v0.2",
    "Phi-2": "@cf/microsoft/phi-2",
    "TinyLlama": "@cf/tinyllama/tinyllama-1.1b-chat-v1.0",
    "Llama-2-7B LoRA": "@cf/meta-llama/llama-2-7b-chat-hf-lora",
    "GLM-4.7 Flash": "@cf/zai-org/glm-4.7-flash"
}

# 检测是否需要 system 角色
def needs_system_role(model_id):
    """检查模型是否需要 system 角色（Llama/Mistral/DeepSeek/Qwen3 不需要）"""
    lower = model_id.lower()
    no_system = ["llama", "mistral", "deepseek", "qwen3", "qwq", "tinyllama", "phi"]
    return not any(x in lower for x in no_system)

# ========== Session State ==========
def init_session():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None

    if not st.session_state.sessions:
        create_session("默认会话")

def create_session(name, model="Llama 3.3 70B"):
    sid = str(uuid.uuid4())[:8]
    model_id = MODELS[model]

    # 关键：根据模型决定是否添加 system 角色
    if needs_system_role(model_id):
        messages = [{"role": "system", "content": "你是一个智能助手"}]
    else:
        messages = []

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

def switch_model(sid, new_model):
    """切换模型，必要时重置消息格式"""
    if sid not in st.session_state.sessions:
        return

    session = st.session_state.sessions[sid]
    old_model_id = MODELS[session["model"]]
    new_model_id = MODELS[new_model]

    old_needs_system = needs_system_role(old_model_id)
    new_needs_system = needs_system_role(new_model_id)

    session["model"] = new_model

    # 如果 system 角色需求变化，重置消息
    if old_needs_system != new_needs_system:
        if new_needs_system:
            session["messages"] = [{"role": "system", "content": "你是一个智能助手"}]
        else:
            session["messages"] = []
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

# ========== API 调用 ==========
def get_api_url(model_id):
    return f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model_id}"

def extract_response(result):
    if not result or not result.get("success"):
        return None

    result_data = result.get("result", {})

    # 格式 1: result.response
    if isinstance(result_data, dict) and "response" in result_data:
        return result_data["response"]

    # 格式 2: OpenAI 格式 choices[0].message.content
    if isinstance(result_data, dict) and "choices" in result_data:
        choices = result_data["choices"]
        if choices and len(choices) > 0:
            msg = choices[0].get("message", {})
            return msg.get("content")

    # 格式 3: 直接字符串
    if isinstance(result_data, str):
        return result_data

    return str(result_data)

def call_api(session, user_input):
    """调用 API，处理 Llama 等特殊格式"""
    try:
        model_id = MODELS[session["model"]]
        url = get_api_url(model_id)

        # 添加用户消息
        session["messages"].append({"role": "user", "content": user_input})
        session["updated_at"] = datetime.now().isoformat()

        # 构建请求体
        payload = {"messages": session["messages"]}

        # 调试信息
        # st.write(f"调试 - 发送消息数: {len(session['messages'])}")

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

            if result.get("success"):
                reply = extract_response(result)
                if reply:
                    session["messages"].append({"role": "assistant", "content": reply})
                    session["updated_at"] = datetime.now().isoformat()
                    return reply, None
                else:
                    session["messages"].pop()
                    return None, "无法解析响应"
            else:
                session["messages"].pop()
                error = result.get("errors", [{}])[0].get("message", "未知错误")
                return None, f"API错误: {error}"

    except urllib.error.HTTPError as e:
        session["messages"].pop()
        error_body = e.read().decode("utf-8")
        return None, f"HTTP {e.code}: {e.reason}\n{error_body[:200]}"
    except Exception as e:
        session["messages"].pop()
        return None, f"请求异常: {str(e)}"

# ========== 导出功能 ==========
def export_session(session, fmt):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = session["name"]

    if fmt == "json":
        data = {
            "name": name,
            "model": session["model"],
            "messages": session["messages"],
            "created_at": session["created_at"]
        }
        return json.dumps(data, ensure_ascii=False, indent=2), f"{name}_{ts}.json"

    elif fmt == "md":
        content = f"# {name}\n\n"
        content += f"模型: {session['model']}\n\n"
        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            role = "🧑 用户" if msg["role"] == "user" else "🤖 AI"
            content += f"### {role}\n\n{msg['content']}\n\n---\n\n"
        return content, f"{name}_{ts}.md"

    else:  # txt
        content = f"会话: {name}\n模型: {session['model']}\n\n"
        for msg in session["messages"]:
            if msg["role"] != "system":
                content += f"[{msg['role']}]\n{msg['content']}\n\n"
        return content, f"{name}_{ts}.txt"

def export_all(fmt):
    sessions = st.session_state.sessions
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        data = {
            "export_time": datetime.now().isoformat(),
            "sessions": {sid: s for sid, s in sessions.items()}
        }
        return json.dumps(data, ensure_ascii=False, indent=2), f"all_{ts}.json", "application/json"

    elif fmt == "zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            for s in sessions.values():
                data = json.dumps({
                    "name": s["name"], "model": s["model"],
                    "messages": s["messages"]
                }, ensure_ascii=False, indent=2)
                zf.writestr(f"{s['name']}_{s['id']}.json", data)
        buf.seek(0)
        return buf.getvalue(), f"all_{ts}.zip", "application/zip"

    else:  # md_zip
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            for s in sessions.values():
                content = f"# {s['name']}\n\n"
                for msg in s["messages"]:
                    if msg["role"] != "system":
                        role = "用户" if msg["role"] == "user" else "AI"
                        content += f"## {role}\n\n{msg['content']}\n\n"
                zf.writestr(f"{s['name']}_{s['id']}.md", content)
        buf.seek(0)
        return buf.getvalue(), f"all_{ts}_md.zip", "application/zip"

def import_session(content):
    try:
        data = json.loads(content)

        if "sessions" in data:
            # 批量导入
            count = 0
            for sid, sdata in data["sessions"].items():
                new_id = str(uuid.uuid4())[:8]
                st.session_state.sessions[new_id] = {
                    "id": new_id,
                    "name": f"导入_{sdata.get('name', '会话')}",
                    "model": sdata.get("model", "Llama 3.3 70B"),
                    "messages": sdata.get("messages", []),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                count += 1
            return True, f"导入 {count} 个会话"
        else:
            # 单会话
            sid = str(uuid.uuid4())[:8]
            st.session_state.sessions[sid] = {
                "id": sid,
                "name": f"导入_{data.get('name', '会话')}",
                "model": data.get("model", "Llama 3.3 70B"),
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
    st.subheader(f"📂 历史会话 ({len(st.session_state.sessions)}个)")

    # 会话列表
    for s in sorted(st.session_state.sessions.values(), key=lambda x: x["updated_at"], reverse=True):
        with st.container():
            c1, c2, c3 = st.columns([8, 1, 1])

            with c1:
                msg_count = len([m for m in s["messages"] if m["role"] != "system"])
                label = f"{s['name']} ({msg_count})"
                is_current = s["id"] == st.session_state.current_id

                if st.button(label, key=f"btn_{s['id']}",
                           type="primary" if is_current else "secondary",
                           use_container_width=True):
                    st.session_state.current_id = s["id"]
                    st.rerun()

            with c2:
                if st.button("/", key=f"ren_{s['id']}", help="重命名"):
                    st.session_state[f"editing_{s['id']}"] = True
                    st.rerun()

            with c3:
                if st.button("X", key=f"del_{s['id']}", help="删除"):
                    if len(st.session_state.sessions) > 1:
                        delete_session(s["id"])
                        st.rerun()
                    else:
                        st.error("至少保留一个")

            # 重命名输入
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
        # 导入
        st.markdown("**📥 导入**")
        uploaded = st.file_uploader("选 JSON 文件", type=["json"], label_visibility="collapsed")
        if uploaded:
            ok, msg = import_session(uploaded.read().decode("utf-8"))
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        st.divider()

        # 导出当前
        if session:
            st.markdown("**📤 导出当前**")
            fmt = st.selectbox("格式", ["JSON", "Markdown", "TXT"], key="fmt_single")
            content, fname = export_session(session, fmt.lower())
            st.download_button("⬇️ 下载", content, fname, use_container_width=True)

        st.divider()

        # 导出全部
        st.markdown(f"**📦 导出全部 ({len(st.session_state.sessions)}个)**")
        fmt_all = st.selectbox("格式", ["JSON", "ZIP", "MD ZIP"], key="fmt_all")
        fmt_map = {"JSON": "json", "ZIP": "zip", "MD ZIP": "md_zip"}
        content, fname, mime = export_all(fmt_map[fmt_all])
        st.download_button("⬇️ 下载全部", content, fname, mime, use_container_width=True)

    # 统计
    st.divider()
    total = sum(len([m for m in s["messages"] if m["role"] != "system"]) 
                for s in st.session_state.sessions.values())
    st.caption(f"💡 {len(st.session_state.sessions)}会话 | {total}消息")

# 主界面
if session:
    # 头部
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.header(f"💬 {session['name']}")
    with c2:
        # 模型选择
        current = session["model"]
        options = list(MODELS.keys())
        selected = st.selectbox("模型", options, index=options.index(current), label_visibility="collapsed")
        if selected != current:
            switch_model(session["id"], selected)
            st.rerun()
    with c3:
        st.caption(MODELS[session["model"]].split("/")[-1][:20])

    # 显示消息
    for msg in session["messages"]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 输入
    if prompt := st.chat_input("输入消息..."):
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用 API
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                reply, error = call_api(session, prompt)
                if error:
                    st.error(error)
                else:
                    st.markdown(reply)
                    st.rerun()

    # 底部
    st.divider()
    c1, c2 = st.columns([2, 4])
    with c1:
        if st.button("🗑️ 清空对话"):
            model_id = MODELS[session["model"]]
            if needs_system_role(model_id):
                session["messages"] = [{"role": "system", "content": "你是助手"}]
            else:
                session["messages"] = []
            session["updated_at"] = datetime.now().isoformat()
            st.rerun()
    with c2:
        count = len([m for m in session["messages"] if m["role"] != "system"])
        st.caption(f"📊 {count} 条消息")
