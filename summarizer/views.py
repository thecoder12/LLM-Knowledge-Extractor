from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Analysis
from .serializers import AnalysisSerializer
import re
import os
from pprint import pprint
from dotenv import load_dotenv
import requests
import json
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def parse_llm_response_with_regex(raw_text):
    result = {'title': '', 'topics': [], 'sentiment': '', 'keywords': [], 'summary': '', 'raw_response': raw_text}
    title_match = re.search(r'"?title"?\s*[:=]\s*["\']?([^\n",\']+)', raw_text, re.IGNORECASE)
    if title_match:
        result['title'] = title_match.group(1).strip()
    topics_match = re.search(r'"?topics"?\s*[:=]\s*\[([^\]]+)\]', raw_text, re.IGNORECASE)
    if topics_match:
        result['topics'] = [t.strip(' "\'') for t in topics_match.group(1).split(',')]
    sentiment_match = re.search(r'"?sentiment"?\s*[:=]\s*["\']?([^\n",\']+)', raw_text, re.IGNORECASE)
    if sentiment_match:
        result['sentiment'] = sentiment_match.group(1).strip()
    summary_match = re.search(r'"?summary"?\s*[:=]\s*["\']?([^\n",\']+)', raw_text, re.IGNORECASE)
    if summary_match:
        result['summary'] = summary_match.group(1).strip()
    keywords_match = re.search(r'"?keywords"?\s*[:=]\s*\[([^\]]+)\]', raw_text, re.IGNORECASE)
    if keywords_match:
        result['keywords'] = [t.strip(' "\'') for t in keywords_match.group(1).split(',')]
    return result



def call_gemini_api(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {"key": GEMINI_API_KEY}
    response = requests.post(url, headers=headers, params=params, json=payload)
    response.raise_for_status()
    gemini_content = response.json()
    import json, re
    raw_text = gemini_content['candidates'][0]['content']['parts'][0]['text']
    print('----')
    print(raw_text)
    print('----')
    raw_text = re.sub('json','',raw_text)
    raw_text = re.sub("```",'',raw_text)
    try:
        result = json.loads(raw_text)
        print(result)
        print(result.get('title', ''))
    except Exception:
        result = parse_llm_response_with_regex(raw_text)  # for Gemini

    return result



def call_openai_api(prompt):
    import openai
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        openai_text = response.choices[0].message.content
        print('----')
        print(openai_text)
        print('----')
        try:
            result = json.loads(openai_text)
        except Exception:
            result = parse_llm_response_with_regex(openai_text)  # for OpenAI
        return result
    except Exception as e:
        return {'title': '', 'topics': [], 'sentiment': '', 'keywords': [], 'summary': '', 'raw_response': str(e)}


def should_use_gemini(request):
    # Always use Gemini as default
    return True

def extract_keywords(text):
    import spacy
    from collections import Counter

    nlp = spacy.load("en_core_web_sm") # Load pre-trained English model
    doc = nlp(text) # Process text
    nouns = [token.text.lower() for token in doc if token.pos_ == "NOUN"] # Extract nouns (singular and plural)
    noun_freq = Counter(nouns) # Count frequency

    # Get the top 3 most common nouns (just the words, not counts)
    top_3_nouns = [word for word, count in noun_freq.most_common(3)]
    return top_3_nouns


def home(request):
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            return render(request, 'summarizer/home.html', {'error': 'Input cannot be empty.'})
        try:
            result = None
            engine = request.GET.get('engine', 'gemini').lower() if request.GET.get('engine') else 'gemini'
            prompt = ( "Text: " + text + "\n\n"
                "You must respond ONLY with valid JSON containing these keys: title, topics (list of 3 key topics), sentiment (positive/neutral/negative), keywords & summary "
                "Do not include any explanation or extra text. Example: {\"title\": \"...\", \"topics\": [\"...\", \"...\", \"...\"], \"sentiment\": \"...\", \"keywords\": [\"...\", \"...\", \"...\"], \"summary\": \"...\"}. "
            )

            if engine == 'gemini':
                result = call_gemini_api(prompt)

            elif engine == 'openai':
                result = call_openai_api(prompt)
            result['keywords'] = extract_keywords(text)
            analysis = Analysis.objects.create(
                title=result.get('title', ''),
                text=text,
                topics=result.get('topics', []),
                sentiment=result.get('sentiment', ''),
                keywords=result.get('keywords', []),
                summary=result['summary'],
            )
            return render(request, 'summarizer/result.html', {'analysis': analysis, 'engine': engine.capitalize()})
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if e.response is not None else str(e)
            if e.response is not None and e.response.status_code == 429:
                return render(request, 'summarizer/home.html', {'error': f'{engine.capitalize()} API rate limit exceeded. Details: {error_detail}'})
            return render(request, 'summarizer/home.html', {'error': f'{engine.capitalize()} API error: {error_detail}'})
        except Exception as e:
            return render(request, 'summarizer/home.html', {'error': f'{engine.capitalize()} API failure: {str(e)}'})
    return render(request, 'summarizer/home.html')

def history(request):
    analyses = Analysis.objects.all().order_by('-created_at')
    return render(request, 'summarizer/history.html', {'analyses': analyses})

class AnalyzeAPI(APIView):
    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'Input cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = None
            engine = request.query_params.get('engine', 'gemini').lower() if request.query_params.get('engine') else 'gemini'
            prompt = ( "Text: " + text + "\n\n"
                "You must respond ONLY with valid JSON containing these keys: title, topics (list of 3 key topics), sentiment (positive/neutral/negative), keywords & summary "
                "Do not include any explanation or extra text. Example: {\"title\": \"...\", \"topics\": [\"...\", \"...\", \"...\"], \"sentiment\": \"...\", \"keywords\": [\"...\", \"...\", \"...\"], \"summary\": \"...\"}. "
            )
            if engine == 'gemini':
                result = call_gemini_api(prompt)

            elif engine == 'openai':
                result = call_openai_api(prompt)
            result['keywords'] = extract_keywords(text)
            analysis = Analysis.objects.create(
                title=result.get('title', ''),
                text=text,
                topics=result.get('topics', []),
                sentiment=result.get('sentiment', ''),
                keywords=result.get('keywords', []),
                summary=result['summary'],
            )
            response_data = AnalysisSerializer(analysis).data
            response_data['engine'] = engine.capitalize()
            return Response(response_data)
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if e.response is not None else str(e)
            if e.response is not None and e.response.status_code == 429:
                return Response({'error': f'API rate limit exceeded. Details: {error_detail}'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({'error': f'API error: {error_detail}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'API failure: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SearchAPI(APIView):
    def get(self, request):
        topic = request.GET.get('topic', '').lower()
        if not topic:
            return Response({'error': 'No topic provided.'}, status=status.HTTP_400_BAD_REQUEST)
        analyses = Analysis.objects.filter(topics__icontains=topic)
        return Response(AnalysisSerializer(analyses, many=True).data)
    

