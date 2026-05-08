import React, { memo } from 'react';

const ColormapSection = memo(({ colormap, onImageClick }) => {
  return (
    <section id={colormap} className="section">
      <h2 className="section-title">{colormap}</h2>
      <img
        src={`boy_01_PC_v2/${colormap}_comparison.png`}
        alt={`${colormap} comparison`}
        loading="lazy"
        onClick={(e) => onImageClick(e.target.src)}
      />
    </section>
  );
});

ColormapSection.displayName = 'ColormapSection';

export default ColormapSection;
