import streamlit as st
import requests
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from difflib import SequenceMatcher

# Define function to initialize the Groq model
def initialize_groq_model():
    return ChatGroq(
        temperature=0.2,  # Low temperature to minimize creative generation
        model_name="llama3-8b-8192",
        groq_api_key=st.secrets["general"]["GROQ_API_KEY"]
    )

# Simple text splitting function
def simple_text_split(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@st.cache_data(show_spinner=True)
def scrape_website(urls):
    headers = {'User-Agent': 'HawkAI/1.0 (+https://www.hartford.edu)'}
    url_contexts = {}
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = ' '.join(soup.stripped_strings)
                chunks = simple_text_split(text)
                url_contexts[url] = chunks
            else:
                st.error(f"Failed to retrieve {url}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error scraping {url}: {e}")
    return url_contexts

def find_relevant_chunks(query, contexts, token_limit=6000, prioritized_urls=None):
    prioritized_urls = prioritized_urls or []
    relevant_chunks = []
    source_urls = []
    total_tokens = 0
    query_token_count = len(query.split()) + 50
    available_tokens = token_limit - query_token_count
    prioritized_chunks_list = []
    other_chunks_list = []

    for url, chunks in contexts.items():
        for chunk in chunks:
            similarity = SequenceMatcher(None, query, chunk).ratio()
            token_count = len(chunk.split())
            if url in prioritized_urls:
                prioritized_chunks_list.append((chunk, similarity, token_count, url))
            else:
                other_chunks_list.append((chunk, similarity, token_count, url))

    prioritized_chunks_list.sort(key=lambda x: x[1], reverse=True)
    other_chunks_list.sort(key=lambda x: x[1], reverse=True)

    for chunk, _, token_count, url in prioritized_chunks_list + other_chunks_list:
        if total_tokens + token_count <= available_tokens:
            relevant_chunks.append(chunk)
            source_urls.append(url)
            total_tokens += token_count
        else:
            break

    return relevant_chunks, source_urls

def truncate_context_to_token_limit(context, max_tokens):
    words = context.split()
    if len(words) > max_tokens:
        words = words[:max_tokens]
    return " ".join(words)

def main():
    st.title("🦅 Hawk AI: Your Admissions Assistant")
    st.write("I am Howie AI, how can I assist you today?")

    # Critical URLs to scrape
    urls = [ 
        "https://www.hartford.edu/academics/graduate-professional-studies/about-graduate-and-professional-studies.aspx",
        "https://www.hartford.edu/admission/graduate-admission/default.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/graduate-studies/graduate-programs.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/graduate-studies/resources.aspx",
        "https://www.hartford.edu/admission/graduate-admission/financing-grad-education.aspx",
        "https://www.hartford.edu/about/offices-divisions/finance-administration/financial-affairs/bursar-office/tuition-fees/graduate-tuition.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/partnerships.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/programs/default.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-architecture/master-of-architecture.aspx",
        "https://www.hartford.edu/barney/academics/business-administration/dual-mba-march.aspx",
        "https://www.hartford.edu/academics/schools-colleges/art/academics/graduate/illustration.aspx",
        "https://www.hartford.edu/academics/schools-colleges/art/academics/graduate/photography.aspx",
        "https://www.hartford.edu/barney/academics/management-marketing-and-entrepreneurship/mba.aspx",
        "https://www.hartford.edu/barney/academics/accounting-and-taxation/masters-in-accounting-and-taxation.aspx",
        "https://www.hartford.edu/barney/academics/business-administration/msba.aspx",
        "https://www.hartford.edu/barney/academics/business-administration/dual-msat-mba.aspx",
        "https://www.hartford.edu/barney/academics/business-administration/mba-certificates.aspx",
        "https://www.hartford.edu/barney/academics/business-administration/dual-m-eng-mba.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/psychology/dual-msop-mba.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/communication/ma-in-integrated-communication.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/computing-sciences/ms-computer-science.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/med-in-early-childhood-elementary.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/med-elementary.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/montessori-education/med-in-education-montessori-concentration.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/med-in-special-education.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/edd-in-educational-leadership.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-education/certificate-college-teaching.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-civil-environmental-and-biomedical-engineering/meng-in-civil-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-electrical-and-computer-engineering/meng-in-electrical-and-computer-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-mechanical-aerospace-and-acoustical-engineering/meng-in-mechanical-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-civil-environmental-and-biomedical-engineering/ms-in-civil-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-electrical-and-computer-engineering/ms-in-electrical-and-computer-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/department-of-mechanical-aerospace-and-acoustical-engineering/ms-in-mechanical-engineering.aspx",
        "https://www.hartford.edu/academics/schools-colleges/ceta/academics/professional-certificates.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-nursing/msn-in-nursing.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-nursing/dnp-nursing.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-rehabilitation-sciences/ms-in-occupational-therapy.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-rehabilitation-sciences/doctor-of-physical-therapy.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-rehabilitation-sciences/physical-therapy-orthopedic-residency.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/programs/post-baccalaureate-premedical-certificate.aspx",
        "https://www.hartford.edu/academics/schools-colleges/enhp/academics/department-of-rehabilitation-sciences/ms-in-prosthetics-and-orthotics.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/psychology/accelerated-ba-ms-in-organizational-psychology.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/psychology/ms-in-organizational-psychology.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/psychology/ms-and-6th-Year-certificate-school-psychology.aspx",
        "https://www.hartford.edu/academics/schools-colleges/arts-sciences/academics/departments-and-centers/psychology/psyd-clinical-psychology/default.aspx",
        "https://www.hartford.edu/admission/partnerships/default.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/",
        "https://www.hartford.edu/academics/graduate-professional-studies/graduate-studies/information-sessions/default.aspx",
        "https://www.hartford.edu/academics/graduate-professional-studies/graduate-studies/graduate-student-experience.aspx", 

        # URLs list continues...
    ]

    # Automatic scraping on app load
    if 'contexts' not in st.session_state:
        with st.spinner("Scraping data..."):
            st.session_state['contexts'] = scrape_website(urls)

    user_query = st.text_input("Enter your query here:")
    if user_query and st.button("Answer Query"):
        try:
            relevant_chunks, source_urls = find_relevant_chunks(
                user_query, 
                st.session_state['contexts'], 
                token_limit=6000, 
                prioritized_urls=[url for url in st.session_state['contexts']]
            )

            # If no relevant chunks are found, provide a fallback response immediately
            if not relevant_chunks:
                fallback_message = (
                    "I am sorry but I am unable to answer your amazing questions. "
                    "Please reach out to Grad Study at gradstudy@hartford.edu."
                )
                st.markdown(f"**Response:** {fallback_message}")
                return

            context_to_send = "\n\n".join(relevant_chunks)
            context_to_send = truncate_context_to_token_limit(context_to_send, 6000)

            prompt = f"""
You are Hawk AI, assisting with inquiries about the University of Hartford Graduate Admissions. 
Your responses should be strictly based on the information provided through official university pages linked in our system. 
Directly answer inquiries about graduate and doctoral programs using this data available on the website. 
Do not extrapolate or create responses beyond the explicit content available. 
If a query cannot be directly answered with the provided information, politely suggest the user contact Grad Study for more comprehensive support.

Context:
{context_to_send}

User Query: {user_query}
"""
            groq_model = initialize_groq_model()
            response = groq_model.invoke(prompt, timeout=30)
            final_answer = response.content.strip()
            st.markdown(f"**Response:** {final_answer}")

        except Exception as e:
            st.error(f"Error generating response: {e}")

if __name__ == "__main__":
    main()
