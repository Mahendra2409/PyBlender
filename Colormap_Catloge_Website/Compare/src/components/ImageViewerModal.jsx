import React, { useState, useRef, useEffect } from 'react';

const ImageViewerModal = ({ isOpen, imageSrc, onClose }) => {
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const containerRef = useRef(null);
  
  // Touch zoom state
  const [initialPinchDist, setInitialPinchDist] = useState(null);
  const initialScaleRef = useRef(1);
  const initialTranslateRef = useRef({ x: 0, y: 0 });
  const pinchCenterRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      resetView();
    } else {
      document.body.style.overflow = 'auto';
    }
    
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const resetView = () => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomSensitivity = 0.1;
    const delta = e.deltaY < 0 ? 1 : -1;
    let newScale = scale * (1 + delta * zoomSensitivity);
    newScale = Math.max(0.5, Math.min(newScale, 15));

    if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        // Mouse relative to container center (since transform-origin is center center)
        const mx = e.clientX - rect.left - rect.width / 2;
        const my = e.clientY - rect.top - rect.height / 2;
        
        const ratio = newScale / scale;
        const newTx = mx - (mx - translate.x) * ratio;
        const newTy = my - (my - translate.y) * ratio;
        
        setTranslate({ x: newTx, y: newTy });
    }

    setScale(newScale);
  };

  // Mouse events
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
    dragStart.current = {
      x: e.clientX - translate.x,
      y: e.clientY - translate.y
    };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setTranslate({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setInitialPinchDist(null);
  };

  // Touch helpers
  const getPinchDistance = (touches) => {
    return Math.hypot(
        touches[0].clientX - touches[1].clientX,
        touches[0].clientY - touches[1].clientY
    );
  };

  const getPinchCenter = (touches) => {
    return {
        x: (touches[0].clientX + touches[1].clientX) / 2,
        y: (touches[0].clientY + touches[1].clientY) / 2
    };
  };

  // Touch events (Mobile support)
  const handleTouchStart = (e) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      dragStart.current = {
        x: e.touches[0].clientX - translate.x,
        y: e.touches[0].clientY - translate.y
      };
      setInitialPinchDist(null);
    } else if (e.touches.length === 2) {
      setIsDragging(false);
      setInitialPinchDist(getPinchDistance(e.touches));
      initialScaleRef.current = scale;
      initialTranslateRef.current = translate;
      pinchCenterRef.current = getPinchCenter(e.touches);
    }
  };

  const handleTouchMove = (e) => {
    if (e.cancelable) e.preventDefault();

    if (isDragging && e.touches.length === 1 && !initialPinchDist) {
      setTranslate({
        x: e.touches[0].clientX - dragStart.current.x,
        y: e.touches[0].clientY - dragStart.current.y
      });
    } else if (e.touches.length === 2 && initialPinchDist) {
      const currentDist = getPinchDistance(e.touches);
      const currentCenter = getPinchCenter(e.touches);
      const distRatio = currentDist / initialPinchDist;
      
      let newScale = initialScaleRef.current * distRatio;
      newScale = Math.max(0.5, Math.min(newScale, 15));
      
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const mx = pinchCenterRef.current.x - rect.left - rect.width / 2;
        const my = pinchCenterRef.current.y - rect.top - rect.height / 2;
        
        const panX = currentCenter.x - pinchCenterRef.current.x;
        const panY = currentCenter.y - pinchCenterRef.current.y;
        
        const ratio = newScale / initialScaleRef.current;
        const newTx = mx - (mx - initialTranslateRef.current.x) * ratio + panX;
        const newTy = my - (my - initialTranslateRef.current.y) * ratio + panY;
        
        setTranslate({ x: newTx, y: newTy });
      }
      setScale(newScale);
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
    setInitialPinchDist(null);
  };

  // Attach non-passive event listeners for wheel and touchmove
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
      container.addEventListener('touchmove', handleTouchMove, { passive: false });
      
      return () => {
        container.removeEventListener('wheel', handleWheel);
        container.removeEventListener('touchmove', handleTouchMove);
      };
    }
  }, [scale, translate, isDragging, initialPinchDist]); 

  if (!isOpen) return null;

  return (
    <div className="viewer-modal active">
      <button className="viewer-close" onClick={onClose}>&times;</button>
      <div 
        ref={containerRef}
        className="viewer-container" 
        onClick={(e) => { if (e.target === containerRef.current) onClose(); }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={handleTouchEnd}
      >
        <img 
          id="viewerImage" 
          src={imageSrc} 
          alt="Zoomable Comparison"
          style={{
            transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
            transition: (isDragging || initialPinchDist) ? 'none' : 'transform 0.15s ease-out'
          }}
        />
      </div>
      <div className="viewer-controls">
        <span>Scroll wheel to zoom, Click & Drag to pan</span>
        <button className="reset-btn" onClick={resetView}>Reset View</button>
      </div>
    </div>
  );
};

export default ImageViewerModal;
