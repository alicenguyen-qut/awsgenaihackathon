import json
import boto3
import os

BUCKET = os.environ.get('RECIPES_BUCKET', 'cooking-assistant-recipes')
REGION = 'ap-southeast-2'

bedrock = boto3.client('bedrock-runtime', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def get_embedding(text):
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({"inputText": text})
    )
    return json.loads(response['body'].read())['embedding']

def index_recipes():
    data_dir = '../data'
    embeddings_data = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r') as f:
                text = f.read()
            
            # Upload recipe text to S3
            s3.put_object(Bucket=BUCKET, Key=f'recipes/{filename}', Body=text)
            
            # Generate and store embedding
            embedding = get_embedding(text)
            embeddings_data.append({
                'recipe_id': filename,
                'text': text,
                'embedding': embedding
            })
            print(f"Indexed: {filename}")
    
    # Store all embeddings in single JSON file
    s3.put_object(
        Bucket=BUCKET,
        Key='embeddings/recipe_embeddings.json',
        Body=json.dumps(embeddings_data)
    )
    print(f"Uploaded {len(embeddings_data)} recipes to S3")

if __name__ == '__main__':
    index_recipes()
    print("Complete!")
