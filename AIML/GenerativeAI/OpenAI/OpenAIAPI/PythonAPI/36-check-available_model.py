from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_APIUC_KEY'))

try:
    models = client.models.list()
    all_models = [model.id for model in models.data]
    
    # Filter for vision-capable models
    vision_models = []
    for model in all_models:
        if any(x in model.lower() for x in ['gpt-4o', 'gpt-4-vision', 'gpt-4-turbo']):
            vision_models.append(model)
    
    print('🔍 Checking for vision-capable models...')
    print(f'📊 Total models available: {len(all_models)}')
    print()
    
    if vision_models:
        print('✅ Vision-capable models found:')
        for i, model in enumerate(vision_models, 1):
            if 'gpt-4o' in model:
                capability = '🚀 Latest multimodal (text, images, audio)'
            elif 'gpt-4-turbo' in model:
                capability = '⚡ Fast vision model'
            elif 'gpt-4-vision' in model:
                capability = '👁️ Vision-enabled GPT-4'
            else:
                capability = '🖼️ Image analysis capable'
            
            print(f'  {i}. {model} - {capability}')
    else:
        print('❌ No vision-capable models found in your account')
        print()
        print('💡 Vision models to look for:')
        print('  - gpt-4o (latest multimodal)')
        print('  - gpt-4-turbo (with vision)')
        print('  - gpt-4-vision-preview')
        
    print()
    print('🔍 All available models:')
    for i, model in enumerate(sorted(all_models)[:20], 1):  # Show first 20
        print(f'  {i:2d}. {model}')
    if len(all_models) > 20:
        print(f'  ... and {len(all_models) - 20} more models')
        
except Exception as e:
    print(f'❌ Error: {e}')
