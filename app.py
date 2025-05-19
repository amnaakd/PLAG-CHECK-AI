from flask import Flask, request, render_template
import re
import math
import string

app = Flask(__name__)  # Fixed: Removed quotes around __name__

# Define thresholds
AI_GENERATED_THRESHOLD = 0.8  # AI detection threshold (0-1 scale)
AI_DETECTION_THRESHOLD = 10    # AI text warning threshold (%)
PLAGIARISM_THRESHOLD = 10      # Plagiarism detection threshold (%)

def calculate_ai_percentage(text):
    """Calculate the likelihood of AI-generated text."""
    if not text.strip():
        return 0.0
    
    # Remove punctuation and numbers
    clean_text = re.sub(rf"[{string.punctuation}0-9]", "", text)
    words = clean_text.lower().split()
    
    if not words:
        return 0.0
    
    # Calculate uniqueness ratio
    unique_words = set(words)
    unique_ratio = len(unique_words) / len(words)
    ai_percentage = (1 - unique_ratio) * 100
    return ai_percentage
@app.route("/")
def loadPage():
    return render_template(
        'index.html',
        query="",
        percentage=0,
        plagiarized_texts=[],  # Initialize as empty list
        ai_percentage=0,
        is_ai_text=False,
        ai_text_detected=False,
        plagiarism_status="No Plagiarism"
    )


@app.route("/", methods=['POST'])
def detect_plagiarism_and_ai_text():
    try:
        inputQuery = request.form.get('query', '').strip()
        if not inputQuery:
            return render_template('index.html', error="Empty input!")
        
        lowercaseQuery = inputQuery.lower()
        
        # Clean and split words
        queryWordList = re.sub(r"[^\w]", " ", lowercaseQuery).split()  # Fixed: Raw string
        
        # Read database (with error handling)
        try:
            with open("database1.txt", "r") as fd:
                database1 = fd.read().lower()
        except FileNotFoundError:
            return render_template('index.html', error="Database file not found!")
        
        databaseWordList = re.sub(r"[^\w]", " ", database1).split()  # Fixed: Raw string
        
        # Get unique words (optimized)
        universalSetOfUniqueWords = list(set(queryWordList).union(set(databaseWordList)))
        
        # Calculate Term Frequencies (TF)
        queryTF = [queryWordList.count(word) for word in universalSetOfUniqueWords]
        databaseTF = [databaseWordList.count(word) for word in universalSetOfUniqueWords]
        
        # Cosine Similarity Calculation
        dotProduct = sum(q * db for q, db in zip(queryTF, databaseTF))
        queryMagnitude = math.sqrt(sum(tf ** 2 for tf in queryTF))
        dbMagnitude = math.sqrt(sum(tf ** 2 for tf in databaseTF))
        
        # Avoid division by zero
        if queryMagnitude == 0 or dbMagnitude == 0:
            matchPercentage = 0.0
        else:
            matchPercentage = (dotProduct / (queryMagnitude * dbMagnitude)) * 100
        
        # Plagiarism detection
        plagiarizedTexts = list(set(queryWordList) & set(databaseWordList))
        plagiarism_status = (
            "Plagiarism Detected" if matchPercentage >= PLAGIARISM_THRESHOLD
            else "Limited Plagiarism" if matchPercentage > 0
            else "No Plagiarism"
        )
        
        # AI text detection
        ai_percentage = calculate_ai_percentage(inputQuery)
        is_ai_text = ai_percentage >= AI_GENERATED_THRESHOLD
        ai_text_detected = ai_percentage > AI_DETECTION_THRESHOLD
        
        return render_template(
            'index.html',
            query=inputQuery,
            percentage=round(matchPercentage, 2),
            plagiarized_texts=plagiarizedTexts,
            ai_percentage=round(ai_percentage, 2),
            is_ai_text=is_ai_text,
            ai_text_detected=ai_text_detected,
            plagiarism_status=plagiarism_status
        )
    
    except Exception as e:
        return render_template('index.html', error=f"Error: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)  # Run in debug mode for development