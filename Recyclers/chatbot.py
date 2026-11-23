import os
import time
import streamlit as st
from google import genai
from google.genai import types, errors

st.set_page_config(page_title="Chatbot", page_icon="💬")
st.title("💬 Chatbot")
st.caption("Your friendly AI buddy - ask me anything!")

# API KEY IS HERE NOW, NOT IN SIDEBAR
api_key = st.text_input("🔑 Paste your Gemini API Key here:", type="password", placeholder="Paste your key starting with AIza...")

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.info("👆 Paste your Gemini API Key above to start chatting.")
    st.stop()

st.success("Key added! You can chat now.")

SYSTEM_PROMPT = "You are a helpful and friendly chatbot assistant. Answer simply and clearly."
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

def generate_with_retry(client, contents, config, status, retries=2):
    last_error = None
    for model in MODELS:
        for attempt in range(retries):
            try:
                status.update(label=f"Trying {model} (attempt {attempt + 1})...")
                return client.models.generate_content(model=model, contents=contents, config=config)
            except errors.ServerError as e:
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2)
            except errors.ClientError as e:
                last_error = e
                break
            except Exception as e:
                last_error = e
                break
    raise RuntimeError(f"All models failed. Last error: {last_error}")

client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Chat with me... 💬"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    contents = [types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])]) for m in st.session_state.messages]
    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False) as status:
            try:
                response = generate_with_retry(client, contents, types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.7, max_output_tokens=1000), status)
                status.update(label="Done", state="complete")
                reply = response.text
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                status.update(label="Failed", state="error")
                st.error(f"Error: {e}")

if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()
