import cv2


class VideoSource:
    """
    Handles video input from webcam or video file sources.
    Provides a unified interface for reading frames from different sources.
    """
    
    def __init__(self, source):
        """
        Initialize video source.
        
        Args:
            source: int (webcam device index, e.g., 0) or str (video file path)
        
        Raises:
            ValueError: If the video source cannot be opened
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)
        
        # Validate source availability on initialization
        if not self.cap.isOpened():
            error_msg = f"Failed to open video source: {source}"
            if isinstance(source, int):
                error_msg += " (webcam not available)"
            else:
                error_msg += " (file not found or invalid format)"
            raise ValueError(error_msg)
    
    def read(self):
        """
        Read a frame from the video source.
        
        Returns:
            numpy.ndarray: BGR image frame, or None if video ends or source unavailable
        """
        if not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        
        # Return None when video ends or read fails
        if not ret:
            return None
        
        return frame
    
    def release(self):
        """
        Release video capture resources.
        Should be called when done using the video source.
        """
        if self.cap is not None:
            self.cap.release()
