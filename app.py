import streamlit as st
import json
import urllib.request
from datetime import datetime

# 配置（使用 Streamlit Secrets 存储）
TOKEN = st.secrets.get("TOKEN", "你的token")
ACCOUNT_ID = st.secrets.get("ACCOUNT_ID", "5163526b3dfa39e2c48287720bd1fcde")

# 模型列表
MODELS = {
    "Llama 3.3 70B": "@cf/meta/llama-3.3-70b-instruct",
    "Kimi K2.5": "@cf/moonshotai/kimi-k2.5",
    "DeepSeek R1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "Qwen3 30B": "@cf/qwen/qwen3-30b-a3b-fp8",
    "Llama 4 Scout": "@cf/meta/llama-4-scout-17b-16e-instruct",
}

st.set_page_config(page_title="AI Chat", page_icon="🤖")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "你是一个智能助手"}]

st.title("🤖 AI 聊天助手")
st.caption(f"当前模型: {st.session_state.get('model', 'Llama 3.3 70B')}")

# 侧边栏选择模型
with st.sidebar:
    selected_model = st.selectbox("选择模型", list(MODELS.keys()))
    st.session_state.model = selected_model
    
    if st.button("清空对话"):
        st.session_state.messages = [{"role": "system", "content": "你是一个智能助手"}]
        st.rerun()

# 显示历史消息
for msg in st.session_state.messages[1:]:  # 跳过 system prompt
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if user_input := st.chat_input("输入消息..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 调用 API
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                model_id = MODELS[selected_model]
                url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model_id}"
                
                data = json.dumps({"messages": st.session_state.messages}).encode('utf-8')
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
                    result = json.loads(response.read().decode('utf-8'))
                    
                    if result.get("success"):
                        result_data = result.get("result", {})
                        
                        # 解析响应
                        if "response" in result_data:
                            ai_response = result_data["response"]
                        elif "choices" in result_data:
                            ai_response = result_data["choices"][0]["message"]["content"]
                        else:
                            ai_response = str(result_data)
                        
                        st.markdown(ai_response)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": ai_response
                        })
                    else:
                        st.error(f"API 错误: {result.get('errors', [{}])[0].get('message', '未知错误')}")
                        
            except Exception as e:
                st.error(f"请求失败: {str(e)}")
