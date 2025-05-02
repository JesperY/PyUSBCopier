import sys
import os
from PyQt6.QtGui import QIcon, QPixmap
from ..core.logger import logger

def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for both development and packaged environments
    
    Args:
        relative_path: Path relative to the resources directory
        
    Returns:
        Absolute path to the resource
    """
    try:
        if getattr(sys, 'frozen', False):
            # If in packaged environment
            base_path = sys._MEIPASS
            
            # First check if the file is in the top level directory
            direct_path = os.path.join(base_path, relative_path)
            logger.debug(f"Packaged env: Looking for resource (top level) {relative_path} at {direct_path}")
            if os.path.exists(direct_path):
                logger.debug(f"Found resource in top level directory: {direct_path}")
                return direct_path
                
            # Then check in the resources subdirectory
            full_path = os.path.join(base_path, 'resources', relative_path)
            logger.debug(f"Packaged env: Looking for resource (subdirectory) {relative_path} at {full_path}")
            if os.path.exists(full_path):
                logger.debug(f"Found resource in resources subdirectory: {full_path}")
                return full_path
            
            # Check src/resources as another possibility
            src_res_path = os.path.join(base_path, 'src', 'resources', relative_path)
            logger.debug(f"Packaged env: Looking for resource in src/resources: {src_res_path}")
            if os.path.exists(src_res_path):
                logger.debug(f"Found resource in src/resources: {src_res_path}")
                return src_res_path
                
            logger.warning(f"Resource not found in packaged environment: {relative_path}")
            return direct_path  # Return top level path
        
        # If in development environment
        # First try to load from src/resources directory
        current_dir = os.path.dirname(os.path.abspath(__file__))  # gui directory
        src_dir = os.path.dirname(current_dir)  # src directory
        resources_dir = os.path.join(src_dir, 'resources')
        
        resource_path = os.path.join(resources_dir, relative_path)
        logger.debug(f"Dev env: Looking for resource {relative_path} at {resource_path}")
        
        if os.path.exists(resource_path):
            logger.debug(f"Found resource at {resource_path}")
            return resource_path
        
        # If not found in src/resources, try the project root
        project_root = os.path.dirname(src_dir)
        resource_path = os.path.join(project_root, relative_path)
        logger.debug(f"Looking for resource in root directory {resource_path}")
        
        if os.path.exists(resource_path):
            logger.debug(f"Found resource at {resource_path}")
            return resource_path
        
        # If still not found, return relative path
        logger.warning(f"Resource not found: {relative_path}, returning relative path")
        return relative_path
    except Exception as e:
        logger.error(f"Error getting resource path: {e}")
        return relative_path

def get_icon_path(icon_name='icon.ico'):
    """Get the path to an icon file
    
    Args:
        icon_name: Icon filename, defaults to icon.ico
        
    Returns:
        Full path to the icon file
    """
    path = get_resource_path(icon_name)
    exists = os.path.exists(path)
    logger.info(f"Icon path: {path}, file exists: {exists}")
    return path

def get_icon(icon_name='icon.ico'):
    """Get the application icon
    
    Args:
        icon_name: Icon filename, defaults to icon.ico
        
    Returns:
        QIcon object
    """
    try:
        # Try different approaches to load the icon
        # Approach 1: Direct path
        icon_path = get_icon_path(icon_name)
        if os.path.exists(icon_path):
            # Create icon from direct file path
            icon = QIcon(icon_path)
            if not icon.isNull():
                logger.info(f"Successfully loaded icon from path: {icon_path}")
                return icon
            logger.warning(f"Icon loaded from {icon_path} is null/empty")
        
        # Approach 2: Try PNG format
        if icon_name.endswith('.ico'):
            png_name = icon_name.replace('.ico', '.png')
            png_path = get_icon_path(png_name)
            if os.path.exists(png_path):
                icon = QIcon(png_path)
                if not icon.isNull():
                    logger.info(f"Successfully loaded PNG icon from path: {png_path}")
                    return icon
                logger.warning(f"PNG icon loaded from {png_path} is null/empty")
        
        # Approach 3: Use a fallback icon from standard Qt resources
        logger.warning("Using fallback standard application icon")
        icon = QIcon.fromTheme("application")
        if not icon.isNull():
            return icon
            
        # Approach 4: Create a simple colored square icon as last resort
        logger.warning("Creating simple colored square icon as fallback")
        pixmap = QPixmap(64, 64)
        pixmap.fill('blue')  # Create a blue square as default icon
        return QIcon(pixmap)
        
    except Exception as e:
        logger.error(f"Error creating icon: {e}")
        # Create emergency fallback icon
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill('red')  # Create a red square as emergency icon
            return QIcon(pixmap)
        except:
            # Last resort - empty icon
            return QIcon()

def get_png_icon(icon_name='icon.png'):
    """Get the application icon in PNG format
    
    Args:
        icon_name: PNG icon filename, defaults to icon.png
        
    Returns:
        QIcon object
    """
    return get_icon(icon_name) 