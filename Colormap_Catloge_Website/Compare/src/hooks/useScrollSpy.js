import { useState, useEffect, useRef } from 'react';

export const useScrollSpy = (colormaps) => {
  const [activeSection, setActiveSection] = useState(colormaps[0] || '');
  const observer = useRef(null);

  useEffect(() => {
    observer.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.3 }
    );

    // Give React a brief moment to ensure all elements are mounted
    setTimeout(() => {
      colormaps.forEach((id) => {
        const el = document.getElementById(id);
        if (el) observer.current.observe(el);
      });
    }, 100);

    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, [colormaps]);

  return { activeSection };
};
