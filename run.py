import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("Python path:", sys.path)

try:
    from app import create_app
    print("Successfully imported create_app")

    app = create_app()
    print("Successfully created app")

except Exception as e:
    print(f"Error creating application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Make app available for Gunicorn
if __name__ == '__main__':
    try:
        print("Starting Flask server on port 5001...")
        port = int(os.environ.get('PORT', 5001))
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

        # Production optimizations
        if not debug_mode:
            print("Running in PRODUCTION mode")
            # Disable debug mode for production
            app.config['DEBUG'] = False
            # Enable threaded mode for better concurrency
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        else:
            print("Running in DEVELOPMENT mode")
            app.run(host='0.0.0.0', port=port, debug=True)

        print("Flask server started successfully")

    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
