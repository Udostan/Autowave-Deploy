"""
Enhanced File Processing Service
Processes uploaded files for all agents to understand and use in their tasks.
"""

import base64
import json
import re
import logging
from typing import Dict, List, Any, Optional
from PIL import Image
import io
import PyPDF2
import docx
import csv
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class FileProcessor:
    """Enhanced file processor that can handle various file types and extract meaningful content."""
    
    def __init__(self):
        self.supported_text_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.xml', '.csv',
            '.yaml', '.yml', '.sql', '.sh', '.bat', '.log', '.ini', '.cfg', '.conf'
        }
        
        self.supported_image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'
        }
        
        self.supported_document_extensions = {
            '.pdf', '.doc', '.docx'
        }
    
    def process_file_content(self, file_content: str) -> Dict[str, Any]:
        """
        Process file content from the universal file upload system.
        
        Args:
            file_content (str): The file content string from getFileContentForAI()
            
        Returns:
            Dict containing processed file information and enhanced content
        """
        try:
            processed_files = []
            
            # Parse the file content string
            files_info = self._parse_file_content_string(file_content)
            
            for file_info in files_info:
                processed_file = self._process_single_file(file_info)
                if processed_file:
                    processed_files.append(processed_file)
            
            return {
                'success': True,
                'files_count': len(processed_files),
                'processed_files': processed_files,
                'summary': self._generate_files_summary(processed_files)
            }
            
        except Exception as e:
            logger.error(f"Error processing file content: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files_count': 0,
                'processed_files': []
            }
    
    def _parse_file_content_string(self, content: str) -> List[Dict[str, Any]]:
        """Parse the file content string to extract individual files."""
        files = []
        
        # Pattern to match file sections
        file_pattern = r'--- File: ([^-]+) ---\n(.*?)(?=\n--- |$)'
        image_pattern = r'--- Image: ([^(]+) \(([^)]+)\) ---\n(.*?)(?=\n--- |$)'
        
        # Find text files
        for match in re.finditer(file_pattern, content, re.DOTALL):
            filename = match.group(1).strip()
            file_content = match.group(2).strip()
            
            files.append({
                'name': filename,
                'type': 'text',
                'content': file_content,
                'extension': self._get_file_extension(filename)
            })
        
        # Find images
        for match in re.finditer(image_pattern, content, re.DOTALL):
            filename = match.group(1).strip()
            mime_type = match.group(2).strip()
            image_data = match.group(3).strip()

            files.append({
                'name': filename,
                'type': 'image',
                'mime_type': mime_type,
                'content': image_data,
                'extension': self._get_file_extension(filename)
            })
        
        return files
    
    def _process_single_file(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single file and extract meaningful information."""
        try:
            filename = file_info['name']
            file_type = file_info['type']
            extension = file_info['extension']
            
            processed = {
                'filename': filename,
                'type': file_type,
                'extension': extension,
                'analysis': {},
                'ai_instructions': []
            }
            
            if file_type == 'text':
                processed.update(self._process_text_file(file_info))
            elif file_type == 'image':
                processed.update(self._process_image_file(file_info))
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing file {file_info.get('name', 'unknown')}: {str(e)}")
            return None
    
    def _process_text_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-based files and extract meaningful information."""
        content = file_info['content']
        extension = file_info['extension']
        
        analysis = {
            'line_count': len(content.split('\n')),
            'character_count': len(content),
            'word_count': len(content.split())
        }
        
        ai_instructions = []
        
        # Language-specific processing
        if extension in ['.py']:
            analysis.update(self._analyze_python_code(content))
            ai_instructions.append("This is Python code. You can analyze its functionality, suggest improvements, debug issues, or explain how it works.")
            
        elif extension in ['.js']:
            analysis.update(self._analyze_javascript_code(content))
            ai_instructions.append("This is JavaScript code. You can analyze its functionality, suggest improvements, debug issues, or explain how it works.")
            
        elif extension in ['.html']:
            analysis.update(self._analyze_html_content(content))
            ai_instructions.append("This is HTML content. You can analyze the structure, suggest improvements, or help with web development tasks.")
            
        elif extension in ['.css']:
            analysis.update(self._analyze_css_content(content))
            ai_instructions.append("This is CSS styling code. You can analyze the styles, suggest improvements, or help with design tasks.")
            
        elif extension in ['.json']:
            analysis.update(self._analyze_json_content(content))
            ai_instructions.append("This is JSON data. You can analyze the structure, validate the format, or help with data processing tasks.")
            
        elif extension in ['.md']:
            analysis.update(self._analyze_markdown_content(content))
            ai_instructions.append("This is Markdown content. You can analyze the structure, suggest improvements, or help with documentation tasks.")
            
        elif extension in ['.csv']:
            analysis.update(self._analyze_csv_content(content))
            ai_instructions.append("This is CSV data. You can analyze the data structure, perform data analysis, or help with data processing tasks.")
            
        else:
            ai_instructions.append("This is a text file. You can analyze its content, summarize it, or help with any text-related tasks.")
        
        return {
            'analysis': analysis,
            'ai_instructions': ai_instructions,
            'content_preview': content[:500] + "..." if len(content) > 500 else content
        }
    
    def _process_image_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process image files."""
        filename = file_info['name']
        mime_type = file_info.get('mime_type', 'image/unknown')
        image_data = file_info.get('content', '')

        analysis = {
            'mime_type': mime_type,
            'format': mime_type.split('/')[-1] if '/' in mime_type else 'unknown',
            'has_data': bool(image_data and image_data.startswith('data:'))
        }

        ai_instructions = []

        if image_data and image_data.startswith('data:'):
            # We have actual image data
            ai_instructions = [
                "This is an image file with actual image data provided.",
                "You can analyze the image content, describe what you see, extract text if it contains any, or help with image-related tasks.",
                "The image data is provided as a base64-encoded data URL that you can process.",
                f"Image format: {analysis['format']}",
                f"Filename: {filename}"
            ]
        else:
            # Fallback for when image data is not available
            ai_instructions = [
                "This is an image file. You can provide guidance based on the filename and type.",
                f"Image format: {analysis['format']}",
                f"Filename: {filename}",
                "Note: The actual image data is not available in this context."
            ]

        return {
            'analysis': analysis,
            'ai_instructions': ai_instructions,
            'content': image_data if image_data else f"Image file: {filename}"
        }
    
    def _analyze_python_code(self, content: str) -> Dict[str, Any]:
        """Analyze Python code content."""
        analysis = {}
        
        # Count imports
        import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
        analysis['import_count'] = len(import_lines)
        analysis['imports'] = import_lines[:10]  # First 10 imports
        
        # Count functions and classes
        function_count = len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
        class_count = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        
        analysis['function_count'] = function_count
        analysis['class_count'] = class_count
        
        # Detect common patterns
        if 'flask' in content.lower():
            analysis['framework'] = 'Flask'
        elif 'django' in content.lower():
            analysis['framework'] = 'Django'
        elif 'fastapi' in content.lower():
            analysis['framework'] = 'FastAPI'
        
        return analysis
    
    def _analyze_javascript_code(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code content."""
        analysis = {}
        
        # Count functions
        function_count = len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*:\s*function', content))
        analysis['function_count'] = function_count
        
        # Detect frameworks/libraries
        if 'react' in content.lower():
            analysis['framework'] = 'React'
        elif 'vue' in content.lower():
            analysis['framework'] = 'Vue'
        elif 'angular' in content.lower():
            analysis['framework'] = 'Angular'
        elif 'jquery' in content.lower():
            analysis['library'] = 'jQuery'
        
        return analysis
    
    def _analyze_html_content(self, content: str) -> Dict[str, Any]:
        """Analyze HTML content."""
        analysis = {}
        
        # Count elements
        tag_count = len(re.findall(r'<[^/][^>]*>', content))
        analysis['tag_count'] = tag_count
        
        # Detect common elements
        if '<form' in content:
            analysis['has_forms'] = True
        if '<table' in content:
            analysis['has_tables'] = True
        if '<script' in content:
            analysis['has_scripts'] = True
        
        return analysis
    
    def _analyze_css_content(self, content: str) -> Dict[str, Any]:
        """Analyze CSS content."""
        analysis = {}
        
        # Count selectors and rules
        selector_count = len(re.findall(r'[^{}]+\s*{', content))
        analysis['selector_count'] = selector_count
        
        return analysis
    
    def _analyze_json_content(self, content: str) -> Dict[str, Any]:
        """Analyze JSON content."""
        analysis = {}
        
        try:
            data = json.loads(content)
            analysis['valid_json'] = True
            analysis['structure'] = type(data).__name__
            
            if isinstance(data, dict):
                analysis['key_count'] = len(data.keys())
                analysis['top_level_keys'] = list(data.keys())[:10]
            elif isinstance(data, list):
                analysis['item_count'] = len(data)
                
        except json.JSONDecodeError:
            analysis['valid_json'] = False
            analysis['error'] = 'Invalid JSON format'
        
        return analysis
    
    def _analyze_markdown_content(self, content: str) -> Dict[str, Any]:
        """Analyze Markdown content."""
        analysis = {}
        
        # Count headers
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        analysis['header_count'] = len(headers)
        analysis['headers'] = headers[:5]  # First 5 headers
        
        # Count links and images
        links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
        
        analysis['link_count'] = len(links)
        analysis['image_count'] = len(images)
        
        return analysis
    
    def _analyze_csv_content(self, content: str) -> Dict[str, Any]:
        """Analyze CSV content."""
        analysis = {}
        
        lines = content.split('\n')
        analysis['row_count'] = len([line for line in lines if line.strip()])
        
        if lines:
            # Analyze first row as headers
            first_row = lines[0].split(',')
            analysis['column_count'] = len(first_row)
            analysis['headers'] = [col.strip().strip('"') for col in first_row]
        
        return analysis
    
    def _generate_files_summary(self, processed_files: List[Dict[str, Any]]) -> str:
        """Generate a summary of all processed files for AI context."""
        if not processed_files:
            return "No files were uploaded."
        
        summary_parts = [f"User uploaded {len(processed_files)} file(s):"]
        
        for file_data in processed_files:
            filename = file_data['filename']
            file_type = file_data['type']
            analysis = file_data.get('analysis', {})
            
            if file_type == 'text':
                lines = analysis.get('line_count', 0)
                words = analysis.get('word_count', 0)
                summary_parts.append(f"- {filename}: {lines} lines, {words} words")
                
                # Add specific details
                if 'framework' in analysis:
                    summary_parts.append(f"  Framework: {analysis['framework']}")
                if 'function_count' in analysis:
                    summary_parts.append(f"  Functions: {analysis['function_count']}")
                if 'class_count' in analysis:
                    summary_parts.append(f"  Classes: {analysis['class_count']}")
                    
            elif file_type == 'image':
                format_type = analysis.get('format', 'unknown')
                summary_parts.append(f"- {filename}: {format_type} image")
        
        return "\n".join(summary_parts)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    def enhance_prompt_with_files(self, original_prompt: str, file_content: str) -> str:
        """
        Enhance the original prompt with processed file information.
        
        Args:
            original_prompt (str): The user's original request
            file_content (str): The raw file content from universal file upload
            
        Returns:
            str: Enhanced prompt with file analysis and instructions
        """
        if not file_content.strip():
            return original_prompt
        
        processed = self.process_file_content(file_content)
        
        if not processed['success'] or not processed['processed_files']:
            return original_prompt
        
        # Build enhanced prompt
        enhanced_parts = [
            original_prompt,
            "\n\n=== UPLOADED FILES ANALYSIS ===",
            processed['summary'],
            "\n=== AI PROCESSING INSTRUCTIONS ==="
        ]
        
        for file_data in processed['processed_files']:
            enhanced_parts.append(f"\nFor {file_data['filename']}:")
            for instruction in file_data['ai_instructions']:
                enhanced_parts.append(f"- {instruction}")

            # Include actual content for processing
            if 'content' in file_data and file_data['content']:
                if file_data.get('analysis', {}).get('has_data'):
                    # For images with actual data, include the base64 data
                    enhanced_parts.append(f"\nImage data:\n{file_data['content']}")
                elif 'content_preview' in file_data:
                    # For text files, include preview
                    enhanced_parts.append(f"\nContent preview:\n{file_data['content_preview']}")
            elif 'content_preview' in file_data:
                enhanced_parts.append(f"\nContent preview:\n{file_data['content_preview']}")
        
        enhanced_parts.append("\n=== END FILE ANALYSIS ===")
        enhanced_parts.append("\nPlease use this file information to better understand and complete the user's request.")
        
        return "\n".join(enhanced_parts)

# Global instance
file_processor = FileProcessor()
