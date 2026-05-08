import React, { useState, useCallback } from 'react';
import colormaps from './colormaps.json';
import Sidebar from './components/Sidebar';
import ColormapSection from './components/ColormapSection';
import ImageViewerModal from './components/ImageViewerModal';
import { useScrollSpy } from './hooks/useScrollSpy';

const App = () => {
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [currentImage, setCurrentImage] = useState('');
  
  const { activeSection } = useScrollSpy(colormaps);

  const openViewer = useCallback((src) => {
    setCurrentImage(src);
    setIsViewerOpen(true);
  }, []);

  const closeViewer = () => {
    setIsViewerOpen(false);
  };

  return (
    <>
      <div className="layout">
        <Sidebar colormaps={colormaps} activeSection={activeSection} />
        <main className="main-content">
          {colormaps.map((colormap) => (
            <ColormapSection 
              key={colormap} 
              colormap={colormap} 
              onImageClick={openViewer}
            />
          ))}
        </main>
      </div>

      <ImageViewerModal 
        isOpen={isViewerOpen} 
        imageSrc={currentImage} 
        onClose={closeViewer} 
      />
    </>
  );
};

export default App;
