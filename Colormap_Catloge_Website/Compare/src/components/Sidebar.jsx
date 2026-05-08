import React, { useState } from 'react';

const Sidebar = ({ colormaps, activeSection }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <div className="mobile-header">
        <div className="mobile-title">
          <h1>Boy 01 Pc V2</h1>
          <p>Colormap Catalog</p>
        </div>
        <button className="menu-btn" onClick={() => setIsOpen(!isOpen)} aria-label="Toggle Menu">
          ☰
        </button>
      </div>

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h1>Boy 01 Pc V2</h1>
          <p>Colormap Comparison Catalog</p>
        </div>
        <nav id="toc">
          {colormaps.map((colormap) => (
            <a
              key={colormap}
              href={`#${colormap}`}
              className={`nav-link ${activeSection === colormap ? 'active' : ''}`}
              id={`link-${colormap}`}
              onClick={() => setIsOpen(false)}
            >
              {colormap.toUpperCase()}
            </a>
          ))}
        </nav>
      </aside>
      
      {isOpen && <div className="sidebar-overlay" onClick={() => setIsOpen(false)}></div>}
    </>
  );
};

export default Sidebar;
