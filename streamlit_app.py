import streamlit as st
import requests
import os
import json
import tempfile
import base64
from PIL import Image
import io

# API Gateway endpoint (replace with your deployed endpoint)
API_ENDPOINT = os.environ.get('API_ENDPOINT', 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod')

# Set page configuration
st.set_page_config(
    page_title="Furniture Product Search",
    page_icon="🪑",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4B8BBE;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .product-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .product-meta {
        color: #64748B;
        font-size: 0.9rem;
    }
    .file-info {
        font-style: italic;
        font-size: 0.85rem;
    }
    .search-button {
        background-color: #4B8BBE;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        text-align: center;
        display: inline-block;
        font-size: 16px;
        margin: 10px 0;
    }
    .upload-section {
        background-color: #eef2ff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>Furniture Product Search</h1>", unsafe_allow_html=True)

# Create sidebar for upload and management
with st.sidebar:
    st.header("Content Management")
    
    # Product folder input
    product_folder = st.text_input("Product Folder", placeholder="e.g., modern_chairs")
    
    # File upload section
    st.subheader("Upload Files")
    uploaded_files = st.file_uploader(
        "Upload product files (images, PDFs, text, CSV)", 
        accept_multiple_files=True
    )
    
    if uploaded_files and product_folder:
        success_count = 0
        failed_count = 0
        
        for uploaded_file in uploaded_files:
            try:
                # Get file info
                file_name = uploaded_file.name
                content_type = uploaded_file.type or "application/octet-stream"
                
                # Get presigned URL
                response = requests.post(
                    f"{API_ENDPOINT}/upload-url",
                    json={
                        "product_folder": product_folder,
                        "file_name": file_name,
                        "content_type": content_type
                    }
                )
                
                if response.status_code == 200:
                    presigned_url = response.json().get("upload_url")
                    
                    # Upload file to S3 using presigned URL
                    upload_response = requests.put(
                        presigned_url,
                        data=uploaded_file.getvalue(),
                        headers={"Content-Type": content_type}
                    )
                    
                    if upload_response.status_code in (200, 204):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                st.error(f"Error uploading {uploaded_file.name}: {str(e)}")
                failed_count += 1
        
        if success_count > 0:
            st.success(f"Successfully uploaded {success_count} file(s)")
        if failed_count > 0:
            st.error(f"Failed to upload {failed_count} file(s)")
    
    # Content update button
    st.subheader("Update Index")
    update_specific = st.checkbox("Update specific product folder only")
    
    if st.button("Update Content Index"):
        with st.spinner("Updating content index..."):
            try:
                update_data = {}
                if update_specific and product_folder:
                    update_data["product_folder"] = product_folder
                
                response = requests.post(
                    f"{API_ENDPOINT}/update-content",
                    json=update_data
                )
                
                if response.status_code == 200:
                    st.success("Content index updated successfully!")
                    st.json(response.json())
                else:
                    st.error(f"Failed to update content index: {response.text}")
            except Exception as e:
                st.error(f"Error updating content index: {str(e)}")

# Main content area
st.header("Search Furniture Products")

# Search input
query = st.text_input("Enter your search query", placeholder="e.g., modern wooden chair with armrests")

# Search button
if st.button("Search", key="search_button") or query:  # Allow Enter key to trigger search
    if query:
        with st.spinner("Searching..."):
            try:
                response = requests.get(
                    f"{API_ENDPOINT}/search",
                    params={"query": query}
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    
                    if results:
                        st.write(f"Found {len(results)} matching products:")
                        
                        # Display results in a grid (3 columns)
                        cols = st.columns(3)
                        
                        for i, result in enumerate(results):
                            with cols[i % 3]:
                                st.markdown(
                                    f"""
                                    <div class="result-card">
                                        <div class="product-title">{result['product_folder'].replace('_', ' ').title()}</div>
                                        <div class="product-meta">Score: {round(result['score'], 2)}</div>
                                        <div class="file-info">File: {result['file_name']}</div>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                    else:
                        st.info("No matching products found. Try a different search query.")
                else:
                    st.error(f"Search failed: {response.text}")
            except Exception as e:
                st.error(f"Error during search: {str(e)}")
    else:
        st.warning("Please enter a search query")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748B; font-size: 0.8rem;">
        Furniture Product Search Application | Built with Streamlit, AWS Lambda, and Bedrock
    </div>
    """, 
    unsafe_allow_html=True
)
