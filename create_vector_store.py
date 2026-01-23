# create_vector_store.py
from admin_backend import update_vector_store_from_faqs

if __name__ == "__main__":
    print("Building vector store from data/faqs.json ...")
    update_vector_store_from_faqs()
    print("Vector store created at vector_store/faiss_index")
