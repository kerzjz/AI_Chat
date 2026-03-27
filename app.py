import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid
import os
import zipfile
import io

# 页面配置 - 必须在最前面
st.set_page_config(
    page_title="Kzz AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 配置 ==========
TOKEN = st.secrets.get("TOKEN", os.getenv("TOKEN", ""))
ACCOUNT_ID = st.secrets.get("ACCOUNT_ID", os.getenv("ACCOUNT_ID", ""))

# 检查配置
if not TOKEN or not ACCOUNT_ID:
    st.error("⚠️ 请在 Secrets 中配置 TOKEN 和 ACCOUNT_ID")
    st.stop()

# 完整模型列表
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

MODEL_CATEGORIES = {
    "🦙 Llama": ["Llama 4 Scout", "Llama 3.3 70B", "Llama 3.3 70B Fast", "Llama 3.2 11B Vision", 
                "Llama 3.2 3B", "Llama 3.2 1B", "Llama 3.1 8B", "Llama 3.1 8B AWQ", 
                "Llama 3.1 8B FP8", "Llama 3 8B", "Llama 3 8B AWQ", "Llama 2 7B FP16", 
                "Llama 2 7B INT8", "Llama Guard 3 8B"],
    "🌙 Kimi": ["Kimi K2.5"],
    "🤖 OpenAI": ["GPT-OSS 20B", "GPT-OSS 120B"],
    "🔷 Gemma": ["Gemma 3 12B", "Gemma 7B", "Gemma 2B", "Gemma 7B HF"],
    "🐉 Qwen": ["Qwen3 30B", "Qwen QWQ 32B", "Qwen2.5 Coder 32B", "Qwen1.5 14B", "Qwen3 Embedding"],
    "⚡ Other": ["DeepSeek R1", "Mistral 7B", "Phi-2", "TinyLlama", "GLM-4.7 Flash", "Llama-2-7B LoRA"]
}

MODEL_DESC = {
    "@cf/meta/llama-4-scout-17b-16e-instruct": "Llama 4最新架构",
    "@cf/meta/llama-3.3-70b-instruct": "Meta官方推荐",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast": "量化加速版",
    "@cf/meta/llama-3.2-11b-vision-instruct": "支持图片理解",
    "@cf/meta/llama-3.2-3b-instruct": "轻量快速",
    "@cf/meta/llama-3.2-1b-instruct": "极速轻量",
    "@cf/meta/llama-3.1-8b-instruct": "均衡快速",
    "@cf/meta/llama-3.1-8b-instruct-awq": "AWQ量化",
    "@cf/meta/llama-3.1-8b-instruct-fp8": "FP8量化",
    "@cf/meta/llama-3-8b-instruct": "标准版",
    "@cf/meta/llama-3-8b-instruct-awq": "AWQ量化",
    "@cf/meta/llama-2-7b-chat-fp16": "FP16精度",
    "@cf/meta/llama-2-7b-chat-int8": "INT8量化",
    "@cf/meta/llama-guard-3-8b": "安全审核",
    "@cf/moonshotai/kimi-k2.5": "长文本支持",
    "@cf/openai/gpt-oss-20b": "OpenAI 20B",
    "@cf/openai/gpt-oss-120b": "OpenAI最强",
    "@cf/google/gemma-3-12b-it": "Google最新",
    "@cf/google/gemma-7b-it-lora": "LoRA微调",
    "@cf/google/gemma-2b-it-lora": "轻量LoRA",
    "@hf/google/gemma-7b-it": "HF版本",
    "@cf/qwen/qwen3-30b-a3b-fp8": "MoE架构",
    "@cf/qwen/qwq-32b": "推理模型",
    "@cf/qwen/qwen2.5-coder-32b-instruct": "代码专用",
    "@cf/qwen/qwen1.5-14b-chat-awq": "中文优秀",
    "@cf/qwen/qwen3-embedding-0.6b": "文本嵌入",
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b": "推理强",
    "@cf/mistral/mistral-7b-instruct-v0.2": "欧洲Mistral",
    "@cf/microsoft/phi-2": "微软轻量",
    "@cf/tinyllama/tinyllama-1.1b-chat-v1.0": "极速轻量",
    "@cf/zai-org/glm-4.7-flash": "智谱中文",
    "@cf/meta-llama/llama-2-7b-chat-hf-lora": "LoRA版"
}

NO_SYSTEM_MODELS = ["llama", "deepseek", "qwen3", "mistral", "tinyllama", "qwq", "phi"]

def supports_system_role(model_name):
    model_lower = model_name.lower()
    return not any(m in model_lower for m in NO_SYSTEM_MODELS)

# ========== Session State 初始化 ==========
def init_session_state():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "editing_session" not in st.session_state:
        st.session_state.editing_session = None
    if "show_new_session" not in st.session_state:
        st.session_state.show_new_session = False
    if "user_input_processed" not in st.session_state:
        st.session_state.user_input_processed = False

    # 创建默认会话
    if not st.session_state.sessions:
        create_session("默认会话")

def create_session(name, model=None):
    session_id = str(uuid.uuid4())[:8]
    model = model or "Llama 3.3 70B"
    model_id = MODELS[model]

    messages = []
    if supports_system_role(model_id):
        messages = [{"role": "system", "content": "你是一个智能助手"}]

    st.session_state.sessions[session_id] = {
        "id": session_id,
        "name": name,
        "model": model,
        "messages": messages,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    st.session_state.current_session_id = session_id
    return session_id

def get_current_session():
    sid = st.session_state.current_session_id
    if sid and sid in st.session_state.sessions:
        return st.session_state.sessions[sid]
    if st.session_state.sessions:
        first_id = list(st.session_state.sessions.keys())[0]
        st.session_state.current_session_id = first_id
        return st.session_state.sessions[first_id]
    return None

def delete_session(session_id):
    if session_id in st.session_state.sessions:
        del st.session_state.sessions[session_id]
        if st.session_state.current_session_id == session_id:
            if st.session_state.sessions:
                st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]
            else:
                st.session_state.current_session_id = None
                create_session("默认会话")

def rename_session(session_id, new_name):
    if session_id in st.session_state.sessions:
        st.session_state.sessions[session_id]["name"] = new_name
        st.session_state.sessions[session_id]["updated_at"] = datetime.now().isoformat()

def switch_model(session_id, new_model):
    if session_id in st.session_state.sessions:
        session = st.session_state.sessions[session_id]
        old_model_id = MODELS[session["model"]]
        new_model_id = MODELS[new_model]

        session["model"] = new_model

        old_support = supports_system_role(old_model_id)
        new_support = supports_system_role(new_model_id)

        if old_support != new_support:
            if new_support:
                session["messages"] = [{"role": "system", "content": "你是一个智能助手"}]
            else:
                session["messages"] = []

        session["updated_at"] = datetime.now().isoformat()

# ========== API 调用 ==========
def get_api_url(model):
    return f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model}"

def extract_response(result):
    if not result or not result.get("success"):
        return None

    result_data = result.get("result", {})

    if isinstance(result_data, dict) and "response" in result_data:
        return result_data["response"]

    if isinstance(result_data, dict) and "choices" in result_data:
        choices = result_data["choices"]
        if choices and len(choices) > 0:
            message = choices[0].get("message", {})
            return message.get("content")

    if isinstance(result_data, str):
        return result_data

    if isinstance(result_data, dict):
        if "content" in result_data:
            return result_data["content"]
        if "text" in result_data:
            return result_data["text"]

    return str(result_data)

def call_api(session, user_input):
    try:
        model_id = MODELS[session["model"]]
        url = get_api_url(model_id)

        # 先添加用户消息到 session
        session["messages"].append({"role": "user", "content": user_input})
        session["updated_at"] = datetime.now().isoformat()

        data = json.dumps({"messages": session["messages"]}).encode("utf-8")
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
                ai_message = extract_response(result)
                if ai_message:
                    session["messages"].append({"role": "assistant", "content": ai_message})
                    session["updated_at"] = datetime.now().isoformat()
                    return ai_message, None
                else:
                    # 解析失败，移除用户消息
                    session["messages"].pop()
                    return None, "无法解析响应格式"
            else:
                # API 错误，移除用户消息
                session["messages"].pop()
                error = result.get("errors", [{}])[0].get("message", "未知错误")
                return None, f"API错误: {error}"

    except urllib.error.HTTPError as e:
        session["messages"].pop()
        error_body = e.read().decode("utf-8")
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        session["messages"].pop()
        return None, f"请求失败: {str(e)}"

# ========== 导出功能 ==========
def export_single_session(session, format_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"{session['name']}_{timestamp}"

    if format_type == "json":
        data = {
            "name": session["name"],
            "model": session["model"],
            "messages": session["messages"],
            "created_at": session["created_at"],
            "exported_at": datetime.now().isoformat()
        }
        return json.dumps(data, ensure_ascii=False, indent=2), f"{filename_base}.json"

    elif format_type == "md":
        content = f"# {session['name']}\n\n"
        content += f"- 模型: {session['model']}\n"
        content += f"- 创建: {session['created_at']}\n"
        content += f"- 导出: {datetime.now().isoformat()}\n\n"
        content += "---\n\n"

        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            role_name = "🧑 用户" if msg["role"] == "user" else "🤖 AI"
            content += f"### {role_name}\n\n{msg['content']}\n\n---\n\n"

        return content, f"{filename_base}.md"

    elif format_type == "txt":
        content = f"会话: {session['name']}\n"
        content += f"模型: {session['model']}\n"
        content += f"时间: {session['created_at']}\n"
        content += "=" * 50 + "\n\n"

        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            role_name = "[用户]" if msg["role"] == "user" else "[AI]"
            content += f"{role_name}\n{msg['content']}\n\n"

        return content, f"{filename_base}.txt"

    return None, None

def export_all_sessions(format_type):
    sessions = st.session_state.sessions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format_type == "json":
        data = {
            "export_time": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": {sid: sesh for sid, sesh in sessions.items()}
        }
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return content, f"all_sessions_{timestamp}.json", "application/json"

    elif format_type == "zip":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for session in sessions.values():
                session_data = {
                    "name": session["name"],
                    "model": session["model"],
                    "messages": session["messages"],
                    "created_at": session["created_at"],
                    "exported_at": datetime.now().isoformat()
                }
                json_content = json.dumps(session_data, ensure_ascii=False, indent=2)
                filename = f"{session['name']}_{session['id']}.json"
                zip_file.writestr(filename, json_content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f"all_sessions_{timestamp}.zip", "application/zip"

    elif format_type == "md_zip":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for session in sessions.values():
                content = f"# {session['name']}\n\n"
                content += f"- 模型: {session['model']}\n"
                content += f"- 创建: {session['created_at']}\n\n"
                content += "---\n\n"

                for msg in session["messages"]:
                    if msg["role"] == "system":
                        continue
                    role_name = "🧑 用户" if msg["role"] == "user" else "🤖 AI"
                    content += f"### {role_name}\n\n{msg['content']}\n\n---\n\n"

                filename = f"{session['name']}_{session['id']}.md"
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f"all_sessions_{timestamp}_md.zip", "application/zip"

    return None, None, None

def import_session(file_content):
    try:
        data = json.loads(file_content)

        if "sessions" in data:
            # 批量导入
            imported_count = 0
            for sid, session_data in data["sessions"].items():
                new_id = str(uuid.uuid4())[:8]
                new_session = {
                    "id": new_id,
                    "name": f"导入_{session_data.get('name', '会话')}",
                    "model": session_data.get("model", "Llama 3.3 70B"),
                    "messages": session_data.get("messages", []),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                st.session_state.sessions[new_id] = new_session
                imported_count += 1
            return True, f"成功导入 {imported_count} 个会话"
        else:
            # 单会话导入
            session_id = str(uuid.uuid4())[:8]
            new_session = {
                "id": session_id,
                "name": f"导入_{data.get('name', '会话')}",
                "model": data.get("model", "Llama 3.3 70B"),
                "messages": data.get("messages", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            st.session_state.sessions[session_id] = new_session
            st.session_state.current_session_id = session_id
            return True, "成功导入 1 个会话"

    except Exception as e:
        return False, str(e)

# ========== 侧边栏 ==========
def render_sidebar():
    with st.sidebar:
        st.title("Kzz AI")

        # 新建会话
        if st.button("➕ 新建会话", use_container_width=True, type="primary"):
            st.session_state.show_new_session = True
            st.rerun()

        if st.session_state.get("show_new_session"):
            with st.form("new_session_form", clear_on_submit=True):
                new_name = st.text_input("会话名称", placeholder=f"会话_{datetime.now().strftime('%m%d_%H%M')}")
                cols = st.columns(2)
                with cols[0]:
                    submit = st.form_submit_button("✓ 创建", use_container_width=True)
                with cols[1]:
                    cancel = st.form_submit_button("✗ 取消", use_container_width=True)

                if submit and new_name:
                    create_session(new_name)
                    st.session_state.show_new_session = False
                    st.rerun()
                elif cancel:
                    st.session_state.show_new_session = False
                    st.rerun()

        st.divider()

        # 会话列表 - 修复错位问题
        sessions_count = len(st.session_state.sessions)
        st.subheader(f"📂 历史会话 ({sessions_count}个)")

        sessions = sorted(
            st.session_state.sessions.values(),
            key=lambda x: x["updated_at"],
            reverse=True
        )

        for session in sessions:
            # 使用 container 避免错位
            with st.container():
                cols = st.columns([8, 1, 1])

                # 会话按钮
                is_current = session["id"] == st.session_state.current_session_id
                msg_count = len([m for m in session["messages"] if m["role"] != "system"])
                label = f"{session['name']} ({msg_count})"

                with cols[0]:
                    btn_type = "primary" if is_current else "secondary"
                    if st.button(label, key=f"sess_btn_{session['id']}", 
                               type=btn_type, use_container_width=True):
                        st.session_state.current_session_id = session["id"]
                        st.rerun()

                # 编辑按钮
                with cols[1]:
                    if st.button("✏️", key=f"edit_{session['id']}", help="重命名"):
                        st.session_state.editing_session = session["id"]
                        st.rerun()

                # 删除按钮
                with cols[2]:
                    if st.button("🗑️", key=f"del_{session['id']}", help="删除"):
                        if sessions_count > 1:
                            delete_session(session["id"])
                            st.rerun()
                        else:
                            st.error("至少保留一个会话")

                # 重命名表单
                if st.session_state.get("editing_session") == session["id"]:
                    with st.form(f"rename_{session['id']}"):
                        new_name = st.text_input("新名称", value=session["name"], label_visibility="collapsed")
                        r_cols = st.columns(2)
                        with r_cols[0]:
                            if st.form_submit_button("✓", use_container_width=True):
                                if new_name:
                                    rename_session(session["id"], new_name)
                                st.session_state.editing_session = None
                                st.rerun()
                        with r_cols[1]:
                            if st.form_submit_button("✗", use_container_width=True):
                                st.session_state.editing_session = None
                                st.rerun()

        st.divider()

        # 导入导出
        with st.expander("📥 导入 / 📤 导出"):
            # 导入
            st.markdown("**📥 导入会话**")
            uploaded = st.file_uploader("选择 JSON 文件", type=["json"], label_visibility="collapsed")
            if uploaded:
                try:
                    content = uploaded.read().decode("utf-8")
                    success, msg = import_session(content)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"导入失败: {msg}")
                except Exception as e:
                    st.error(f"文件读取失败: {e}")

            st.divider()

            # 导出当前
            current = get_current_session()
            if current:
                st.markdown("**📤 导出当前**")
                fmt = st.selectbox("格式", ["JSON", "Markdown", "TXT"], key="single_fmt")
                content, fname = export_single_session(current, fmt.lower())
                st.download_button("⬇️ 下载", content, fname, use_container_width=True)

            st.divider()

            # 导出全部
            st.markdown(f"**📦 导出全部 ({sessions_count}个)**")
            fmt_all = st.selectbox("格式", ["JSON (合并)", "ZIP (JSON)", "ZIP (Markdown)"], key="all_fmt")
            fmt_map = {"JSON (合并)": "json", "ZIP (JSON)": "zip", "ZIP (Markdown)": "md_zip"}
            content, fname, mime = export_all_sessions(fmt_map[fmt_all])
            st.download_button(f"⬇️ 下载全部", content, fname, mime, use_container_width=True)

        # 统计
        st.divider()
        total_msgs = sum(len([m for m in s["messages"] if m["role"] != "system"]) 
                        for s in st.session_state.sessions.values())
        st.caption(f"💡 {sessions_count}个会话 | {total_msgs}条消息")

# ========== 主界面 ==========
def render_main():
    session = get_current_session()

    if not session:
        st.error("⚠️ 没有活动会话")
        return

    # 顶部栏
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.header(f"💬 {session['name']}")

    with col2:
        # 模型选择器（扁平化列表避免嵌套问题）
        current_model = session["model"]

        # 创建带分组的选项列表
        options = []
        option_labels = {}
        for cat, models in MODEL_CATEGORIES.items():
            for m in models:
                label = f"{cat} › {m}"
                options.append(m)  # 实际值
                option_labels[m] = label  # 显示标签

        selected = st.selectbox(
            "模型",
            options,
            format_func=lambda x: option_labels.get(x, x),
            index=options.index(current_model) if current_model in options else 0,
            label_visibility="collapsed"
        )

        if selected != current_model:
            switch_model(session["id"], selected)
            st.rerun()

    with col3:
        model_id = MODELS.get(session["model"], "")
        desc = MODEL_DESC.get(model_id, "")[:15]
        st.caption(desc)

    # 消息显示区域
    for msg in session["messages"]:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 输入框 - 修复不显示问题
    user_input = st.chat_input("输入消息...", key="chat_input")

    if user_input and user_input.strip():
        # 立即显示用户消息
        with st.chat_message("user"):
            st.markdown(user_input)

        # 调用 API
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response, error = call_api(session, user_input.strip())

                if error:
                    st.error(f"❌ {error}")
                else:
                    st.markdown(response)
                    # 成功后再 rerun 刷新界面
                    st.rerun()

    # 底部操作
    st.divider()
    cols = st.columns([2, 2, 6])

    with cols[0]:
        if st.button("🗑️ 清空对话", use_container_width=True):
            model_id = MODELS[session["model"]]
            if supports_system_role(model_id):
                session["messages"] = [{"role": "system", "content": "你是一个智能助手"}]
            else:
                session["messages"] = []
            session["updated_at"] = datetime.now().isoformat()
            st.rerun()

    with cols[1]:
        msg_count = len([m for m in session["messages"] if m["role"] != "system"])
        st.caption(f"📊 {msg_count} 条消息")

# ========== 主程序 ==========
def main():
    init_session_state()
    render_sidebar()
    render_main()

if __name__ == "__main__":
    main()
