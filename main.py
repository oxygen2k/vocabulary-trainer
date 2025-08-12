import json
import csv 
import random
import datetime 
import streamlit as st

#HILFSFUNKTIONEN

#JSON einlesen
def get_vocabulary(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            vocabulary = json.load(file)
            for vocab in vocabulary:
                if "mode" not in vocab:
                    vocab["mode"] = "learn"
                    vocab["level"] = 0
                    vocab["next_due"] = datetime.date.today().isoformat()
            return vocabulary 
    except FileNotFoundError:
        return []
    
#JSON speichern
def save_vocabulary(file_path, vocabulary):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(vocabulary, file, ensure_ascii=False, indent=4)

#Intervall-Berechnung
def calculate_next_due(level):
    today = datetime.date.today()
    intervals = [1, 2, 4, 7, 14, 30]
    interval_days = intervals[min(level, len(intervals) - 1)]
    return (today + datetime.timedelta(days=interval_days)).isoformat()

#----------
#UI START
#----------
st.set_page_config(page_title="Vokabeltrainer", layout="centered")
st.title("Vokabeltrainer")

#Sprache auswählen
language_display = {
    "Deutsch-Englisch": ("de-en", "english"),
    "Deutsch-Französisch": ("de-fr", "french"),
    "Deutsch-Spanisch": ("de-es", "spanish")
}
choose_language = st.sidebar.selectbox("Sprache wählen", list(language_display.keys()))
language, foreign_key = language_display[choose_language] 
file_path = f"{language}.json"

#Modus wählen
mode = st.sidebar.radio("Modus wählen", ["Lernmodus", "Prüfungsmodus", "Neue Vokabel hinzufügen", "Vokabeln aus CSV importieren"])
vocabulary = get_vocabulary(file_path)

#Vokabeln hinzufügen (json)
if mode == "Neue Vokabel hinzufügen":
    german = st.text_input("Deutsches Wort:")
    foreign_word = st.text_input(f"{foreign_key.capitalize()} Wort:")
    if st.button("Hinzufügen"):
        if any(vocab["german"].lower() == german.lower() for vocab in vocabulary):
            st.warning(f"'{german}' existiert bereits.")
        else:
            vocabulary.append({
                "german": german, 
                foreign_key: foreign_word,
                "level": 0,
                "mode": "learn",
            "next_due": datetime.date.today().isoformat()
            })
        save_vocabulary(file_path, vocabulary)
        st.success(f"Vokabel '{german}' - '{foreign_word}' wurde hinzugefügt.")

#Vokabeln hinzufügen via CSV
elif mode == "Vokabeln aus CSV importieren":
    uploaded = st.file_uploader("CSV-Datei hochladen", type="csv")
    if uploaded:
        reader = csv.reader(uploaded.read().decode("utf-8").splitlines(), delimiter=";")
        added = 0 
        for row in reader:
            german, foreign_word = row
            if any(vocab["german"].lower() == german.lower() for vocab in vocabulary): 
                continue
            vocabulary.append({
                "german": german,
                foreign_key: foreign_word,
                "level": 0,
                "mode": "learn",
                "next_due": datetime.date.today().isoformat()
            })
            added += 1
        save_vocabulary(file_path, vocabulary)
        st.success(f"Vokabeln wurden erfolgreich importiert.")

#Lernmodus
elif mode == "Lernmodus":
    learn_vocab = [vocab for vocab in vocabulary if vocab.get("mode") == "learn"]
    if not learn_vocab:
        st.info("Keine Vokabeln im Lernmodus.")
    else:
        random.shuffle(learn_vocab)
        for vocab in learn_vocab:
            with st.form(key=vocab["german"]):
                st.write(f"**Was heißt:** {vocab['german']}")
                show  = st.form_submit_button("Lösung anzeigen")
                if show:
                    st.write(f"Antwort: {vocab[foreign_key]}")
                    feedback = st.radio("Wusstes Du's?", ["Ja", "Nein"], horizontal=True, key=f"fb_{vocab['german']}")
                    if feedback == "Ja":
                        vocab["level"] += 1
                        vocab["mode"] = "test"
                        vocab["next_due"] = calculate_next_due(vocab["level"])
                    else:
                        vocab["level"] = 0
                        vocab["next_due"] = calculate_next_due(0)
                    save_vocabulary(file_path, vocabulary)

#Prüfungsmodus
elif mode == "Prüfungsmodus":
    today = datetime.date.today()
    due_vocab = [v for v in vocabulary if  v.get("mode") == "test" and datetime.date.fromisoformat(v["next_due"]) <= today]
    if not due_vocab:
        st.info("Keine Vokabeln sind heute fällig. Übe erst im Lernmodus.")
    else:
        random.shuffle(due_vocab)
        for vocab in due_vocab:
            answer = st.text_input(f"Was heißt: {vocab['german']}?", key=f"q_{vocab['german']}")
            if st.button(f"Antwort prüfen: {vocab['german']}"):
                if answer.lower() == vocab[foreign_key].lower():
                    st.success("Richtig!")
                    vocab["level"] += 1
                else:
                    st.error(f"Falsch. Richtige Antwort: {vocab[foreign_key]}")
                    if vocab["level"] > 0:
                        vocab["level"] -= 1
                    else:
                        vocab["mode"] = "learn"
                vocab["next_due"] = calculate_next_due(vocab["level"])
                save_vocabulary(file_path, vocabulary)