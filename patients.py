# from supabase_client import supabase
# import uuid

# def create_patient(name, sex, age):
#     patient_id = str(uuid.uuid4())
#     supabase.table("patients").insert({
#         "id": patient_id,
#         "name": name,
#         "sex": sex,
#         "age": age
#     }).execute()
#     return patient_id


# def get_patient(patient_id):
#     return supabase.table("patients").select("*").eq("id", patient_id).execute().data[0]


# def list_patients():
#     return supabase.table("patients").select("*").execute().data
