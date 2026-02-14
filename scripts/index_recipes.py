import json
import boto3
import os

BUCKET = os.environ.get('S3_BUCKET') or os.environ.get('RECIPES_BUCKET', 'cooking-assistant-recipes')
REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')

bedrock = boto3.client('bedrock-runtime', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def get_embedding(text):
    """Get embedding using Titan Embeddings V2"""
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            "inputText": text,
            "dimensions": 1024,
            "normalize": True
        })
    )
    return json.loads(response['body'].read())['embedding']

def index_recipes():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    embeddings_data = []
    
    print(f"Reading recipes from: {data_dir}")
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Upload recipe text to S3
            s3.put_object(Bucket=BUCKET, Key=f'recipes/{filename}', Body=text)
            
            # Generate and store embedding
            embedding = get_embedding(text)
            embeddings_data.append({
                'recipe_id': filename,
                'text': text[:500],  # Store preview only
                'embedding': embedding
            })
            print(f"✓ Indexed: {filename}")
    
    # Store all embeddings in single JSON file
    s3.put_object(
        Bucket=BUCKET,
        Key='embeddings/recipe_embeddings.json',
        Body=json.dumps(embeddings_data)
    )
    print(f"\n✅ Uploaded {len(embeddings_data)} recipes to S3")
    print(f"📦 Bucket: {BUCKET}")
    print(f"🌍 Region: {REGION}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔄 Indexing Recipes to S3")
    print("="*60 + "\n")
    index_recipes()
    print("\n" + "="*60)
    print("✨ Complete!")
    print("="*60 + "\n")
