import base64
import requests
import os
import json
from io import BytesIO
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv
import argparse
import re
from dataclasses import dataclass

@dataclass
class FamilyMember:
    """Represents a family member with their image and relationship"""
    name: str
    relationship: str
    image_path: str
    encoded_image: str


@dataclass
class ImageAnalysisResult:
    """Result of image importance analysis"""
    image_path: str
    importance_score: int
    analysis: str
    detected_family_members: List[str]


class ImageImportanceAnalyzer:
    """Main class for analyzing image importance using VLM with family face context"""
    
    def __init__(self, api_key: str, model: str = "Qwen/Qwen2.5-VL-7B-Instruct"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.hyperbolic.xyz/v1/chat/completions"
        
    def encode_image(self, img: Image.Image) -> str:
        """Encode PIL Image to base64 string"""
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return encoded_string
    
    def load_image_safely(self, image_path: str) -> Optional[Image.Image]:
        """Load image with error handling"""
        try:
            img = Image.open(image_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def find_family_faces_folder(self, root_directory: str) -> Optional[str]:
        """Find the FamilyFaces folder in the directory structure"""
        root_path = Path(root_directory)
        
        # Search for any folder containing "FamilyFaces" in its name
        for folder in root_path.rglob("*"):
            if folder.is_dir() and "FamilyFaces" in folder.name:
                return str(folder)
        
        return None
    
    def parse_relationship_from_filename(self, filename: str) -> Tuple[str, str]:
        """Extract name and relationship from filename"""
        # Remove extension
        name_part = Path(filename).stem
        
        # Common relationship patterns
        relationship_patterns = {
            r'uncle': 'uncle',
            r'aunt': 'aunt', 
            r'mom': 'mother',
            r'mother': 'mother',
            r'dad': 'father',
            r'father': 'father',
            r'sister': 'sister',
            r'brother': 'brother',
            r'grandma': 'grandmother',
            r'grandmother': 'grandmother',
            r'grandpa': 'grandfather',
            r'grandfather': 'grandfather',
            r'cousin': 'cousin',
            r'wife': 'wife',
            r'husband': 'husband',
            r'son': 'son',
            r'daughter': 'daughter',
            r'friend': 'friend'
        }
        
        # Try to extract relationship from filename
        relationship = "family member"  # default
        for pattern, rel in relationship_patterns.items():
            if re.search(pattern, name_part.lower()):
                relationship = rel
                break
        
        # Clean up the name by removing relationship words and numbers
        name = re.sub(r'[_\-\d]+', ' ', name_part).strip()
        for pattern in relationship_patterns.keys():
            name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
        
        if not name:
            name = name_part
            
        return name, relationship
    
    def load_family_faces(self, family_faces_folder: str) -> List[FamilyMember]:
        """Load all family face images with their relationships"""
        family_members = []
        
        if not os.path.exists(family_faces_folder):
            print(f"Family faces folder not found: {family_faces_folder}")
            return family_members
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        
        for file_path in Path(family_faces_folder).rglob("*"):
            if file_path.suffix.lower() in image_extensions:
                img = self.load_image_safely(str(file_path))
                if img:
                    name, relationship = self.parse_relationship_from_filename(file_path.name)
                    encoded_img = self.encode_image(img)
                    
                    family_member = FamilyMember(
                        name=name,
                        relationship=relationship,
                        image_path=str(file_path),
                        encoded_image=encoded_img
                    )
                    family_members.append(family_member)
                    print(f"Loaded family member: {name} ({relationship})")
        
        return family_members
    
    def build_importance_analysis_prompt(self, family_members: List[FamilyMember]) -> str:
        """Build comprehensive prompt for image importance analysis"""
        
        family_context = ""
        if family_members:
            family_context = "Family members for reference:\n"
            for member in family_members:
                family_context += f"- {member.name} ({member.relationship})\n"
        
        prompt = f"""You are an expert image analyst tasked with rating the importance of a target image to a user based on multiple factors.

                {family_context}

                Analyze the target image and assign an importance score from 0.00 to 100.00 using these weighted criteria:
                Note that giving a score with two decimal places is required to provide more granularity in your scoring.
                **Family & Personal Connection (40%):**
                - Identification of family members (cross-reference with provided family faces)
                - Emotional resonance and interpersonal dynamics captured
                - Depth of personal memories and relationships depicted

                **Image Quality (25%):**
                - Focus sharpness and visual clarity
                - Lighting balance and proper exposure
                - Compositional strength and framing

                **Content Significance (25%):**
                - Milestone events, celebrations, or meaningful occasions
                - Capturing of fleeting or unique moments
                - Location appeal and environmental context

                **Rarity & Uniqueness (10%):**
                - Distinctive situations, expressions, or arrangements
                - Documentary or historical significance
                - Irreproducibility of the moment

                Output your assessment in this exact format:
                IMPORTANCE_SCORE: [0.00-100.00]
                DETECTED_FAMILY_MEMBERS: [list recognized individuals from reference images, or "None identified"]
                ANALYSIS: [Comprehensive explanation covering: (1) family presence and relationships, (2) technical quality observations, (3) content and moment significance, (4) rarity factors. Be precise about visible elements that influence the rating.]

                Provide concrete observations rather than generalities. Explain both strengths and limitations affecting the final score.
                """
        return prompt
    
    def build_api_payload(self, prompt: str, target_image: str, family_images: List[str]) -> Dict[str, Any]:
        """Build API payload with target image and family reference images"""
        
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        
        # Add target image first
        content.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{target_image}"}
        })
        
        # Add family reference images
        for i, family_img in enumerate(family_images):
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{family_img}"}
            })
        
        return {
            "messages": [{
                "role": "user",
                "content": content
            }],
            "model": self.model,
            "max_tokens": 1024,
            "temperature": 0.1,
            "top_p": 0.001,
        }
    
    def call_vlm_api(self, payload: dict) -> dict:
        """Call the Hyperbolic VLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {"error": str(e)}
    
    def parse_vlm_response(self, response_text: str) -> Tuple[int, str, List[str]]:
        """Parse VLM response to extract score, analysis, and detected family members"""
        
        # Extract importance score
        score_match = re.search(r'IMPORTANCE_SCORE:\s*(\d+\.\d+)', response_text)
        importance_score = float(score_match.group(1)) if score_match else 0.0
        
        # Extract detected family members
        family_match = re.search(r'DETECTED_FAMILY_MEMBERS:\s*\[(.*?)\]', response_text, re.DOTALL)
        detected_family = []
        if family_match:
            family_text = family_match.group(1).strip()
            if family_text and family_text != "":
                detected_family = [member.strip().strip('"\'') for member in family_text.split(',')]
        
        # Extract analysis
        analysis_match = re.search(r'ANALYSIS:\s*(.*)', response_text, re.DOTALL)
        analysis = analysis_match.group(1).strip() if analysis_match else response_text
        
        return importance_score, analysis, detected_family
    
    def analyze_image_importance(self, target_image_path: str, family_members: List[FamilyMember]) -> ImageAnalysisResult:
        """Analyze importance of a single target image"""
        
        # Load target image
        target_img = self.load_image_safely(target_image_path)
        if not target_img:
            return ImageAnalysisResult(
                image_path=target_image_path,
                importance_score=0,
                analysis="Failed to load target image",
                detected_family_members=[]
            )
        
        # Encode target image
        target_encoded = self.encode_image(target_img)
        
        # Get family images (limit to avoid token limits)
        family_encoded_images = [member.encoded_image for member in family_members[:3]]
        
        # Build prompt and payload
        prompt = self.build_importance_analysis_prompt(family_members)
        payload = self.build_api_payload(prompt, target_encoded, family_encoded_images)
        
        # Call API
        print(f"Analyzing image: {target_image_path}")
        response = self.call_vlm_api(payload)
        
        if "error" in response:
            return ImageAnalysisResult(
                image_path=target_image_path,
                importance_score=0,
                analysis=f"API Error: {response['error']}",
                detected_family_members=[]
            )
        
        # Parse response
        response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        importance_score, analysis, detected_family = self.parse_vlm_response(response_text)
        
        return ImageAnalysisResult(
            image_path=target_image_path,
            importance_score=importance_score,
            analysis=analysis,
            detected_family_members=detected_family
        )
    
    def process_directory(self, root_directory: str, output_file: Optional[str] = None) -> List[ImageAnalysisResult]:
        """Process entire directory structure to analyze all images"""
        
        # Find family faces folder
        family_faces_folder = self.find_family_faces_folder(root_directory)
        if not family_faces_folder:
            print("No FamilyFaces folder found in directory structure")
            return []
        
        print(f"Found family faces folder: {family_faces_folder}")
        
        # Load family faces
        family_members = self.load_family_faces(family_faces_folder)
        print(f"Loaded {len(family_members)} family members")
        
        if not family_members:
            print("No family members loaded, continuing without family context")
        
        # Find all target images (excluding family faces folder)
        target_images = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        
        for file_path in Path(root_directory).rglob("*"):
            if (file_path.suffix.lower() in image_extensions and 
                file_path.is_file() and 
                family_faces_folder not in str(file_path.parent)):
                target_images.append(str(file_path))
        
        print(f"Found {len(target_images)} target images to analyze")
        
        # Analyze each image
        results = []
        for i, image_path in enumerate(target_images):
            print(f"Processing image {i+1}/{len(target_images)}: {Path(image_path).name}")
            result = self.analyze_image_importance(image_path, family_members)
            results.append(result)
            
            # Print result summary
            print(f"  Score: {result.importance_score}/100")
            if result.detected_family_members:
                print(f"  Family detected: {', '.join(result.detected_family_members)}")
            print()
        
        # Save results if output file specified
        if output_file:
            self.save_results(results, output_file)
        
        return results
    
    def save_results(self, results: List[ImageAnalysisResult], output_file: str):
        """Save analysis results to JSON file"""
        
        results_data = []
        for result in results:
            results_data.append({
                "image_path": result.image_path,
                "importance_score": result.importance_score,
                "analysis": result.analysis,
                "detected_family_members": result.detected_family_members
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze image importance using VLM with family face context")
    parser.add_argument("--directory", help="Root directory containing images and FamilyFaces folder")
    parser.add_argument("--output", "-o", help="Output JSON file for results")
    parser.add_argument("--model", default="Qwen/Qwen2.5-VL-7B-Instruct", help="VLM model to use")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("HYPERBOLIC_API_KEY")
    
    if not api_key:
        print("Error: HYPERBOLIC_API_KEY not found in environment variables")
        return
    
    # Create analyzer
    analyzer = ImageImportanceAnalyzer(api_key, args.model)
    
    # Process directory
    results = analyzer.process_directory(args.directory, args.output)
    
    # Print summary
    if results:
        scores = [r.importance_score for r in results]
        print(f"\nSummary:")
        print(f"Total images analyzed: {len(results)}")
        print(f"Average importance score: {sum(scores) / len(scores):.1f}")
        print(f"Highest score: {max(scores)}")
        print(f"Lowest score: {min(scores)}")
        
        # Show top 5 most important images
        top_images = sorted(results, key=lambda x: x.importance_score, reverse=True)[:5]
        print(f"\nTop 5 most important images:")
        for i, result in enumerate(top_images, 1):
            print(f"{i}. {Path(result.image_path).name} - Score: {result.importance_score}")


if __name__ == "__main__":
    main()