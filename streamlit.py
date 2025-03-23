# Libraries 
import streamlit as st # Web Interface
import requests # HTTP Requests to FastAPI
import json # Json Data Handling
import base64   # For encoding and decoding the audio


# Streamlit UI 
st.markdown('<div class="trendy-title">NewsPulse Sentiment Analyzer</div>', unsafe_allow_html=True)

st.markdown("""
    <style>
    .trendy-title {
        color: black;
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        text-shadow: 1px 1px 2px #000000;
        margin-bottom: 10px;
    }
    .black-subtext {
        color: black;
        font-size: 18px;
        text-align: center;
        margin-bottom: 20px;
    }
    .stApp {
        background-color: #00CED1;  /* Turquoise background */
    }
    .stApp > div {
        background: rgba(255, 255, 255, 0.3);  /* Semi-transparent white overlay */
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    <div class="black-subtext">Enter a company name to analyze news sentiment and hear a Hindi summary.</div>
    """, unsafe_allow_html=True)


# User input
company = st.text_input("Company Name", "e.g., Tata Motors")

# Analyze the input with provided logic
if st.button("Analyze"):
    if company:
        with st.spinner("Fetching and analyzing news..."):
            # Call FastAPI backend
            try:
                fastapi_url = f"http://localhost:8000/analyze/{company}" # FastAPI endpoint URL
                response = requests.get(fastapi_url, timeout=120)  # GET request with 120s timeout
                response.raise_for_status() # HTTP status 
                response_data = response.json() # json response parsing

                # JSON data and audio Extraction
                data = json.loads(response_data["data"])  # Parse the JSON string
                en_audio_bytes = bytes.fromhex(response_data["audio_english"])  # Convert hex back to bytes
                hi_audio_bytes = bytes.fromhex(response_data["audio_hindi"])    # Convert hex back to bytes

                # Display JSON output first
                st.subheader("JSON Output")
                st.json(data)

                # Download JSON button
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"{company}_sentiment_analysis.json",
                    mime="application/json"
                )

                # Table Summary
                st.subheader("News Articles and Sentiment")
                st.table(data["articles"])

                # Overall Summary
                st.write("**Comparative Analysis:**", data["summary"]["text"])
                st.write("**Hindi Summary:**", data["summary"]["hindi_text"])

                # Output Audio
                st.write("**English Audio:**")
                st.audio(en_audio_bytes, format="audio/mp3")

                st.write("**Hindi Audio:**")
                st.audio(hi_audio_bytes, format="audio/mp3")

            # Provides network-related errors
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the backend: {e}")
            # Json - related errors
            except json.JSONDecodeError:
                st.error("Error decoding response from the backend.")
            #U Unknown errors
            except Exception as e:
                st.error(f"Unexpected error: {e}")
    # if input not provides
    else:
        st.warning("Please enter a company name.")

# Footer
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: black;
        text-align: right;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        Design & Developed by Sowbarnika
    </div>
    """, unsafe_allow_html=True)