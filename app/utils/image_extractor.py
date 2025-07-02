"""
Enhanced image extraction and processing for the Super Agent.
This module provides advanced image extraction, selection, and integration capabilities.
"""

import re
import json
import logging
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.utils.mcp_client import MCPClient
from app.utils.direct_image_search import DirectImageSearch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageExtractor:
    """
    Enhanced image extraction and processing for the Super Agent.
    """

    def __init__(self, mcp_client=None):
        """
        Initialize the image extractor.

        Args:
            mcp_client (MCPClient, optional): MCP client for image search. If None, a new one will be created.
        """
        self.mcp_client = mcp_client or MCPClient(base_url="http://localhost:5011")
        logger.info("Initialized ImageExtractor with MCP client at http://localhost:5011")

        # Initialize direct image search
        self.direct_image_search = DirectImageSearch()
        logger.info("Initialized DirectImageSearch for fallback image search")

    def extract_images_from_browsed_pages(self, browsed_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract images from browsed pages.

        Args:
            browsed_pages (List[Dict]): List of browsed pages with content

        Returns:
            List[Dict]: List of extracted images with metadata
        """
        all_images = []

        for page in browsed_pages:
            url = page.get('url', '')
            title = page.get('title', 'Unknown')
            content = page.get('content', '')
            html = page.get('html', '')

            # If HTML is not available, try to fetch it
            if not html and url:
                try:
                    logger.info(f"HTML not available for {url}, trying to fetch it")
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        html = response.text
                        logger.info(f"Successfully fetched HTML for {url}")
                except Exception as e:
                    logger.error(f"Error fetching HTML for {url}: {str(e)}")

            # Extract images if HTML is available
            if html:
                try:
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extract images using various methods
                    page_images = self._extract_images_from_html(soup, url)

                    # Add page metadata to each image
                    for img in page_images:
                        img['source_url'] = url
                        img['source_title'] = title
                        img['relevance_score'] = self._calculate_image_relevance(img, content)

                    all_images.extend(page_images)
                    logger.info(f"Extracted {len(page_images)} images from {url}")
                except Exception as e:
                    logger.error(f"Error extracting images from {url}: {str(e)}")
            else:
                logger.warning(f"No HTML available for {url}, skipping image extraction")

        # Sort images by relevance score (higher is better)
        all_images.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        # Log the number of images extracted
        if all_images:
            logger.info(f"Extracted a total of {len(all_images)} images from {len(browsed_pages)} pages")
            # Log some sample images
            for i, img in enumerate(all_images[:3]):
                logger.info(f"Sample image {i+1}: {img.get('src', '')[:50]}...")
        else:
            logger.warning(f"No images extracted from {len(browsed_pages)} pages")

        return all_images

    def _extract_images_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract images from HTML using various methods.

        Args:
            soup (BeautifulSoup): BeautifulSoup object of the HTML
            base_url (str): Base URL for resolving relative URLs

        Returns:
            List[Dict]: List of extracted images
        """
        images = []

        try:
            # Method 1: Extract from img tags
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src', '')
                data_src = img.get('data-src', '')  # Some sites use data-src for lazy loading

                # Use data-src if src is empty or a placeholder
                if not src or src.startswith('data:') or 'placeholder' in src.lower():
                    src = data_src

                # Skip empty sources and SVGs (often icons)
                if not src or src.endswith('.svg'):
                    continue

                # Convert relative URLs to absolute
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                # Get metadata
                alt = img.get('alt', '')
                width = img.get('width', '')
                height = img.get('height', '')

                # Check if this is a substantial image
                if self._is_substantial_image(img, src, width, height, alt):
                    images.append({
                        'src': src,
                        'alt': alt,
                        'width': width,
                        'height': height,
                        'extraction_method': 'img_tag',
                        'parent_tag': img.parent.name if img.parent else None
                    })

            # Method 2: Extract from picture elements
            picture_tags = soup.find_all('picture')
            for picture in picture_tags:
                sources = picture.find_all('source', srcset=True)
                for source in sources:
                    srcset = source.get('srcset', '')
                    if srcset:
                        # Extract the first URL from srcset (usually highest quality)
                        srcset_parts = srcset.split(',')[0].strip().split(' ')[0]
                        if srcset_parts:
                            # Convert relative URLs to absolute
                            if not srcset_parts.startswith(('http://', 'https://')):
                                srcset_parts = urljoin(base_url, srcset_parts)

                            images.append({
                                'src': srcset_parts,
                                'alt': source.get('alt', picture.find('img').get('alt', '') if picture.find('img') else ''),
                                'width': source.get('width', ''),
                                'height': source.get('height', ''),
                                'extraction_method': 'picture_source',
                                'parent_tag': picture.parent.name if picture.parent else None
                            })

            # Method 3: Extract from background images in style attributes
            elements_with_style = soup.find_all(lambda tag: tag.has_attr('style'))
            for element in elements_with_style:
                style = element.get('style', '')
                if 'background-image' in style or 'background:' in style:
                    # Extract URL from background-image: url('...')
                    match = re.search(r"(?:background-image|background):\s*.*?url\(['\"]?([^'\"\)]+)['\"]?\)", style)
                    if match:
                        src = match.group(1)

                        # Skip data URLs
                        if src.startswith('data:'):
                            continue

                        # Convert relative URLs to absolute
                        if not src.startswith(('http://', 'https://')):
                            src = urljoin(base_url, src)

                        images.append({
                            'src': src,
                            'alt': element.get_text(strip=True)[:50] or 'Background image',
                            'width': '',
                            'height': '',
                            'extraction_method': 'background_image',
                            'parent_tag': element.name
                        })

            # Method 4: Extract from meta tags (Open Graph and Twitter)
            # Open Graph image
            og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'property': 'og:image'})
            if og_image and og_image.get('content'):
                src = og_image.get('content')
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                og_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'property': 'og:title'})
                og_title_text = og_title.get('content', '') if og_title else ''

                images.append({
                    'src': src,
                    'alt': og_title_text,
                    'width': '',
                    'height': '',
                    'extraction_method': 'og_meta',
                    'parent_tag': 'meta',
                    'relevance_score': 10  # High relevance for OG images
                })

            # Twitter image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', attrs={'property': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                src = twitter_image.get('content')
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                twitter_title = soup.find('meta', attrs={'name': 'twitter:title'}) or soup.find('meta', attrs={'property': 'twitter:title'})
                twitter_title_text = twitter_title.get('content', '') if twitter_title else ''

                images.append({
                    'src': src,
                    'alt': twitter_title_text,
                    'width': '',
                    'height': '',
                    'extraction_method': 'twitter_meta',
                    'parent_tag': 'meta',
                    'relevance_score': 9  # High relevance for Twitter images
                })

            # Method 5: Extract from link rel="image_src" tags
            link_image = soup.find('link', attrs={'rel': 'image_src'})
            if link_image and link_image.get('href'):
                src = link_image.get('href')
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                images.append({
                    'src': src,
                    'alt': soup.title.string if soup.title else '',
                    'width': '',
                    'height': '',
                    'extraction_method': 'link_image',
                    'parent_tag': 'link',
                    'relevance_score': 8  # High relevance for link images
                })

            # Method 6: Extract from JSON-LD structured data
            script_tags = soup.find_all('script', attrs={'type': 'application/ld+json'})
            for script in script_tags:
                try:
                    if script.string:
                        json_data = json.loads(script.string)
                        # Extract image from Article schema
                        if isinstance(json_data, dict):
                            image_url = None
                            if '@type' in json_data and json_data['@type'] in ['Article', 'NewsArticle', 'BlogPosting', 'Product']:
                                image_url = json_data.get('image', {}).get('url', None) if isinstance(json_data.get('image'), dict) else json_data.get('image', None)

                            if image_url:
                                if isinstance(image_url, list) and len(image_url) > 0:
                                    image_url = image_url[0] if isinstance(image_url[0], str) else image_url[0].get('url', '')

                                if isinstance(image_url, str) and image_url:
                                    # Convert relative URLs to absolute
                                    if not image_url.startswith(('http://', 'https://')):
                                        image_url = urljoin(base_url, image_url)

                                    images.append({
                                        'src': image_url,
                                        'alt': json_data.get('headline', '') or json_data.get('name', ''),
                                        'width': '',
                                        'height': '',
                                        'extraction_method': 'json_ld',
                                        'parent_tag': 'script',
                                        'relevance_score': 9  # High relevance for structured data images
                                    })
                except Exception as e:
                    logger.error(f"Error parsing JSON-LD: {str(e)}")

            # Remove duplicates based on src
            unique_images = []
            seen_urls = set()
            for img in images:
                if img['src'] not in seen_urls:
                    seen_urls.add(img['src'])
                    unique_images.append(img)

            logger.info(f"Extracted {len(unique_images)} unique images from HTML")
            return unique_images

        except Exception as e:
            logger.error(f"Error extracting images from HTML: {str(e)}")
            return []

    def _is_substantial_image(self, img_tag, src: str, width, height, alt: str) -> bool:
        """
        Determine if an image is substantial (not an icon, spacer, etc.).

        Args:
            img_tag: BeautifulSoup img tag
            src (str): Image source URL
            width: Width attribute value
            height: Height attribute value
            alt (str): Alt text

        Returns:
            bool: True if the image is substantial, False otherwise
        """
        # Check dimensions if available
        if width and height:
            try:
                w, h = int(width), int(height)
                # Larger images are more likely to be content-relevant
                if w >= 200 and h >= 200:
                    return True
                # Medium-sized images might be relevant
                elif w >= 100 and h >= 100:
                    # Check if the image has a descriptive alt text
                    if alt and len(alt) > 10:
                        return True
            except (ValueError, TypeError):
                pass

        # Check file extension for common image formats
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if any(src.lower().endswith(ext) for ext in image_extensions):
            return True

        # Check if image is in a relevant container
        parent = img_tag.parent
        if parent:
            # Images in articles, figures, or main content are likely relevant
            if parent.name in ['figure', 'article', 'main', 'section'] or \
               (parent.get('class') and any(c for c in parent.get('class') if 'content' in c.lower())):
                return True

        # Check for keywords in alt text or surrounding text
        if alt and any(keyword in alt.lower() for keyword in ['photo', 'image', 'picture', 'photograph']):
            return True

        # Default to False for small images without context
        return False

    def _calculate_image_relevance(self, image: Dict[str, Any], page_content: str = '') -> float:
        """
        Calculate a relevance score for an image based on various factors.

        Args:
            image (Dict): Image metadata
            page_content (str, optional): Content of the page. Defaults to empty string.

        Returns:
            float: Relevance score (higher is better)
        """
        score = 0.0

        # Factor 1: Image size (if available)
        try:
            width = int(image.get('width', 0))
            height = int(image.get('height', 0))
            area = width * height

            if area > 250000:  # Large image (500x500 or larger)
                score += 5.0
            elif area > 40000:  # Medium image (200x200 or larger)
                score += 3.0
            elif area > 10000:  # Small image (100x100 or larger)
                score += 1.0
        except (ValueError, TypeError):
            # If dimensions are not available or invalid, neutral score
            score += 2.0

        # Factor 2: Extraction method
        method = image.get('extraction_method', '')
        if method in ['og_meta', 'twitter_meta', 'json_ld']:
            score += 5.0  # High relevance for meta tags and structured data
        elif method == 'img_tag':
            score += 3.0  # Medium relevance for img tags
        elif method == 'picture_source':
            score += 4.0  # High-medium relevance for picture sources
        elif method == 'background_image':
            score += 2.0  # Lower relevance for background images
        elif method == 'link_image':
            score += 4.0  # High-medium relevance for link images

        # Factor 3: Parent tag context
        parent_tag = image.get('parent_tag', '')
        if parent_tag in ['figure', 'article', 'main', 'section']:
            score += 3.0  # High relevance for images in content containers
        elif parent_tag in ['div', 'span']:
            score += 1.0  # Medium relevance for general containers
        elif parent_tag == 'a':
            score += 2.0  # Medium-high relevance for linked images

        # Factor 4: Alt text quality
        alt_text = image.get('alt', '')
        if alt_text:
            if len(alt_text) > 30:
                score += 3.0  # High relevance for detailed alt text
            elif len(alt_text) > 10:
                score += 2.0  # Medium relevance for moderate alt text
            else:
                score += 0.5  # Low relevance for minimal alt text

        # Factor 5: Image URL analysis
        src = image.get('src', '')
        if 'hero' in src.lower() or 'banner' in src.lower() or 'cover' in src.lower():
            score += 3.0  # High relevance for hero/banner images
        if any(term in src.lower() for term in ['thumb', 'icon', 'logo', 'avatar']):
            score -= 2.0  # Lower relevance for thumbnails, icons, etc.

        # Factor 6: Content relevance (if page content is provided)
        if page_content:
            # Extract keywords from page content
            keywords = self._extract_keywords(page_content)

            # Check if any keywords appear in the image alt text or src
            keyword_matches = 0
            for keyword in keywords:
                if keyword.lower() in alt_text.lower():
                    keyword_matches += 1
                if keyword.lower() in src.lower():
                    keyword_matches += 0.5

            # Add score based on keyword matches
            score += min(keyword_matches * 0.5, 3.0)  # Cap at 3.0

        return max(0.0, score)  # Ensure score is not negative

    def search_images_for_topics(self, topics: List[str], num_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for images related to specific topics.

        Args:
            topics (List[str]): List of topics to search for
            num_results (int): Number of results per topic

        Returns:
            List[Dict]: List of image results
        """
        all_images = []

        for topic in topics:
            try:
                # First try using the MCP client
                try:
                    logger.info(f"Searching images for topic with MCP client: {topic}")
                    topic_images = self.mcp_client.search_images(topic, num_results=num_results)

                    # If successful, add the images
                    if topic_images:
                        # Add topic metadata to each image
                        for img in topic_images:
                            img['topic'] = topic
                            img['search_result'] = True

                        all_images.extend(topic_images)
                        logger.info(f"Found {len(topic_images)} images for topic with MCP client: {topic}")
                        continue  # Skip to next topic if successful
                except Exception as e:
                    logger.warning(f"MCP client image search failed for topic {topic}: {str(e)}")

                # Fall back to direct image search if MCP client fails
                logger.info(f"Falling back to direct image search for topic: {topic}")
                direct_images = self.direct_image_search.search_images(topic, num_results=num_results)

                # Add topic metadata to each image
                for img in direct_images:
                    img['topic'] = topic
                    img['search_result'] = True

                all_images.extend(direct_images)
                logger.info(f"Found {len(direct_images)} images for topic with direct search: {topic}")

            except Exception as e:
                logger.error(f"All image search methods failed for topic {topic}: {str(e)}")

        return all_images

    def match_images_to_sections(self, sections: List[Dict[str, Any]], images: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match images to content sections based on relevance.

        Args:
            sections (List[Dict]): List of content sections
            images (List[Dict]): List of available images

        Returns:
            Dict[str, List[Dict]]: Dictionary mapping section IDs to relevant images
        """
        section_images = {}

        for section in sections:
            section_id = section.get('id', '')
            section_title = section.get('title', '')
            section_content = section.get('content', '')

            # Skip sections without ID or content
            if not section_id or not section_content:
                continue

            # Find relevant images for this section
            relevant_images = []

            # Method 1: Direct keyword matching
            keywords = self._extract_keywords(section_title + " " + section_content[:500])

            for img in images:
                # Calculate a match score for this image and section
                match_score = 0

                # Check alt text for keyword matches
                alt_text = img.get('alt', '')
                for keyword in keywords:
                    if keyword.lower() in alt_text.lower():
                        match_score += 2

                # Check image source URL for keyword matches
                src = img.get('src', '')
                for keyword in keywords:
                    if keyword.lower() in src.lower():
                        match_score += 1

                # Check if image is from the same source as the section content
                if img.get('source_url') == section.get('source_url'):
                    match_score += 3

                # Add match score to image
                img_copy = img.copy()
                img_copy['match_score'] = match_score

                # Add to relevant images if score is positive
                if match_score > 0:
                    relevant_images.append(img_copy)

            # Sort by match score (higher is better)
            relevant_images.sort(key=lambda x: x.get('match_score', 0), reverse=True)

            # If no relevant images found, use the highest relevance images
            if not relevant_images and images:
                # Use top 2 images by relevance score
                relevant_images = sorted(
                    [img.copy() for img in images],
                    key=lambda x: x.get('relevance_score', 0),
                    reverse=True
                )[:2]

                # Mark these as fallback images
                for img in relevant_images:
                    img['fallback'] = True

            # Store images for this section
            section_images[section_id] = relevant_images[:3]  # Limit to top 3 images per section

        return section_images

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text (str): Text to extract keywords from

        Returns:
            List[str]: List of keywords
        """
        # Simple keyword extraction based on word frequency
        # In a real implementation, you might use NLP techniques

        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Count word frequency
        word_counts = {}
        for word in words:
            # Skip common stop words
            if word in ['the', 'and', 'for', 'with', 'that', 'this', 'are', 'from', 'have', 'has']:
                continue
            word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Return top keywords
        return [word for word, _ in sorted_words[:10]]

    def extract_content_sections(self, browsed_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content sections from browsed pages.

        Args:
            browsed_pages (List[Dict]): List of browsed pages

        Returns:
            List[Dict]: List of content sections
        """
        sections = []
        section_id = 0

        for page in browsed_pages:
            url = page.get('url', '')
            title = page.get('title', 'Unknown')
            content = page.get('content', '')
            html = page.get('html', '')

            # Skip pages without content
            if not content:
                continue

            # Create a main section for the page
            section_id += 1
            main_section = {
                'id': f'section_{section_id}',
                'title': title,
                'content': content[:1000],  # Limit content length
                'source_url': url,
                'source_title': title,
                'type': 'main'
            }
            sections.append(main_section)

            # Extract subsections if HTML is available
            if html:
                try:
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find headings (h1, h2, h3)
                    headings = soup.find_all(['h1', 'h2', 'h3'])

                    for heading in headings:
                        # Get heading text
                        heading_text = heading.get_text(strip=True)

                        # Skip empty headings
                        if not heading_text:
                            continue

                        # Get content following this heading
                        content = ''
                        current = heading.next_sibling

                        # Collect content until next heading or end
                        while current and current.name not in ['h1', 'h2', 'h3']:
                            if current.name in ['p', 'div', 'span', 'li', 'ul', 'ol']:
                                content += current.get_text(strip=True) + ' '
                            current = current.next_sibling

                        # Create a subsection if content is available
                        if content:
                            section_id += 1
                            subsection = {
                                'id': f'section_{section_id}',
                                'title': heading_text,
                                'content': content[:500],  # Limit content length
                                'source_url': url,
                                'source_title': title,
                                'type': 'subsection',
                                'heading_level': int(heading.name[1])
                            }
                            sections.append(subsection)

                except Exception as e:
                    logger.error(f"Error extracting sections from {url}: {str(e)}")

        return sections

    def process_summary_with_images(self, task_summary: str, section_images: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Process a task summary to include images.

        Args:
            task_summary (str): The task summary text
            section_images (Dict[str, List[Dict]]): Dictionary mapping section IDs to images

        Returns:
            str: The processed task summary with images
        """
        # Find image placeholders in the format [IMAGE: description]
        image_regex = r'\[IMAGE: (.+?)\]'

        # Find all image placeholders
        image_matches = re.findall(image_regex, task_summary)

        # If no image placeholders were found, try to add images to section headers
        if not image_matches:
            logger.info("No image placeholders found in task summary, adding images to section headers")
            return self._add_images_to_section_headers(task_summary, section_images)

        # Keep track of descriptions we've already processed
        processed_descriptions = {}

        # Keep track of image sources to prevent duplicates
        used_image_sources = set()

        # Flatten all available images
        all_images = []
        for section_id, images in section_images.items():
            all_images.extend(images)

        # Sort by relevance score (higher is better)
        all_images.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        # Process each image placeholder
        for description in image_matches:
            # Check if we've already processed this description
            if description in processed_descriptions:
                logger.info(f"Using cached image for: {description}")
                image_html = processed_descriptions[description]
                task_summary = task_summary.replace(f'[IMAGE: {description}]', image_html, 1)
                continue

            # Try to find a matching image from browsed pages
            best_image = None

            # Method 1: Look for direct keyword matches in alt text
            keywords = description.lower().split()
            for img in all_images:
                # Skip if we've already used this image source
                if img.get('src') in used_image_sources:
                    continue

                alt_text = img.get('alt', '').lower()
                if any(keyword in alt_text for keyword in keywords):
                    best_image = img
                    break

            # Method 2: If no match found, use the highest relevance image
            if not best_image and all_images:
                # Find the first image that hasn't been used yet
                for img in all_images:
                    if img.get('src') not in used_image_sources:
                        best_image = img
                        break

                # If all images have been used, use the first one anyway
                if not best_image and all_images:
                    best_image = all_images[0]

                # Remove this image from the list to avoid reusing it
                if best_image in all_images:
                    all_images.remove(best_image)

            # Method 3: If no browsed images available, search for an image
            if not best_image:
                try:
                    # First try MCP client
                    logger.info(f"No matching image found, searching with MCP client for: {description}")
                    search_results = self.mcp_client.search_images(description, num_results=1)
                    if search_results:
                        best_image = search_results[0]
                        logger.info(f"Found image with MCP client for: {description}")
                except Exception as e:
                    logger.warning(f"MCP client image search failed: {str(e)}")

                # Fall back to direct image search if MCP client fails
                if not best_image:
                    try:
                        logger.info(f"Falling back to direct image search for: {description}")
                        direct_results = self.direct_image_search.search_images(description, num_results=1)
                        if direct_results:
                            best_image = direct_results[0]
                            logger.info(f"Found image with direct search for: {description}")
                    except Exception as e:
                        logger.error(f"Direct image search failed: {str(e)}")

            # If we found an image, use it
            if best_image:
                try:
                    logger.info(f"Using image: {best_image.get('src', '')[:50]}...")
                    # Add to used sources to prevent duplicates
                    if best_image.get('src'):
                        used_image_sources.add(best_image['src'])

                    # Create HTML for the image without container - directly integrated with text
                    image_html = f'''
                    <img src="{best_image["src"]}" alt="{description}" style="object-fit: contain; width: auto; max-height: 400px; margin: 1.5rem auto; display: block;">
                    <p style="text-align: center; font-size: 0.9rem; color: #666; font-style: italic; margin-top: -0.5rem; margin-bottom: 1.5rem;">{description}</p>
                    '''
                    task_summary = task_summary.replace(f'[IMAGE: {description}]', image_html, 1)
                    # Cache this image for future occurrences of the same description
                    processed_descriptions[description] = image_html
                except Exception as e:
                    logger.error(f"Error using image: {str(e)}")
                    # Fall back to placeholder
                    placeholder_url = f'https://placehold.co/800x400/f5f5f5/333333?text={description.replace(" ", "+")}'
                    image_html = f'''
                    <img src="{placeholder_url}" alt="{description}" style="object-fit: contain; width: auto; max-height: 400px; margin: 1.5rem auto; display: block;">
                    <p style="text-align: center; font-size: 0.9rem; color: #666; font-style: italic; margin-top: -0.5rem; margin-bottom: 1.5rem;">{description}</p>
                    '''
                    task_summary = task_summary.replace(f'[IMAGE: {description}]', image_html, 1)
                    processed_descriptions[description] = image_html
            else:
                logger.info(f"No image found for: {description}, using placeholder")
                # If no image was found, use a placeholder
                placeholder_url = f'https://placehold.co/800x400/f5f5f5/333333?text={description.replace(" ", "+")}'
                image_html = f'''
                <img src="{placeholder_url}" alt="{description}" style="object-fit: contain; width: auto; max-height: 400px; margin: 1.5rem auto; display: block;">
                <p style="text-align: center; font-size: 0.9rem; color: #666; font-style: italic; margin-top: -0.5rem; margin-bottom: 1.5rem;">{description}</p>
                '''
                task_summary = task_summary.replace(f'[IMAGE: {description}]', image_html, 1)
                # Cache this placeholder for future occurrences
                processed_descriptions[description] = image_html

        return task_summary

    def _add_images_to_section_headers(self, task_summary: str, section_images: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Add images to section headers in the task summary.

        Args:
            task_summary (str): The task summary text
            section_images (Dict[str, List[Dict]]): Dictionary mapping section IDs to images

        Returns:
            str: The processed task summary with images added to section headers
        """
        # Find section headers in the format ## Section Title
        section_regex = r'(^|\n)## ([^\n]+)'

        # Find all section headers
        section_matches = re.findall(section_regex, task_summary)

        if not section_matches:
            logger.info("No section headers found in task summary")
            return task_summary

        # Keep track of image sources to prevent duplicates
        used_image_sources = set()

        # Flatten all available images
        all_images = []
        for section_id, images in section_images.items():
            all_images.extend(images)

        # If no images available, try to search for images based on the task summary title
        if not all_images:
            try:
                # Extract the title from the task summary (first line after #)
                title_match = re.search(r'^# ([^\n]+)', task_summary)
                if title_match:
                    title = title_match.group(1)
                    # First try MCP client
                    try:
                        logger.info(f"Searching for images based on title with MCP client: {title}")
                        search_results = self.mcp_client.search_images(title, num_results=3)
                        if search_results:
                            all_images.extend(search_results)
                            logger.info(f"Found {len(search_results)} images with MCP client for title: {title}")
                    except Exception as e:
                        logger.warning(f"MCP client image search failed for title: {str(e)}")

                    # Fall back to direct image search if MCP client fails or returns no results
                    if not all_images:
                        try:
                            logger.info(f"Falling back to direct image search for title: {title}")
                            direct_results = self.direct_image_search.search_images(title, num_results=3)
                            if direct_results:
                                all_images.extend(direct_results)
                                logger.info(f"Found {len(direct_results)} images with direct search for title: {title}")
                        except Exception as e:
                            logger.error(f"Direct image search failed for title: {str(e)}")
            except Exception as e:
                logger.error(f"Error searching for images based on title: {str(e)}")

        # Sort by relevance score (higher is better)
        all_images.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        # If still no images available, return the original summary
        if not all_images:
            logger.info("No images available for section headers")
            return task_summary

        # Process each section header
        for i, (prefix, section_title) in enumerate(section_matches):
            # Skip if we've used all images
            if i >= len(all_images):
                break

            # Find an image that hasn't been used yet
            image = None
            for img in all_images:
                if img.get('src') not in used_image_sources:
                    image = img
                    # Add to used sources
                    if img.get('src'):
                        used_image_sources.add(img['src'])
                    break

            # If all images have been used, use the first one
            if not image and all_images:
                image = all_images[i % len(all_images)]

            # Skip if no image is available
            if not image:
                continue

            # Create HTML for the image with improved styling
            try:
                image_html = f'''

<img src="{image["src"]}" alt="{section_title}" style="object-fit: contain; width: auto; max-height: 400px; margin: 1.5rem auto; display: block;">
<p style="text-align: center; font-size: 0.9rem; color: #666; font-style: italic; margin-top: -0.5rem; margin-bottom: 1.5rem;">{section_title}</p>

                '''

                # Replace the section header with the section header + image
                old_header = f"{prefix}## {section_title}"
                new_header = f"{prefix}## {section_title}{image_html}"
                task_summary = task_summary.replace(old_header, new_header, 1)
            except Exception as e:
                logger.error(f"Error adding image to section header: {str(e)}")

        return task_summary
