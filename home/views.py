from rest_framework.decorators import api_view
from rest_framework.response import Response
import opennsfw2 as n2
from PIL import Image, UnidentifiedImageError
from nudenet import NudeClassifier
import numpy as np
import requests
from io import BytesIO
import os
from requests.exceptions import RequestException
import pillow_avif

# Load the NudeClassifier once, globally
classifier = NudeClassifier()

# List of common video file extensions
video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.3gp']

# List of common image file extensions
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.avif']

@api_view(['GET', 'POST'])
def image(request):
    def fetch_url(url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content

    def process_image(url):
        try:
            image_data = fetch_url(url)
        except RequestException as e:
            raise ValueError(f"Failed to fetch the URL: {e}")

        image_bytes = BytesIO(image_data)
        try:
            image_pil = Image.open(image_bytes)
            # Ensure image is in RGB mode
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')
        except UnidentifiedImageError:
            raise ValueError('Invalid image format or corrupted image')
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")

        image_np = np.array(image_pil)
        result = classifier.classify(image_np)
        safe_prob = round(result[0].get('safe', 0) * 100)
        unsafe_prob = round(result[0].get('unsafe', 0) * 100)

        final_result = {
            "safe probability": safe_prob,
            "unsafe probability": unsafe_prob
        }

        if unsafe_prob > 30:
            res = final_result["message"] = "unsafe"
            return res
        else:
            res2 = final_result["message"] = "safe"
            return res2
        return final_result

    def process_video(url):
        elapsed_seconds, nsfw_probabilities = n2.predict_video_frames(url)
        final_result = {
            'elapsed time': elapsed_seconds[100],
            'unsafe': nsfw_probabilities[100] * 100
        }

        if nsfw_probabilities[100] * 100 > 40:
            final_result["message"] = "unsafe"

        return final_result

    try:
        if request.method == 'GET':
            url = request.GET.get('search')
        elif request.method == 'POST':
            url = request.data.get('search')

        if not url:
            return Response({'error': 'No URL provided'}, status=400)

        _, ext = os.path.splitext(url)
        if ext.lower() in video_extensions:
            # Process video
            result = process_video(url)
            return Response(result)
        elif ext.lower() in image_extensions:
            # Process image
            try:
                result = process_image(url)
                return Response(result)
            except ValueError as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response({'error': 'Unsupported file extension'}, status=400)

    except RequestException as e:
        return Response({'error': 'Failed to fetch the URL: ' + str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
