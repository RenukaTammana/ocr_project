import cv2
import numpy as np
import pytesseract
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
import base64

def home(request):
    return render(request, 'ocr_app/home.html')

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding or other techniques to enhance text visibility
    processed_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return processed_image


def extract_info(image):
    processed_image = preprocess_image(image)
    text = pytesseract.image_to_string(processed_image)
    print("Extracted Text:")
    print(text)
    name, birth_date = parse_text(text) 
    return name, birth_date


def parse_text(text):
    name = None
    birth_date = None

    all_text_list = re.split(r'[\n]', text)
    text_list = list()
    
    for i in all_text_list:
        if re.match(r'^(\s)+$', i) or i=='':
            continue
        else:
            text_list.append(i)
    print(text_list)

    if "MALE" in text or "male" in text or "FEMALE" in text or "female" in text :
        name=aadhar_name(text_list)
    else:
        name=pan_name(text)

    #Extract Date of Birth 
    dob_match_pan = re.search(r'(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    if dob_match_pan:
        birth_date = dob_match_pan.group(0).strip() 
    return name, birth_date

def aadhar_name(text_list):
    try:
        user_dob = str()
        user_name = str()
        aadhar_dob_pat = r'(YoB|YOB:|DOB:|DOB|AOB)'
        date_ele = str()
        for idx, i in enumerate(text_list):
            if re.search(aadhar_dob_pat, i):
                index = re.search(aadhar_dob_pat, i).span()[1]
                date_ele = i
                dob_idx = idx
            else:
                continue

        date_str=''
        for i in date_ele[index:]:
            if re.match(r'\d', i):
                date_str = date_str+i
            elif re.match(r'/', i):
                date_str = date_str+i
            else:
                continue
        user_dob = date_str

        user_name = text_list[dob_idx-1]
        pattern = re.search(r'([A-Z][a-zA-Z\s]+)', user_name)
        # pattern = re.search(r'([A-Z][a-zA-Z\s]+[A-Z][a-zA-Z\s]+[A-Z][a-zA-Z]+)'or r'([A-Z][a-zA-Z\s]+[A-Z][a-zA-Z])' , user_name)
        if pattern:
            name = pattern.group(0).strip()
        else:
            name= None    
        return name
    except Exception:
            return None

def pan_name(text):
    pancard_name=None
    name_patterns = [
        r'(Name\s*\n[A-Z]+[\s]+[A-Z]+[\s]+[A-Z]+[\s])',  
        r'(Name\s*\n[A-Z]+[\s]+[A-Z]+[\s])', 
        r'(Name\s*\n[A-Z\s]+)'  
    ]

    for pattern in name_patterns:
            name_match_pan = re.search(pattern,text)
            if name_match_pan:
                matched_name = name_match_pan.group(1).strip().replace('\n', ' ') 
                pancard_name = re.sub(r'^Name\s+', '', matched_name)
                print("pan name:", pancard_name)
                break
    return pancard_name

def process_image(image):
    name, birth_date = extract_info(image)
    if birth_date is None:
        # Handle case where birth_date could not be extracted
        return name, None, None 
    else:
        age=calculate_age(birth_date)
    if name:
        name = name.upper()
    
    return name, birth_date, age

def calculate_age(birth_date):
    try:
        birth_date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']
        for fmt in birth_date_formats:
            try:
                birth_date = datetime.strptime(birth_date, "%d/%m/%Y")
                print(birth_date)
                break  
            except ValueError:
                continue
        age = (datetime.now() - birth_date).days // 365
    except (ValueError, TypeError):
       
        birth_date = None
        age = None
    return age
def visitor_card_template(request):
    name = request.GET.get('name', '')
    birth_date = request.GET.get('birth_date', '')
    age = calculate_age(birth_date)
    email = request.GET.get('email', '')
    phone = request.GET.get('phone','')
    
    #age = int(age) if age else None
    
    # Define the context dictionary to pass the data to the template
    context = {
        'name': name,
        'birth_date': birth_date,
        'age': age,
        'email': email,
        'phone':phone
    }
    
    if int(context['age'])<18:
             return render(request, 'ocr_app/vscard.html', {'error_message': "Not eligible to get a Visitor Card"})

    # Render the vscard.html template with the provided data
    return render(request, 'ocr_app/vscard.html', context)

   # return render(request, 'ocr_app/vscard.html')
@csrf_exempt 
def upload_image(request):
    if request.method == 'POST':
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), -1)
            name, birth_date, age = process_image(image)

            if birth_date is None or name is None:
                return render(request, 'ocr_app/home.html', {'error_message': "Image quality is too poor. Please try again or add the details manually."})

          
            return render(request, 'ocr_app/home.html', {'name': name, 'birth_date': birth_date, 'age': age})
        else:
           
            name = request.POST.get('name')
            birth_date = request.POST.get('birth_date')
            age = calculate_age(birth_date)  

            
            return render(request, 'ocr_app/home.html', {'name': name, 'birth_date': birth_date, 'age': age})

    return render(request, 'ocr_app/home.html')