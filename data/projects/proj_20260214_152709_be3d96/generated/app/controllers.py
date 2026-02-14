from flask import Blueprint, request, jsonify
from app.services.content_generator import ContentGenerator
from app.models import ProductContent

controllers = Blueprint('controllers', __name__)

# Route to handle product content generation
@controllers.route('/generate-content', methods=['POST'])
def generate_content():
    try:
        # Check for required fields in the request
        if 'image' not in request.files or 'description' not in request.form:
            return jsonify({'error': 'Missing required fields: image and/or description'}), 400

        # Retrieve uploaded image and description
        image = request.files['image']
        description = request.form['description']

        # Validate inputs
        if not image.filename or not description.strip():
            return jsonify({'error': 'Invalid input: image file or description is empty'}), 400

        # Initialize content generator service
        generator = ContentGenerator()

        # Generate product content
        product_title, selling_points = generator.generate(image, description)

        # Save product content to database
        product_content = ProductContent(title=product_title, selling_points=selling_points)
        product_content.save()

        # Return generated content
        return jsonify({
            'title': product_title,
            'selling_points': selling_points
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500