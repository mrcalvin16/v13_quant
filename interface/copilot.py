import streamlit as st

def main():
    st.title("V13 Co-Pilot")
    st.write("Ask your trading engine questions:")

    query = st.text_input("Your question:")
    if st.button("Submit"):
        st.write(f"You asked: {query}")
        # In production, you would route this to NLP logic or strategy queries

if __name__ == "__main__":
    main()
