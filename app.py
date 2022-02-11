import os ,jsonlines, csv, io, logging , json
import pandas as pd 
from flask import Flask, jsonify ,request
from google.cloud import aiplatform, storage
from google.protobuf import json_format
from flask_httpauth import HTTPBasicAuth
from io import StringIO

#details for vertex-ai
PROJECT_ID = "----------"
REGION = "us-central1"
aiplatform.init(project=PROJECT_ID, location=REGION)

def create_df_from_csv(bucket_name , file_name): #to be added as global 
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob = blob.download_as_string()
    blob = blob.decode('utf-8')

    blob = StringIO(blob)  #tranform bytes to string here

    df = pd.read_csv(blob)  #then use csv library to read the content
    return df

google_tag_map_df=create_df_from_csv("google-cloud-storage-bucket-name" ,"csv-file.csv")



app = Flask(__name__)

#authentication
auth = HTTPBasicAuth()
USER_DATA = {"username" : "password"}

@auth.verify_password 
def verify (username, password): 
    if not (username and password):
        return false
    return USER_DATA.get(username) == password

 
@app.route('/predict', methods=['POST'])
@auth.login_required
def predict():
    data = request.get_json() #gets data from api
    content = data.get("input_text") 
    threshold=data.get("threshold", 0.01 )
    topn_per_category = data.get("topn_per_category" , 20)
    tags_response = {"tags": []}
    #vertex-ai code
    endpoint_name = "------------------"    #vertex ai endpoint name/number
    endpoint = aiplatform.Endpoint(endpoint_name)
    
   
    response = endpoint.predict(instances=[{"content": content}])
    def format_tags(response, content , tags_response ,topn_per_category):
    
        for prediction_ in response.predictions:
            single_input_dict = dict()
            single_input_dict["input_text"] = content
            # single_tag_dict["id"] = id # To be passed as parameter
            ids = prediction_["ids"]
            display_names = prediction_["displayNames"]
            confidence_scores = prediction_["confidences"]
            single_input_tag = []
            for i, _ in enumerate(ids):
                if confidence_scores[i] >= threshold:
                    tmp_data = {"label": display_names[i], "score": confidence_scores[i]}
                    single_input_tag.append(tmp_data)
            si_tag_df = pd.DataFrame.from_records(single_input_tag)
            si_tag_df = si_tag_df.merge(google_tag_map_df, how='inner', on='label')
            si_tag_df = si_tag_df.sort_values(by=['label_type', 'score'], ascending=[True, False])
            si_tag_df = si_tag_df.groupby('label_type').head(topn_per_category)
            single_input_tag = si_tag_df.to_dict(orient='records')
            single_input_dict["tags"] = single_input_tag
            tags_response["tags"].append(single_input_dict)
        return tags_response
    input_file_data = format_tags(response,content, tags_response ,topn_per_category) 
    return jsonify(input_file_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))