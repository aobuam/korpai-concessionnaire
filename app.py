import streamlit as st
import re
import openai
from openai import OpenAI
import os

openai_api_key = st.secrets["OPENAI_API_KEY"]
index_name = st.secrets["INDEX_NAME"]

# Initialisation des API
openai.api_key = openai_api_key  # Clé OpenAI
client = OpenAI(api_key=openai_api_key)  # Clé OpenAI pour le client

# Configuration de la page
st.set_page_config(
    page_title="Concessionnaire AI",  # Titre de l'onglet
    page_icon="https://www.cittoncars.co.za/wp-content/uploads/2023/06/chrysler-logo-1955.jpg",  # URL du favicon
    layout="wide",  # Mise en page large
)

# Injection des styles CSS pour cacher les éléments par défaut et ajuster l'espacement
custom_styles = """
    <style>
    #MainMenu {visibility: hidden;} /* Cacher le menu principal */
    footer {visibility: hidden;} /* Cacher le pied de page */
    header {visibility: hidden;} /* Cacher l'en-tête */
    .block-container {
        padding-top: 0rem; /* Réduire la marge supérieure */
    }
    </style>
"""
st.write(f'<div style="display:none;">{custom_styles}</div>', unsafe_allow_html=True)
st.markdown(custom_styles, unsafe_allow_html=True)



# Ajout de l'entête
def add_header():
    st.markdown(
        """
        <style>
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background-color: #fff;
            border-bottom: 1px solid #eee;
        }
        .logo {
            height: 40px;
            border-radius: 8px;
        }
        .user-icon {
            height: 40px;
            width: 40px;
            border-radius: 50%;
        }
        </style>
        <div class="header">
            <img class="logo" src="https://www.cittoncars.co.za/wp-content/uploads/2023/06/chrysler-logo-1955.jpg">
            <img class="user-icon" src="https://www.iconpacks.net/icons/2/free-user-icon-3296-thumb.png" alt="User Icon">
        </div>
        """,
        unsafe_allow_html=True,
    )


# Ajout du pied de page avec gestion conditionnelle des 330px
def add_footer(dynamic_space=True):
    space = "330px" if dynamic_space and len(st.session_state.messages) == 0 else "10px"
    st.markdown(
        f"""
        <style>
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #888;
            margin-top: {space};
            padding-top: 10px;
            border-top: 1px solid #eee;
        }}
        .footer a {{
            color: #007bff;
            text-decoration: none;
            margin: 0 8px;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        </style>
        <div class="footer">
            Powered by AbaKorp © 2024 | 
            <a href="#">Terms</a> | 
            <a href="#">Privacy</a> | 
            <a href="#">Disclaimer</a> | 
            <a href="#">Support</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Fonction principale
def discuter_avec_gpt():
    add_header()

    st.markdown(
        """
        <style>
        .title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            color: #002570;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2rem;
            color: #555;
            margin-top: -10px;
        }
        </style>
        <h1 class="title">Concessionnaire AI</h1>
        <p class="subtitle">Posez n'importe quelle question sur nos voitures.</p>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    def envoyer_question():
        user_question = st.session_state.get("user_question", "")
        if user_question.strip():
            if not st.session_state.messages or st.session_state.messages[-1].get("content") != user_question:
                st.session_state.messages.append({"role": "user", "content": user_question})

            loading_container = st.empty()
            with loading_container:
                st.markdown(
                    """
                    <div style="
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        z-index: 9999;
                        text-align: center;
                    ">
                        <img src="https://assets-v2.lottiefiles.com/a/36038e50-1178-11ee-9eeb-932b0ace7009/xwvJM3wTT2.gif" 
                            alt="Loading..." 
                            style="width: 60px; height: 60px; border-radius: 50%; display: block;">
                        <p style="font-size: 14px; color: #555;">Loading...</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            bot_response = ""
            prompt = (
                "Tu es un assisstant concessionnaire. Tu réponds aux les questions de tes clients. Tu es un demo donc ecris des choses qui sont crédibles."
                "Parle de modèles de voitures A, B, C etc. Tu parles des prix et des modes de financements"
                "Soit proffessionel, concis.\n\n"
            )

            response = client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model="gpt-3.5-turbo",
            )
            bot_response = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

        loading_container.empty()
        st.session_state["user_question"] = ""

    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(
                f"""<div style="text-align: right; background-color: #F0F7FF;
                     padding: 10px; border-radius: 10px; margin: 10px 0;">
                     {message['content']}
                     </div>""",
                unsafe_allow_html=True,
            )
        elif message["role"] == "assistant":
            st.markdown(
                f"""<div style="text-align: left; background-color: #FFFFFF; 
                     padding: 10px; border-radius: 10px; margin: 10px 0; position: relative;">
                     {message['content']}
                     </div>""",
                unsafe_allow_html=True,
            )

    with st.container():
        col1, col2 = st.columns([8, 1])
        with col1:
            st.text_input(
                label="",
                key="user_question",
                on_change=envoyer_question,
                placeholder="Ask anything...",
                label_visibility="collapsed",
            )
        with col2:
            st.button("↑", on_click=envoyer_question)

    add_footer(dynamic_space=True)


if __name__ == "__main__":
    discuter_avec_gpt()
