import streamlit as st
import re
import openai
from openai import OpenAI
from pinecone import Pinecone
import os

openai_api_key = st.secrets["OPENAI_API_KEY"]
pinecone_api_key = st.secrets["PINECONE_API_KEY"]
index_name = st.secrets["INDEX_NAME"]

# Initialisation des API
openai.api_key = openai_api_key  # Clé OpenAI
client = OpenAI(api_key=openai_api_key)  # Clé OpenAI pour le client
pc = Pinecone(api_key=pinecone_api_key)  # Clé Pinecone
index = pc.Index(index_name)  # Nom de l'index Pinecone

# Configuration de la page
st.set_page_config(
    page_title="Concessionnaire AI",  # Titre de l'onglet
    page_icon="https://yt3.googleusercontent.com/DfdvAuF8NjXPJbIbGqIfF9u89HpNQ86tfUTlnd_gw2ajNPh1bzPcOsCgsNEgt0IBzVjaVPQ80A=s160-c-k-c0x00ffffff-no-rj",  # URL du favicon
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


# Fonction pour générer un embedding avec OpenAI
def generate_embedding(text):
    response = openai.embeddings.create(input=[text], model="text-embedding-ada-002")
    embedding = response.data[0].embedding
    return embedding


# Fonction pour effectuer une recherche sémantique
def semantic_search(query, top_k=10, score_threshold=0.75):
    try:
        query_embedding = generate_embedding(query)
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        links = []
        for i, result in enumerate(results.matches):
            if result.score < score_threshold:
                break
            metadata = result.metadata
            links.append({
                "title": metadata["title"],
                "url": metadata["url"]
            })
        return links
    except Exception as e:
        st.error(f"Erreur lors de la recherche Pinecone : {e}")
        return None


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
            <img class="logo" src="https://www.cittoncars.co.za/blog/the-evolution-of-the-chrysler-badge/">
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
        <h1 class="title">Duke AI</h1>
        <p class="subtitle">Ask any question about Duke University.</p>
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
            results = semantic_search(user_question, top_k=5, score_threshold=0.75)
            if not results:
                bot_response = "I couldn't find any relevant information. Please try another question."
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            else:
                context = "\n".join([f"[{result['title']}]({result['url']})" for result in results])
                prompt = (
                    "You are Duke AI, a virtual assistant created for Duke University. An expert in academic support, university services, "
                    "and student resources, you assist users with practical advice tailored to their needs. Your tone is approachable, "
                    "professional, and concise, reflecting the welcoming culture of Duke University.\n\n"
                    "Directives for your responses:\n"
                    "1. **Prioritize user-visible context:**\n"
                    "   - Base your responses solely on the visible context of the conversation (questions and answers exchanged with the user).\n"
                    "   - When a question is asked:\n"
                    "     - If the question mentions a specific service, resource, or topic (e.g., 'Duke Health'), ensure the response focuses only on that specific subject.\n"
                    "     - Otherwise, if the question is general (e.g., 'Tell me more'), rely on the previous visible exchanges to identify the main topic and expand on it.\n"
                    "     - Otherwise, if no relevant information or context is available, respond: "
                    "'I currently do not have enough information to answer your question. Could you clarify or provide more details?'\n\n"
                    "2. **Filter and validate information:**\n"
                    "   - When retrieving relevant resources or information, apply the following rules:\n"
                    "     - Use only information directly related to the question or the main topic from the conversation.\n"
                    "     - Exclude any resources or details that do not align with the user's question or are not specific to Duke University.\n"
                    "     - Avoid sharing unrelated or ambiguous information.\n\n"
                    "3. **Structure your responses:**\n"
                    "   - Organize your response into clear and concise points or paragraphs.\n"
                    "   - If applicable, include references to Duke University resources or links, with a brief description of each resource.\n"
                    "   - Ensure your response is easy to read and addresses the user's question comprehensively.\n\n"
                    "4. **Maintain conversational logic:**\n"
                    "   - When the user asks a follow-up question (e.g., 'Tell me more'), ensure your response builds on the specific topic from the previous exchanges.\n"
                    "   - If no clear connection to previous exchanges exists, politely ask for clarification.\n\n"
                    "5. **Tone and clarity:**\n"
                    "   - Use an approachable yet professional tone that reflects Duke University's culture.\n"
                    "   - Provide responses that are concise but rich in relevant and practical information.\n\n"
                    f"Context:\n{context}\n\n"
                    "Question: Respond directly and in detail to the question asked, following the rules above. "
                    "Focus on relevant Duke University resources, services, or advice. If applicable, include links to these resources with a brief explanation of their purpose. "
                    "If the question is ambiguous or lacks context, request clarification to better address the user's needs."
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
