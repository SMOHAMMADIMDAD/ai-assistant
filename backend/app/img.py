import os
from google import genai

from PIL import Image
from io import BytesIO
from dotenv import load_dotenv # <--- ADD THIS LINE
load_dotenv()
# --- 1. Configuration ---
# Make sure you have set your GOOGLE_API_KEY as an environment variable
# For example: export GOOGLE_API_KEY='YOUR_API_KEY_HERE'
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

# --- 2. Define the Image Generation Function ---
def generate_and_save_image(prompt: str, filename: str = "generated_image.png"):
    """
    Generates an image using the specified model and saves it to a file.
    """
    try:
        print(f"Initializing model: gemini-2.5-flash-image-preview...")
        # Initialize the specific model for image generation
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-image-preview")

        print(f"Sending prompt to the API: '{prompt}'...")
        # Generate the image content
        response = model.generate_content(prompt)

        # --- 3. Extract and Process the Image Data ---
        # The image data is located in a specific part of the response structure
        image_data = response.candidates[0].content.parts[0].inline_data.data

        # Use BytesIO to handle the raw binary data in memory
        image_bytes = BytesIO(image_data)

        # Open the image using the Pillow library
        image = Image.open(image_bytes)

        # --- 4. Save the Image ---
        print(f"Saving image to '{filename}'...")
        image.save(filename)
        print("Image generation successful!")

    except Exception as e:
        print(f"An error occurred during image generation: {e}")

# --- 5. Run the Generator ---
if __name__ == "__main__":
    # Define your prompt for the image
    user_prompt = "A high-detail, photorealistic image of a majestic lion with a golden mane, standing on a rocky cliff at sunrise."

    # Define the output filename
    output_filename = "majestic_lion.png"

    # Call the function to generate and save the image
    generate_and_save_image(user_prompt, output_filename)
