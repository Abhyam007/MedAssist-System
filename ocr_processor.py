import requests
import re
from datetime import datetime
import time
import tempfile
import os
from config import EXCEL_COLUMNS, TEST_PARAMETERS, OCR_SPACE_API_KEY

class OCRProcessor:
    def __init__(self):
        """Initialize OCR Processor with OCR.space API"""
        self.api_key = OCR_SPACE_API_KEY
        self.api_url = "https://api.ocr.space/parse/image"
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            print("[!] Warning: OCR.space API key not configured!")
            print("Please add your API key in config.py")
        else:
            print("[+] OCR.space API configured")
    
    def extract_text_from_pdf(self, pdf_bytes):
        """
        Extract text from PDF using OCR.space API
        Args:
            pdf_bytes: PDF file as bytes
        Returns:
            Extracted text as string
        """
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("OCR.space API key not configured. Please add your API key in config.py")
        
        # Save PDF to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        try:
            print("Uploading PDF to OCR.space API...")
            
            # Prepare the request
            with open(tmp_path, 'rb') as f:
                payload = {
                    'apikey': self.api_key,
                    'language': 'eng',
                    'isOverlayRequired': False,
                    'OCREngine': 2,  # Engine 2 is more accurate
                    'detectOrientation': True,
                    'scale': True,
                    'isTable': True,
                    'filetype': 'PDF'
                }
                
                files = {'file': f}
                
                # Make API request with timeout
                response = requests.post(
                    self.api_url,
                    files=files,
                    data=payload,
                    timeout=60
                )
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                
                # Check for API errors
                if result.get('IsErroredOnProcessing'):
                    error_msg = result.get('ErrorMessage', ['Unknown error'])
                    raise Exception(f"OCR API Error: {error_msg[0] if isinstance(error_msg, list) else error_msg}")
                
                # Check OCR exit code
                if result.get('OCRExitCode') == 1:
                    # Extract text from all pages
                    parsed_results = result.get('ParsedResults', [])
                    full_text = ""
                    
                    for page_num, page in enumerate(parsed_results, 1):
                        print(f"Processing page {page_num}/{len(parsed_results)}...")
                        page_text = page.get('ParsedText', '')
                        full_text += page_text + "\n\n"
                    
                    if not full_text.strip():
                        raise Exception("No text extracted from PDF. The PDF might be empty or image quality might be too low.")
                    
                    print(f"[+] Successfully extracted {len(full_text)} characters")
                    return full_text
                else:
                    error_details = result.get('ErrorDetails', 'Unknown error')
                    raise Exception(f"OCR processing failed: {error_details}")
            else:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            # Clean up temp file on timeout
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise Exception("OCR API request timed out. Please try again or check your internet connection.")
        
        except requests.exceptions.RequestException as e:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise Exception(f"Network error: {str(e)}")
        
        except Exception as e:
            # Clean up temp file on any error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    
    def create_manual_report(self, report_type, patient_info=None):
        """Create a manual report template for manual data entry"""
        data = {col: None for col in EXCEL_COLUMNS}
        
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = report_type
        data["Notes"] = "Manual Entry"
        
        if patient_info:
            data.update(patient_info)
        
        return data
    
    def extract_report_date(self, text):
        """Extract report date from document text"""
        date_patterns = [
            r"Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Report Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Date of Report[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Test Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Collection Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b",
            r"Date[:\s]*(\d{1,2}[-/]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/]\d{2,4})",
            r"(\d{1,2}[-/]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/]\d{2,4})",
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    date_str = match.strip()
                    try:
                        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y", 
                                   "%Y-%m-%d", "%Y/%m/%d", "%d-%b-%Y", "%d/%b/%Y",
                                   "%d-%B-%Y", "%d/%B/%Y"]:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                return parsed_date.strftime("%Y-%m-%d")
                            except:
                                continue
                    except:
                        continue
        
        return None
    
    def detect_report_type(self, text):
        """Automatically detect the type of medical report"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in 
               ['ultrasound', 'sonography', 'usg', 'echotexture', 'mm']):
            return "Ultrasound Report"
        
        elif any(keyword in text_lower for keyword in 
                 ['liver function', 'lft', 'sgot', 'sgpt', 'bilirubin']):
            return "Liver Function Test (LFT)"
        
        elif any(keyword in text_lower for keyword in 
                 ['complete blood', 'cbc', 'cbp', 'hemoglobin', 'wbc', 'rbc']):
            return "Complete Blood Picture (CBP)"
        
        elif any(keyword in text_lower for keyword in 
                 ['thyroid', 'tsh', 't3', 't4']):
            return "Thyroid Test"
        
        elif any(keyword in text_lower for keyword in 
                 ['blood pressure', 'heart rate', 'temperature', 'vitals']):
            return "Vitals Check"
        
        else:
            return "Blood Test"
    
    def extract_patient_info(self, text):
        """Extract patient information from report"""
        patient_info = {
            "Patient Name": None,
            "Patient Age": None,
            "Patient Gender": None
        }
        
        name_patterns = [
            r"Patient Name[:\s]*([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Name[:\s]*([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Patient[:\s]*([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Baby\s+([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Mr\.\s+([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Mrs\.\s+([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"Ms\.\s+([A-Z][A-Za-z\s\-\.]+?)(?:\n|Age|Gender|Date|$)",
            r"PATIENT NAME[:\s]*([A-Z][A-Z\s\-\.]+?)(?:\n|AGE|GENDER|DATE|$)",
            r"NAME[:\s]*([A-Z][A-Z\s\-\.]+?)(?:\n|AGE|GENDER|DATE|$)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and name.lower() not in ['date', 'age', 'gender', 'test', 'report']:
                    name = re.sub(r'\s+', ' ', name)
                    patient_info["Patient Name"] = name
                    break
        
        age_patterns = [
            r"Age[:\s]*(\d+)[\s]*(?:years|yrs|year|Y|months|month|M|days|day|D)?",
            r"(\d+)[\s]*(?:years|yrs|year|Y|months|month|M|days|day|D)",
            r"AGE[:\s]*(\d+)",
            r"(\d+)[YMD]"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = match.group(1).strip()
                if age.isdigit() and 0 <= int(age) <= 150:
                    patient_info["Patient Age"] = age
                    break
        
        gender_patterns = [
            r"Gender[:\s]*(Male|Female|M|F|Other)",
            r"Sex[:\s]*(Male|Female|M|F|Other)",
            r"GENDER[:\s]*(MALE|FEMALE|M|F)",
            r"\b(Male|Female)\b"
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).strip()
                if gender.upper() in ['M', 'MALE']:
                    patient_info["Patient Gender"] = "Male"
                elif gender.upper() in ['F', 'FEMALE']:
                    patient_info["Patient Gender"] = "Female"
                else:
                    patient_info["Patient Gender"] = gender
                break
        
        return patient_info
    
    def extract_ultrasound_data(self, text):
        """Extract ultrasound specific data"""
        ultrasound_data = {}
        
        liver_pattern = r"Liver.*?(\d+)[\s]*mm"
        liver_match = re.search(liver_pattern, text, re.IGNORECASE)
        if liver_match:
            ultrasound_data["Liver Size"] = float(liver_match.group(1))
        
        gb_keywords = ['normal', 'distended', 'calculi', 'wall thickening']
        for keyword in gb_keywords:
            if keyword in text.lower():
                ultrasound_data["Gall Bladder Status"] = keyword.capitalize()
                break
        
        spleen_pattern = r"Spleen.*?(\d+)[\s]*mm"
        spleen_match = re.search(spleen_pattern, text, re.IGNORECASE)
        if spleen_match:
            ultrasound_data["Spleen Size"] = float(spleen_match.group(1))
        
        kidney_pattern = r"kidney.*?(\d+)[\s]*x[\s]*(\d+)[\s]*mm"
        kidney_matches = re.findall(kidney_pattern, text, re.IGNORECASE)
        
        if len(kidney_matches) >= 2:
            ultrasound_data["Right Kidney Size"] = f"{kidney_matches[0][0]} x {kidney_matches[0][1]} mm"
            ultrasound_data["Left Kidney Size"] = f"{kidney_matches[1][0]} x {kidney_matches[1][1]} mm"
        
        findings_pattern = r"Findings[:\s]*(.*?)(?:IMPRESSION|Conclusion|$)"
        findings_match = re.search(findings_pattern, text, re.DOTALL | re.IGNORECASE)
        if findings_match:
            ultrasound_data["Ultrasound Findings"] = findings_match.group(1).strip()[:500]
        
        impression_pattern = r"IMPRESSION[:\s]*(.*?)(?:Dr\.|$)"
        impression_match = re.search(impression_pattern, text, re.DOTALL | re.IGNORECASE)
        if impression_match:
            ultrasound_data["Ultrasound Impression"] = impression_match.group(1).strip()[:500]
        
        return ultrasound_data
    
    def extract_medical_values(self, text):
        """Extract medical values with improved parsing"""
        values = {}
        
        patterns = {
            "Hemoglobin": [r"HEMOGLOBIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"Hb.*?([0-9]+\.?[0-9]*)", r"Haemoglobin.*?([0-9]+\.?[0-9]*)"],
            "RBC": [r"RBC.*?([0-9]+\.?[0-9]*)\s*10", r"Red Blood Cells.*?([0-9]+\.?[0-9]*)", r"Red Blood Cell.*?([0-9]+\.?[0-9]*)"],
            "WBC": [r"WBC.*?([0-9]+\.?[0-9]*)\s*10", r"White Blood Cells.*?([0-9]+\.?[0-9]*)", r"White Blood Cell.*?([0-9]+\.?[0-9]*)"],
            "Platelets": [r"PLATELET.*?([0-9]+\.?[0-9]*)\s*10", r"Platelet Count.*?([0-9]+\.?[0-9]*)", r"PLT.*?([0-9]+\.?[0-9]*)"],
            "Glucose": [r"GLUCOSE.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Blood Sugar.*?([0-9]+\.?[0-9]*)", r"FBS.*?([0-9]+\.?[0-9]*)"],
            "Cholesterol": [r"CHOLESTEROL.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Total Cholesterol.*?([0-9]+\.?[0-9]*)"],
            "Total Bilirubin": [r"TOTAL BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Bilirubin Total.*?([0-9]+\.?[0-9]*)"],
            "Conjugated Bilirubin": [r"CONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Direct Bilirubin.*?([0-9]+\.?[0-9]*)"],
            "Unconjugated Bilirubin": [r"UNCONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Indirect Bilirubin.*?([0-9]+\.?[0-9]*)"],
            "SGOT (AST)": [r"SGOT.*?([0-9]+\.?[0-9]*)\s*U/L", r"AST.*?([0-9]+\.?[0-9]*)\s*U/L", r"Aspartate.*?([0-9]+\.?[0-9]*)"],
            "SGPT (ALT)": [r"SGPT.*?([0-9]+\.?[0-9]*)\s*U/L", r"ALT.*?([0-9]+\.?[0-9]*)\s*U/L", r"Alanine.*?([0-9]+\.?[0-9]*)"],
            "Alkaline Phosphatase": [r"ALKALINE PHOSPHATASE.*?([0-9]+\.?[0-9]*)\s*U/L", r"ALP.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "Total Protein": [r"TOTAL PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Albumin": [r"ALBUMIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Globulin": [r"GLOBULIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "A/G Ratio": [r"A/G RATIO.*?([0-9]+\.?[0-9]*)", r"AG RATIO.*?([0-9]+\.?[0-9]*)"],
            "PCV/HCT": [r"PCV.*?([0-9]+\.?[0-9]*)\s*%", r"HCT.*?([0-9]+\.?[0-9]*)\s*%", r"Hematocrit.*?([0-9]+\.?[0-9]*)"],
            "MCV": [r"MCV.*?([0-9]+\.?[0-9]*)\s*fL", r"Mean Corpuscular Volume.*?([0-9]+\.?[0-9]*)"],
            "MCH": [r"MCH.*?([0-9]+\.?[0-9]*)\s*pg", r"Mean Corpuscular Hemoglobin.*?([0-9]+\.?[0-9]*)"],
            "MCHC": [r"MCHC.*?([0-9]+\.?[0-9]*)\s*g/dL", r"Mean Corpuscular Hemoglobin Concentration.*?([0-9]+\.?[0-9]*)"],
            "RDW-CV": [r"RDW.*?([0-9]+\.?[0-9]*)\s*%", r"Red Cell Distribution Width.*?([0-9]+\.?[0-9]*)"],
            "MPV": [r"MPV.*?([0-9]+\.?[0-9]*)\s*fL", r"Mean Platelet Volume.*?([0-9]+\.?[0-9]*)"],
            "Neutrophils": [r"NEUTROPHILS.*?([0-9]+\.?[0-9]*)\s*%", r"Neutrophil.*?([0-9]+\.?[0-9]*)"],
            "Lymphocytes": [r"LYMPHOCYTES.*?([0-9]+\.?[0-9]*)\s*%", r"Lymphocyte.*?([0-9]+\.?[0-9]*)"],
            "Monocytes": [r"MONOCYTES.*?([0-9]+\.?[0-9]*)\s*%", r"Monocyte.*?([0-9]+\.?[0-9]*)"],
            "Eosinophils": [r"EOSINOPHILS.*?([0-9]+\.?[0-9]*)\s*%", r"Eosinophil.*?([0-9]+\.?[0-9]*)"],
            "T3 (Triiodothyronine)": [r"T3.*?([0-9]+\.?[0-9]*)\s*ng/mL", r"TRIIODOTHYRONINE.*?([0-9]+\.?[0-9]*)", r"Triiodothyronine.*?([0-9]+\.?[0-9]*)"],
            "T4 (Thyroxine)": [r"T4.*?([0-9]+\.?[0-9]*)\s*µg/dL", r"THYROXINE.*?([0-9]+\.?[0-9]*)", r"Thyroxine.*?([0-9]+\.?[0-9]*)"],
            "TSH": [r"TSH.*?([0-9]+\.?[0-9]*)\s*µIU/mL", r"THYROID STIMULATING.*?([0-9]+\.?[0-9]*)", r"Thyroid Stimulating Hormone.*?([0-9]+\.?[0-9]*)"],
            "Blood Pressure Systolic": [r"(\d{2,3})/\d{2,3}\s*mmHg", r"BP.*?(\d{2,3})/\d{2,3}", r"Systolic.*?(\d{2,3})"],
            "Blood Pressure Diastolic": [r"\d{2,3}/(\d{2,3})\s*mmHg", r"BP.*?\d{2,3}/(\d{2,3})", r"Diastolic.*?(\d{2,3})"],
            "Heart Rate": [r"Heart Rate.*?(\d{2,3})\s*bpm", r"HR.*?(\d{2,3})", r"Pulse.*?(\d{2,3})"],
            "Temperature": [r"Temperature.*?(\d{2,3}\.\d)\s*°F", r"Temp.*?(\d{2,3}\.\d)", r"Body Temperature.*?(\d{2,3}\.\d)"]
        }
        
        for param, param_patterns in patterns.items():
            for pattern in param_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        values[param] = value
                        break
                    except ValueError:
                        continue
        
        bp_pattern = r"(\d{2,3})/(\d{2,3})"
        bp_matches = re.findall(bp_pattern, text)
        if bp_matches:
            systolic, diastolic = bp_matches[0]
            values["Blood Pressure Systolic"] = float(systolic)
            values["Blood Pressure Diastolic"] = float(diastolic)
        
        return values
    
    def extract_dynamic_test_parameters(self, text):
        """Dynamically extract any test parameters found in the report"""
        dynamic_params = {}
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            if any(skip in line.lower() for skip in ['patient', 'date', 'age', 'gender', 'report', 'doctor', 'lab', 'address', 'phone', 'email']):
                continue
            
            pattern = r"([A-Z][A-Za-z\s\(\)/]+?)[:\s]+([0-9]+\.?[0-9]*)\s*([a-zA-Z/%°µ]+)?"
            matches = re.findall(pattern, line)
            if matches:
                for match in matches:
                    param_name = match[0].strip()
                    param_value = match[1].strip()
                    
                    param_name = re.sub(r'\s+', ' ', param_name)
                    param_name = param_name.strip(':-=')
                    
                    if len(param_name) < 3 or param_name.isdigit():
                        continue
                    
                    if param_name.lower() in ['date', 'age', 'gender', 'name', 'test', 'report', 'normal', 'range', 'unit', 'reference']:
                        continue
                    
                    try:
                        value = float(param_value)
                        if 0 <= value <= 1000000:
                            dynamic_params[param_name] = value
                    except:
                        continue
        
        return dynamic_params
    
    def parse_medical_report(self, text, selected_test_type=None):
        """Parse medical report text and extract all parameters"""
        print("Parsing extracted text...")
        
        data = {col: None for col in EXCEL_COLUMNS}
        
        patient_info = self.extract_patient_info(text)
        data.update(patient_info)
        
        extracted_date = self.extract_report_date(text)
        if extracted_date:
            data["Date"] = extracted_date
        else:
            data["Date"] = datetime.now().strftime("%Y-%m-%d")
        
        detected_type = selected_test_type or self.detect_report_type(text)
        data["Report Type"] = detected_type
        data["Notes"] = ""
        
        medical_values = self.extract_medical_values(text)
        data.update(medical_values)
        
        dynamic_params = self.extract_dynamic_test_parameters(text)
        
        dynamic_notes = []
        for param_name, param_value in dynamic_params.items():
            if param_name not in data or data[param_name] is None:
                dynamic_notes.append(f"{param_name}: {param_value}")
        
        if dynamic_notes:
            if data.get("Notes"):
                data["Notes"] += " | Dynamic Tests: " + "; ".join(dynamic_notes)
            else:
                data["Notes"] = "Dynamic Tests: " + "; ".join(dynamic_notes)
        
        if data["Report Type"] == "Ultrasound Report":
            ultrasound_data = self.extract_ultrasound_data(text)
            data.update(ultrasound_data)
            return data
        
        if data["Albumin"] and data["Total Protein"]:
            if not data["Globulin"]:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)
            
            if data["Globulin"] and not data["A/G Ratio"] and data["Globulin"] > 0:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)
        
        return data
    
    def process_pdf_report(self, pdf_bytes, selected_test_type=None):
        """Main method to process PDF and return structured data"""
        print("Extracting text from PDF using OCR.space API...")
        text = self.extract_text_from_pdf(pdf_bytes)
        
        print("Parsing extracted text...")
        parsed_data = self.parse_medical_report(text, selected_test_type)
        return parsed_data, text
    
    def get_detected_parameters(self, parsed_data):
        """Get list of parameters that were successfully detected"""
        detected = []
        for key, value in parsed_data.items():
            if key not in ["Date", "Report Type", "Notes", "Patient Name", 
                          "Patient Age", "Patient Gender", "Ultrasound Findings", 
                          "Ultrasound Impression"] and value is not None:
                detected.append(key)
        return detected