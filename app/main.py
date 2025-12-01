import streamlit as st

import pandas as pd

import psycopg2

import os

from huggingface_hub import InferenceClient



# --- 1. Configuration ---

st.set_page_config(page_title="Assistant Qualité de l'Air")



FLAG_URL = "https://upload.wikimedia.org/wikipedia/en/c/c3/Flag_of_France.svg"



# Création de colonnes pour aligner l'image et le titre

col_drapeau, col_titre = st.columns([1, 7]) # Le '1' est la largeur de la colonne drapeau



with col_drapeau:

    # Affichage de l'image du drapeau

    st.image(FLAG_URL, width=80)



with col_titre:

    # Titre principal à côté

    st.title("Assistant Qualité de l'Air")



# --- 2. Token & Client ---

hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not hf_token:

    hf_token = st.sidebar.text_input("Token Hugging Face", type="password")

    if not hf_token:

        st.stop()



repo_id = "Qwen/Qwen2.5-7B-Instruct"

try:

    client = InferenceClient(token=hf_token)

except Exception as e:

    st.error(f"Erreur Client : {e}")

    st.stop()



# --- 3. Connexion DB ---

def get_db_connection():

    except Exception as e:

        return None



# --- 4. Historique ---

if "messages" not in st.session_state:

    st.session_state.messages = []



for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if "dataframe" in message:

            st.dataframe(message["dataframe"])



# --- 5. Logique Principale ---

if prompt := st.chat_input("Ex: Quelle est la ville la moins polluée maintenant ?"):

    

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):

        st.markdown(prompt)



    with st.chat_message("assistant"):

        with st.spinner("Analyse en cours..."):

            try:

                # --- ÉTAPE 1 : GÉNÉRATION SQL ---

                messages_sql = [

                    {

                        "role": "system",

                        "content": """You are a PostgreSQL expert. Return ONLY the SQL query.

Schema: raw_measurements(city, latitude, longitude, timestamp, pm10, pm2_5, no2, o3, so2, aqi).



CRITICAL RULES:

1. Return ONLY the valid SQL query. No markdown.



2. **TIME HANDLING ("Maintenant" / "Now")**:

   - If user says "Maintenant", "Actuel", "Now", "Latest":

   - You MUST filter by the absolute latest timestamp using a subquery: 

   - `WHERE timestamp = (SELECT MAX(timestamp) FROM raw_measurements)`

   - Do NOT just use CURRENT_DATE.



3. **SORTING LOGIC ("Plus" vs "Moins")**:

   - **High/Bad Pollution**: Words like "Plus", "Pire", "Max", "Haute", "Most":

     -> USE `ORDER BY [column] DESC` (Big numbers first).

   - **Low/Good Pollution**: Words like "Moins", "Mieux", "Min", "Faible", "Least", "Cleanest":

     -> USE `ORDER BY [column] ASC` (Small numbers first).



4. **AGGREGATION**:

   - When grouping by city, always use MAX(aqi) or AVG(aqi).

"""

                    },

                    {"role": "user", "content": prompt}

                ]



                # Appel au modèle pour le SQL

                response_sql = client.chat_completion(model=repo_id, messages=messages_sql, max_tokens=250, temperature=0.1)

                clean_sql = response_sql.choices[0].message.content.replace("```sql", "").replace("```", "").strip()

                

                # --- ÉTAPE 2 : EXÉCUTION ---

                conn = get_db_connection()

                df_result = None

                result_text_for_llm = "Aucun résultat trouvé dans la base de données."

                

                if conn:

                    try:

                        df_result = pd.read_sql_query(clean_sql, conn)

                        if not df_result.empty:

                            result_text_for_llm = df_result.to_string(index=False)

                    except Exception as sql_err:

                        result_text_for_llm = f"Erreur d'exécution SQL : {sql_err}"

                    finally:

                        conn.close()



                # --- ÉTAPE 3 : RÉPONSE NATURELLE ---

                messages_final = [

                    {

                        "role": "system",

                        "content": "Tu es un assistant expert en qualité de l'air. Tu reçois une question et une donnée brute. Formule une réponse directe et naturelle en français. Ne répète pas la question. Ne dis pas 'Voici le résultat'."

                    },

                    {

                        "role": "user", 

                        "content": f"Question Utilisateur: {prompt}\nDonnées SQL trouvées: {result_text_for_llm}\n\nFais une phrase affirmative simple (ex: 'Actuellement, la ville la moins polluée est X avec un score de Y')."

                    }

                ]

                

                response_final = client.chat_completion(model=repo_id, messages=messages_final, max_tokens=200, temperature=0.7)

                final_answer = response_final.choices[0].message.content



                # Affichage

                st.markdown(final_answer)

                

                if df_result is not None and not df_result.empty:

                    st.dataframe(df_result)



                # Sauvegarde

                msg_data = {"role": "assistant", "content": final_answer}

                if df_result is not None and not df_result.empty:

                    msg_data["dataframe"] = df_result

                

                st.session_state.messages.append(msg_data)



            except Exception as e:

                st.error("Une erreur est survenue lors du traitement.")