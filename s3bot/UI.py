Sure, I can help with that! By default, Streamlit places the sidebar on the left side of the page. However, you can use some custom CSS to move it to the right side. Here's a step-by-step guide:

1. **Create a CSS file**: First, create a CSS file (e.g., `styles.css`) with the following content:

    ```css
    .css-1lcbmhc {
        order: 2; /* Move the sidebar to the right */
    }
    .css-1d391kg {
        order: 1; /* Move the main content to the left */
    }
    ```

2. **Load the CSS file in your Streamlit app**: Use the `st.markdown` function to load the CSS file in your Streamlit app. Add the following code to your Streamlit script:

    ```python
    import streamlit as st

    # Load the CSS file
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Your Streamlit app code
    st.sidebar.title("Sidebar")
    st.sidebar.write("This is the sidebar content.")
    st.write("This is the main content.")
    ```

This should move the sidebar to the right side of the page. Let me know if you need any further assistance!
