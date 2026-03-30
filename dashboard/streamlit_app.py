import streamlit as st
import requests
from typing import Optional

API_URL = st.secrets.get("API_URL", "http://localhost:8000")


def login() -> Optional[str]:
    st.title("CKD-CI Clinical Decision Support")
    st.write("Please log in to continue.")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        resp = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            st.session_state["token"] = token
            st.experimental_rerun()
        else:
            st.error("Login failed")
    return st.session_state.get("token")


def single_patient_scoring(token: str):
    st.header("Single Patient Scoring")
    pid = st.text_input("Patient Identifier")
    # For demonstration, allow arbitrary JSON features input
    features_text = st.text_area("Features (JSON)", value='{}')
    if st.button("Score"):
        try:
            features = eval(features_text)
        except Exception:
            st.error("Invalid features JSON")
            return
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{API_URL}/predictions/predict", json={"patient_identifier": pid, "features": features}, headers=headers)
        if resp.status_code == 200:
            st.success("Prediction successful")
            st.json(resp.json())
        else:
            st.error(f"Prediction failed: {resp.status_code} {resp.text}")


def batch_scoring(token: str):
    st.header("Batch Scoring (CSV)")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        import pandas as pd

        df = pd.read_csv(uploaded)
        st.write(f"Uploaded {len(df)} rows")
        if st.button("Run Batch"):
            headers = {"Authorization": f"Bearer {token}"}
            items = []
            for _, row in df.iterrows():
                try:
                    features = row.to_dict()
                    pid = features.pop("patient_identifier", None) if "patient_identifier" in features else None
                    items.append({"patient_identifier": pid, "features": features})
                except Exception:
                    continue
            resp = requests.post(f"{API_URL}/predictions/batch", json={"items": items}, headers=headers)
            if resp.status_code == 200:
                st.success("Batch scoring complete")
                st.json(resp.json())
            else:
                st.error(f"Batch failed: {resp.status_code} {resp.text}")


def prediction_history(token: str):
    st.header("Prediction History")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/predictions/history", headers=headers)
    if resp.status_code == 200:
        st.write(resp.json())
    else:
        st.error("Failed to load history")


def model_info(token: str):
    st.header("Model Info")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/models/info", headers=headers)
    if resp.status_code == 200:
        st.json(resp.json())
    else:
        st.error("Failed to fetch model info")


def main():
    token = st.session_state.get("token")
    if not token:
        token = login()
        return

    menu = st.sidebar.selectbox("Menu", ["Single Patient", "Batch Scoring", "History", "Model Info", "Logout"])
    if menu == "Single Patient":
        single_patient_scoring(token)
    elif menu == "Batch Scoring":
        batch_scoring(token)
    elif menu == "History":
        prediction_history(token)
    elif menu == "Model Info":
        model_info(token)
    elif menu == "Logout":
        st.session_state.pop("token", None)
        st.experimental_rerun()


if __name__ == "__main__":
    main()
