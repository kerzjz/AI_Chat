import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid
import os
import zipfile
import io

# 页面配置
st.set_page_config(
    page_title="Kzz AI Chat",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 配置 ==========
TOKEN = st.secrets.get("TOKEN", os.getenv("TOKEN", "your_token_here"))
ACCOUNT_ID = st.secrets.get("ACCOUNT_ID", os.getenv("ACCOUNT_ID", "your_account_id_here"))

# 完整模型列表（按类别分组）
MODELS = {
    # Llama 系列
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

    # Kimi / Moonshot
    "Kimi K2.5": "@cf/moonshotai/kimi-k2.5",

    # OpenAI
    "GPT-OSS 20B": "@cf/openai/gpt-oss-20b",
    "GPT-OSS 120B": "@cf/openai/gpt-oss-120b",

    # Google Gemma
    "Gemma 3 12B": "@cf/google/gemma-3-12b-it",
    "Gemma 7B": "@cf/google/gemma-7b-it-lora",
    "Gemma 2B": "@cf/google/gemma-2b-it-lora",
    "Gemma 7B HF": "@hf/google/gemma-7b-it",

    # Qwen 系列
    "Qwen3 30B": "@cf/qwen/qwen3-30b-a3b-fp8",
    "Qwen3 Embedding": "@cf/qwen/qwen3-embedding-0.6b",
    "Qwen QWQ 32B": "@cf/qwen/qwq-32b",
    "Qwen2.5 Coder 32B": "@cf/qwen/qwen2.5-coder-32b-instruct",
    "Qwen1.5 14B": "@cf/qwen/qwen1.5-14b-chat-awq",

    # DeepSeek
    "DeepSeek R1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",

    # Mistral
    "Mistral 7B": "@cf/mistral/mistral-7b-instruct-v0.2",

    # Microsoft
    "Phi-2": "@cf/microsoft/phi-2",

    # TinyLlama
    "TinyLlama": "@cf/tinyllama/tinyllama-1.1b-chat-v1.0",

    # LoRA 模型
    "Llama-2-7B LoRA": "@cf/meta-llama/llama-2-7b-chat-hf-lora",

    # GLM
    "GLM-4.7 Flash": "@cf/zai-org/glm-4.7-flash"
}

# 模型分类（用于下拉菜单分组）
MODEL_CATEGORIES = {
    "🦙 Llama 系列": ["Llama 4 Scout", "Llama 3.3 70B", "Llama 3.3 70B Fast", "Llama 3.2 11B Vision", 
                     "Llama 3.2 3B", "Llama 3.2 1B", "Llama 3.1 8B", "Llama 3.1 8B AWQ", 
                     "Llama 3.1 8B FP8", "Llama 3 8B", "Llama 3 8B AWQ", "Llama 2 7B FP16", 
                     "Llama 2 7B INT8", "Llama Guard 3 8B"],
    "🌙 Kimi": ["Kimi K2.5"],
    "🤖 OpenAI": ["GPT-OSS 20B", "GPT-OSS 120B"],
    "🔷 Google Gemma": ["Gemma 3 12B", "Gemma 7B", "Gemma 2B", "Gemma 7B HF"],
    "🐉 Qwen": ["Qwen3 30B", "Qwen QWQ 32B", "Qwen2.5 Coder 32B", "Qwen1.5 14B", "Qwen3 Embedding"],
    "🧠 DeepSeek": ["DeepSeek R1"],
    "⚡ 其他": ["Mistral 7B", "Phi-2", "TinyLlama", "GLM-4.7 Flash", "Llama-2-7B LoRA"]
}

# 模型描述
MODEL_DESC = {
    "@cf/meta/llama-4-scout-17b-16e-instruct": "Llama 4，最新架构",
    "@cf/meta/llama-3.3-70b-instruct": "Meta最新，推荐",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast": "快速版本，量化",
    "@cf/meta/llama-3.2-11b-vision-instruct": "支持图像理解",
    "@cf/meta/llama-3.2-3b-instruct": "轻量级",
    "@cf/meta/llama-3.2-1b-instruct": "极速轻量",
    "@cf/meta/llama-3.1-8b-instruct": "快速均衡",
    "@cf/meta/llama-3.1-8b-instruct-awq": "AWQ量化",
    "@cf/meta/llama-3.1-8b-instruct-fp8": "FP8量化",
    "@cf/meta/llama-3-8b-instruct": "Llama 3标准版",
    "@cf/meta/llama-3-8b-instruct-awq": "AWQ量化",
    "@cf/meta/llama-2-7b-chat-fp16": "FP16精度",
    "@cf/meta/llama-2-7b-chat-int8": "INT8量化",
    "@cf/meta/llama-guard-3-8b": "安全审核模型",
    "@cf/moonshotai/kimi-k2.5": "Moonshot，长上下文",
    "@cf/openai/gpt-oss-20b": "OpenAI 20B",
    "@cf/openai/gpt-oss-120b": "OpenAI 120B，最强",
    "@cf/google/gemma-3-12b-it": "Google最新",
    "@cf/google/gemma-7b-it-lora": "LoRA微调",
    "@cf/google/gemma-2b-it-lora": "轻量LoRA",
    "@hf/google/gemma-7b-it": "HuggingFace版",
    "@cf/qwen/qwen3-30b-a3b-fp8": "Qwen3 30B，MoE架构",
    "@cf/qwen/qwq-32b": "QWQ推理模型",
    "@cf/qwen/qwen2.5-coder-32b-instruct": "代码专用",
    "@cf/qwen/qwen1.5-14b-chat-awq": "中文优秀",
    "@cf/qwen/qwen3-embedding-0.6b": "文本嵌入",
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b": "推理能力强",
    "@cf/mistral/mistral-7b-instruct-v0.2": "欧洲模型",
    "@cf/microsoft/phi-2": "微软轻量模型",
    "@cf/tinyllama/tinyllama-1.1b-chat-v1.0": "极速轻量",
    "@cf/zai-org/glm-4.7-flash": "智谱GLM，中文强",
    "@cf/meta-llama/llama-2-7b-chat-hf-lora": "LoRA微调版"
}

NO_SYSTEM_MODELS = ["llama", "deepseek", "qwen3", "mistral", "tinyllama", "qwq", "phi"]

def supports_system_role(model_name):
    """检查模型是否支持 system 角色"""
    model_lower = model_name.lower()
    return not any(m in model_lower for m in NO_SYSTEM_MODELS)

# ========== 初始化 Session State ==========
def init_session_state():
    """初始化会话状态"""
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "editing_session" not in st.session_state:
        st.session_state.editing_session = None
    if "show_new_session" not in st.session_state:
        st.session_state.show_new_session = False

    # 如果没有会话，创建一个默认会话
    if not st.session_state.sessions:
        create_session("默认会话")

def create_session(name, model=None):
    """创建新会话"""
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
    """获取当前会话"""
    sid = st.session_state.current_session_id
    if sid and sid in st.session_state.sessions:
        return st.session_state.sessions[sid]
    # 如果没有当前会话，返回第一个
    if st.session_state.sessions:
        first_id = list(st.session_state.sessions.keys())[0]
        st.session_state.current_session_id = first_id
        return st.session_state.sessions[first_id]
    return None

def delete_session(session_id):
    """删除会话"""
    if session_id in st.session_state.sessions:
        del st.session_state.sessions[session_id]
        # 如果删除的是当前会话，切换到其他会话
        if st.session_state.current_session_id == session_id:
            if st.session_state.sessions:
                st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]
            else:
                st.session_state.current_session_id = None
                create_session("默认会话")

def rename_session(session_id, new_name):
    """重命名会话"""
    if session_id in st.session_state.sessions:
        st.session_state.sessions[session_id]["name"] = new_name
        st.session_state.sessions[session_id]["updated_at"] = datetime.now().isoformat()

def switch_model(session_id, new_model):
    """切换模型"""
    if session_id in st.session_state.sessions:
        session = st.session_state.sessions[session_id]
        old_model_id = MODELS[session["model"]]
        new_model_id = MODELS[new_model]

        session["model"] = new_model

        # 检查是否需要重置消息格式
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
    """提取 AI 回复"""
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
    """调用 API"""
    try:
        model_id = MODELS[session["model"]]
        url = get_api_url(model_id)

        # 添加用户消息
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
                    session["messages"].pop()
                    return None, "无法解析响应格式"
            else:
                session["messages"].pop()
                error = result.get("errors", [{}])[0].get("message", "未知错误")
                return None, f"API 错误: {error}"

    except urllib.error.HTTPError as e:
        session["messages"].pop()
        error_body = e.read().decode("utf-8")
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        session["messages"].pop()
        return None, f"请求失败: {str(e)}"

# ========== 导出功能 ==========
def export_single_session(session, format_type):
    """导出单个会话"""
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
        content += f"模型: {session['model']}\n"
        content += f"创建时间: {session['created_at']}\n"
        content += f"导出时间: {datetime.now().isoformat()}\n\n"
        content += "---\n\n"

        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            role_icon = "🧑" if msg["role"] == "user" else "🤖"
            role_name = "用户" if msg["role"] == "user" else "AI"
            content += f"## {role_icon} {role_name}\n\n{msg['content']}\n\n---\n\n"

        return content, f"{filename_base}.md"

    elif format_type == "txt":
        content = f"会话: {session['name']}\n"
        content += f"模型: {session['model']}\n"
        content += f"时间: {session['created_at']}\n"
        content += "=" * 50 + "\n\n"

        for msg in session["messages"]:
            if msg["role"] == "system":
                continue
            role_name = "用户" if msg["role"] == "user" else "AI"
            content += f"[{role_name}]\n{msg['content']}\n\n"

        return content, f"{filename_base}.txt"

    return None, None

def export_all_sessions(format_type):
    """导出所有会话"""
    sessions = st.session_state.sessions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format_type == "json":
        # 导出为单个 JSON 文件（包含所有会话）
        data = {
            "export_time": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": {sid: sesh for sid, sesh in sessions.items()}
        }
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return content, f"all_sessions_{timestamp}.json", "application/json"

    elif format_type == "zip":
        # 导出为 ZIP 文件（每个会话一个文件）
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for session in sessions.values():
                # 每个会话保存为 JSON
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
        # 导出为 ZIP 文件（Markdown 格式）
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for session in sessions.values():
                content = f"# {session['name']}\n\n"
                content += f"模型: {session['model']}\n"
                content += f"创建时间: {session['created_at']}\n\n"
                content += "---\n\n"

                for msg in session["messages"]:
                    if msg["role"] == "system":
                        continue
                    role_icon = "🧑" if msg["role"] == "user" else "🤖"
                    role_name = "用户" if msg["role"] == "user" else "AI"
                    content += f"## {role_icon} {role_name}\n\n{msg['content']}\n\n---\n\n"

                filename = f"{session['name']}_{session['id']}.md"
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f"all_sessions_{timestamp}_md.zip", "application/zip"

    return None, None, None

def import_session(file_content, file_name):
    """导入会话"""
    try:
        data = json.loads(file_content)

        # 检查是否是批量导出的文件（包含 sessions 键）
        if "sessions" in data:
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

        # 单个会话导入
        else:
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

# ========== UI 组件 ==========
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🤖 AI 聊天助手")

        # 新建会话按钮
        if st.button("➕ 新建会话", use_container_width=True):
            st.session_state.show_new_session = True

        # 新建会话输入框
        if st.session_state.get("show_new_session"):
            with st.form("new_session_form"):
                new_name = st.text_input("会话名称", value=f"会话_{datetime.now().strftime('%m%d_%H%M')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("创建", use_container_width=True):
                        if new_name:
                            create_session(new_name)
                            st.session_state.show_new_session = False
                            st.rerun()
                with col2:
                    if st.form_submit_button("取消", use_container_width=True):
                        st.session_state.show_new_session = False
                        st.rerun()

        st.divider()

        # 会话列表
        st.subheader(f"📂 历史会话 ({len(st.session_state.sessions)}个)")

        sessions = sorted(
            st.session_state.sessions.values(),
            key=lambda x: x["updated_at"],
            reverse=True
        )

        for session in sessions:
            col1, col2, col3 = st.columns([6, 1, 1])

            with col1:
                # 会话按钮
                is_current = session["id"] == st.session_state.current_session_id
                btn_type = "primary" if is_current else "secondary"

                msg_count = len([m for m in session["messages"] if m["role"] != "system"])
                label = f"{session['name']} ({msg_count})"

                if st.button(label, key=f"sess_{session['id']}", type=btn_type, use_container_width=True):
                    st.session_state.current_session_id = session["id"]
                    st.rerun()

            with col2:
                # 重命名按钮
                if st.button("✏️", key=f"rename_{session['id']}"):
                    st.session_state.editing_session = session["id"]
                    st.rerun()

            with col3:
                # 删除按钮
                if st.button("🗑️", key=f"delete_{session['id']}"):
                    if len(st.session_state.sessions) > 1:
                        delete_session(session["id"])
                        st.rerun()
                    else:
                        st.error("至少保留一个会话")

            # 重命名输入框
            if st.session_state.get("editing_session") == session["id"]:
                with st.form(f"rename_form_{session['id']}"):
                    new_name = st.text_input("新名称", value=session["name"])
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("确认"):
                            rename_session(session["id"], new_name)
                            st.session_state.editing_session = None
                            st.rerun()
                    with col2:
                        if st.form_submit_button("取消"):
                            st.session_state.editing_session = None
                            st.rerun()

        st.divider()

        # 导入导出
        with st.expander("📥 导入 / 📤 导出"):
            # 导入
            st.subheader("📥 导入会话")
            uploaded_file = st.file_uploader("选择文件 (JSON)", type=["json"])
            if uploaded_file is not None:
                content = uploaded_file.read().decode("utf-8")
                success, message = import_session(content, uploaded_file.name)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(f"导入失败: {message}")

            st.divider()

            # 导出当前会话
            st.subheader("📤 导出当前会话")
            current = get_current_session()
            if current:
                col1, col2 = st.columns(2)
                with col1:
                    export_format = st.selectbox("格式", ["Markdown", "JSON", "TXT"], key="single_export")
                with col2:
                    format_map = {"Markdown": "md", "JSON": "json", "TXT": "txt"}
                    content, filename = export_single_session(current, format_map[export_format])
                    st.download_button(
                        label="⬇️ 下载",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )

            st.divider()

            # 导出所有会话
            st.subheader("📦 导出所有会话")
            col1, col2 = st.columns(2)
            with col1:
                all_export_format = st.selectbox(
                    "格式", 
                    ["JSON (合并)", "JSON (ZIP)", "Markdown (ZIP)"], 
                    key="all_export"
                )
            with col2:
                format_map_all = {
                    "JSON (合并)": "json",
                    "JSON (ZIP)": "zip", 
                    "Markdown (ZIP)": "md_zip"
                }
                content, filename, mime_type = export_all_sessions(format_map_all[all_export_format])
                st.download_button(
                    label=f"⬇️ 下载 {len(st.session_state.sessions)}个会话",
                    data=content,
                    file_name=filename,
                    mime=mime_type,
                    use_container_width=True
                )

        # 关于
        st.divider()
        total_msgs = sum(len([m for m in s["messages"] if m["role"] != "system"]) 
                        for s in st.session_state.sessions.values())
        st.caption(f"💡 {len(st.session_state.sessions)}个会话 | {total_msgs}条消息")

def render_main():
    """渲染主界面"""
    session = get_current_session()

    if not session:
        st.error("没有活动会话")
        return

    # 顶部信息栏
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.subheader(f"💬 {session['name']}")

    with col2:
        # 模型选择（带分组）
        current_model = session["model"]

        # 找到当前模型所在的分类
        current_category = None
        for cat, models in MODEL_CATEGORIES.items():
            if current_model in models:
                current_category = cat
                break

        # 创建分组选项
        options = []
        for cat, models in MODEL_CATEGORIES.items():
            for m in models:
                options.append(f"{cat} › {m}")

        current_option = f"{current_category} › {current_model}" if current_category else current_model

        selected = st.selectbox(
            "选择模型",
            options,
            index=options.index(current_option) if current_option in options else 0,
            label_visibility="collapsed"
        )

        # 提取模型名称
        new_model = selected.split(" › ")[1] if " › " in selected else selected

        if new_model != current_model:
            switch_model(session["id"], new_model)
            st.rerun()

    with col3:
        model_id = MODELS[session["model"]]
        desc = MODEL_DESC.get(model_id, "")
        st.caption(desc[:20] + "..." if len(desc) > 20 else desc)

    # 显示消息
    chat_container = st.container()
    with chat_container:
        for msg in session["messages"]:
            if msg["role"] == "system":
                continue

            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 输入框
    if user_input := st.chat_input("输入消息..."):
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response, error = call_api(session, user_input)

                if error:
                    st.error(error)
                else:
                    st.markdown(response)

        st.rerun()

    # 底部操作栏
    cols = st.columns([1, 1, 1, 6])

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
        st.caption(f"共 {msg_count} 条消息")

# ========== 主程序 ==========
def main():
    init_session_state()
    render_sidebar()
    render_main()

if __name__ == "__main__":
    main()
