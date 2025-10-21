import React, { useRef, useState } from 'react';
import { SvgFullscreenModal } from './SvgFullscreenModal';

interface SvgWithFullscreenProps {
  svgContent: string;
  className?: string;
}

export function SvgWithFullscreen({ svgContent, className = '' }: SvgWithFullscreenProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleFullscreen = () => {
    setIsFullscreen(true);
  };

  const handleCloseFullscreen = () => {
    setIsFullscreen(false);
  };

  return (
    <>
      <div 
        ref={wrapperRef}
        className={`svg-zoom-wrapper ${className}`}
        style={{ position: 'relative' }}
      >
        <div dangerouslySetInnerHTML={{ __html: svgContent }} />
        
        {/* 全屏按钮 */}
        <button
          onClick={handleFullscreen}
          className="fullscreen-btn"
          aria-label="全屏显示"
          title="全屏显示"
          style={{ 
            position: 'absolute', 
            top: '8px', 
            right: '8px', 
            zIndex: 1001,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            opacity: 0.7
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '1';
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '0.7';
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
          </svg>
        </button>
      </div>

      <SvgFullscreenModal
        isOpen={isFullscreen}
        onClose={handleCloseFullscreen}
        svgContent={svgContent}
      />
    </>
  );
}
