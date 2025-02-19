import streamlit as st
import time

def main():
    st.set_page_config(page_title="AI Chatbot", layout="wide")
    
    # Top Navigation Bar
    st.markdown(
        """
        <style>
            .top-bar {
                background-color: #f8f9fa;
                padding: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #dee2e6;
            }
            .top-bar .logo { font-size: 20px; font-weight: bold; }
            .top-bar .options { font-size: 14px; }
            .sidebar .stButton > button { width: 100%; }
        </style>
        <div class='top-bar'>
            <div class='logo'>IBM WatsonX Chatbot Clone</div>
            <div class='options'>
                <button>Upgrade</button>
                <button>Deploy</button>
                <button>New Prompt</button>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Sidebar for chat history
    with st.sidebar:
        st.header("History")
        st.button("Now: Llama-3-70b-instruct")
        st.button("12:29 PM: Granite-3-8b-instruct")
        st.write("---")
        st.write("Previous Chats")
        
    # Chat Area
    st.markdown("""<div style='padding: 10px; height: 500px; overflow-y: scroll; border: 1px solid #ccc;'>""", unsafe_allow_html=True)
    st.markdown("### Element-wise Addition")
    st.code("""
    result = array1 + array2
    print(result) # Output: [5 7 9]
    """, language='python')
    
    st.markdown("### Matrix Multiplication")
    st.code("""
    array1 = np.array([[1, 2], [3, 4]])
    array2 = np.array([[5, 6], [7, 8]])
    result = array1 @ array2
    print(result)
    """, language='python')
    
    st.markdown("### Output:")
    st.code("""
    [[19 22]
     [43 50]]
    """, language='python')
    
    st.markdown("### Calculate the Mean of an Array")
    st.code("""
    array = np.array([1, 2, 3, 4, 5])
    mean = np.mean(array)
    print(mean) # Output: 3.0
    """, language='python')
    
    st.markdown("""</div>""", unsafe_allow_html=True)
    
    # User Input Box
    user_input = st.text_input("Type something...")
    if user_input:
        st.write("User:", user_input)
        time.sleep(1)
        st.write("Chatbot: Processing...")

if __name__ == "__main__":
    main()
