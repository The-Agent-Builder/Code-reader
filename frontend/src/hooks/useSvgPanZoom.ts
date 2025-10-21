import { useEffect, useRef } from 'react';

export function useSvgPanZoom(containerRef: React.RefObject<HTMLElement>, content: string | null, enabled: boolean = true) {
  const panZoomInstancesRef = useRef<Map<SVGElement, any>>(new Map());
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled || !containerRef.current || !content) return;

    const initializePanZoom = async () => {
      const svgElements = containerRef.current?.querySelectorAll('svg');
      
      if (!svgElements || svgElements.length === 0) {
        retryTimeoutRef.current = setTimeout(() => {
          void initializePanZoom();
        }, 1000);
        return;
      }

      try {
        const svgPanZoom = (await import("svg-pan-zoom")).default;

        svgElements.forEach((svgElement) => {
          if (panZoomInstancesRef.current.has(svgElement)) {
            return;
          }

          // 创建独立的容器包装器
          const wrapper = document.createElement('div');
          wrapper.className = 'svg-zoom-wrapper';

          // 包装 SVG 元素
          svgElement.parentNode?.insertBefore(wrapper, svgElement);
          wrapper.appendChild(svgElement);

          // 设置 SVG 样式
          svgElement.style.maxWidth = "none";
          svgElement.style.width = "100%";
          svgElement.style.height = "100%";
          svgElement.style.display = "block";

          // 初始化 svg-pan-zoom
          const panZoomInstance = svgPanZoom(svgElement, {
            zoomEnabled: true,
            controlIconsEnabled: false,
            fit: false,
            center: false,
            minZoom: 0.1,
            maxZoom: 10,
            zoomScaleSensitivity: 0.3,
            dblClickZoomEnabled: true,
            mouseWheelZoomEnabled: true,
            preventMouseEventsDefault: true,
          });

          // 添加鼠标事件监听器，防止滚轮影响页面滚动
          const handleWheel = (event: WheelEvent) => {
            event.preventDefault();
            event.stopPropagation();
          };

          const handleMouseEnter = () => {
            document.body.style.overflow = 'hidden';
          };

          const handleMouseLeave = () => {
            document.body.style.overflow = 'auto';
          };

          wrapper.addEventListener('wheel', handleWheel, { passive: false });
          wrapper.addEventListener('mouseenter', handleMouseEnter);
          wrapper.addEventListener('mouseleave', handleMouseLeave);

          (wrapper as any)._svgPanZoomEvents = {
            handleWheel,
            handleMouseEnter,
            handleMouseLeave
          };

          panZoomInstancesRef.current.set(svgElement, panZoomInstance);

          // 添加全屏按钮
          const fullscreenBtn = document.createElement('button');
          fullscreenBtn.className = 'fullscreen-btn';
          fullscreenBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
            </svg>
          `;
          fullscreenBtn.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            z-index: 1001;
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid #d1d5db;
            border-radius: 4px;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            opacity: 0.7;
          `;
          
          
          // 添加悬停效果
          fullscreenBtn.addEventListener('mouseenter', () => {
            fullscreenBtn.style.opacity = '1';
            fullscreenBtn.style.backgroundColor = 'rgba(255, 255, 255, 1)';
          });
          
          fullscreenBtn.addEventListener('mouseleave', () => {
            fullscreenBtn.style.opacity = '0.7';
            fullscreenBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
          });

          // 添加全屏功能
          fullscreenBtn.addEventListener('click', () => {
            // 创建全屏模态框
            const modal = document.createElement('div');
            modal.style.cssText = `
              position: fixed;
              top: 0;
              left: 0;
              width: 100vw;
              height: 100vh;
              background-color: rgba(0, 0, 0, 0.8);
              z-index: 9999;
              display: flex;
              align-items: center;
              justify-content: center;
              cursor: pointer;
              user-select: none;
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
            `;
            
            // 创建白色区域容器（占据全屏的80%）
            const whiteContainer = document.createElement('div');
            whiteContainer.style.cssText = `
              width: 80vw;
              height: 80vh;
              background: white;
              border-radius: 12px;
              box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
              position: relative;
              overflow: hidden;
              display: flex;
              align-items: center;
              justify-content: center;
              user-select: none;
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
            `;
            
            const modalContent = document.createElement('div');
            modalContent.style.cssText = `
              max-width: 90vw;
              max-height: 90vh;
              background: transparent;
              border-radius: 8px;
              padding: 0;
              position: relative;
              cursor: default;
              display: flex;
              align-items: center;
              justify-content: center;
              user-select: none;
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
            `;
            
            // 获取 SVG 的 HTML 字符串并修复 CSS 问题
            let svgHtml = svgElement.outerHTML;
            
            // 修复无效的 CSS 值
            svgHtml = svgHtml.replace(/max-width:\s*no\b/g, 'max-width: none');
            svgHtml = svgHtml.replace(/max-width:\s*no\s*;/g, 'max-width: none;');
            svgHtml = svgHtml.replace(/max-width:\s*no\s*"/g, 'max-width: none"');
            svgHtml = svgHtml.replace(/max-width:\s*no\s*'/g, "max-width: none'");
            
            // 确保 SVG 有正确的尺寸
            svgHtml = svgHtml.replace(/width="100%"/g, 'width="100%" height="100%"');
            svgHtml = svgHtml.replace(/style="[^"]*overflow:\s*hidden[^"]*"/g, 'style="overflow: visible"');
            
            // 移除无效的 height="auto" 属性
            svgHtml = svgHtml.replace(/height="auto"/g, 'height="100%"');
            
            
            // 创建可拖动的SVG容器
            const contentDiv = document.createElement('div');
            contentDiv.style.cssText = `
              width: 100%;
              height: 100%;
              display: flex;
              align-items: center;
              justify-content: center;
              overflow: visible;
              cursor: grab;
              position: relative;
              transform: translateZ(0);
              will-change: transform;
              contain: layout style paint;
              user-select: none;
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
            `;
            contentDiv.innerHTML = svgHtml;
            
            // 确保 SVG 元素有正确的样式
            const svgInModal = contentDiv.querySelector('svg');
            if (svgInModal) {
              svgInModal.style.cssText = `
                max-width: none !important;
                width: 100% !important;
                height: 100% !important;
                display: block !important;
                overflow: visible !important;
                pointer-events: auto !important;
                position: relative !important;
                z-index: 10 !important;
                transform: translateZ(0) !important;
                will-change: transform !important;
                backface-visibility: hidden !important;
                -webkit-backface-visibility: hidden !important;
                user-select: none !important;
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
              `;
              
              // 移除自定义滚轮事件处理，使用 svg-pan-zoom 的内置功能
              
              // 为全屏模式添加 svg-pan-zoom 功能
              setTimeout(async () => {
                try {
                  const svgPanZoom = (await import("svg-pan-zoom")).default;
                  const fullscreenPanZoom = svgPanZoom(svgInModal, {
                    zoomEnabled: true,
                    panEnabled: true,
                    controlIconsEnabled: false,
                    fit: false,
                    center: false,
                    minZoom: 0.1,
                    maxZoom: 10,
                    zoomScaleSensitivity: 0.1, // 降低缩放敏感度，减少卡顿
                    dblClickZoomEnabled: true,
                    mouseWheelZoomEnabled: true,
                    preventMouseEventsDefault: false,
                    // 优化性能设置
                    beforeZoom: function(prevScale, newScale) {
                      // 添加防抖，减少频繁更新
                      return true;
                    },
                    onZoom: function(newScale) {
                      // 使用 requestAnimationFrame 优化渲染
                      requestAnimationFrame(() => {
                        // 强制重绘
                        svgInModal.style.transform = '';
                      });
                    },
                    onPan: function(newPan) {
                      // 使用 requestAnimationFrame 优化拖拽
                      requestAnimationFrame(() => {
                        // 强制重绘
                        svgInModal.style.transform = '';
                      });
                    }
                  });
                  
                  
                  // 手动移除 svg-pan-zoom 创建的控制元素（更保守的方法）
                  const removeControls = () => {
                    const svgContainer = svgInModal.parentElement;
                    if (svgContainer) {
                      // 只移除明确是控制元素的，不要移除 SVG 本身
                      const controls = svgContainer.querySelectorAll('.svg-pan-zoom-control, .svg-pan-zoom-controls');
                      controls.forEach(control => {
                        if (control.parentNode && control !== svgInModal) {
                          control.parentNode.removeChild(control);
                        }
                      });
                      
                    }
                  };
                  
                  // 延迟执行，确保 SVG 已经渲染完成
                  setTimeout(removeControls, 300);
                  
                  // 存储实例以便清理
                  (modal as any)._panZoomInstance = fullscreenPanZoom;
                  
                  // 添加自定义简洁控制按钮（暂时隐藏）
                  // const customControls = document.createElement('div');
                  // customControls.style.cssText = `
                  //   position: absolute;
                  //   top: 10px;
                  //   right: 10px;
                  //   z-index: 1000;
                  //   display: none;
                  //   flex-direction: column;
                  //   gap: 5px;
                  // `;
                  
                  // // 放大按钮
                  // const zoomInBtn = document.createElement('button');
                  // zoomInBtn.innerHTML = '+';
                  // zoomInBtn.style.cssText = `
                  //   width: 30px;
                  //   height: 30px;
                  //   background: rgba(255, 255, 255, 0.9);
                  //   border: 1px solid #ccc;
                  //   border-radius: 4px;
                  //   cursor: pointer;
                  //   font-size: 16px;
                  //   font-weight: bold;
                  //   display: flex;
                  //   align-items: center;
                  //   justify-content: center;
                  //   transform: translateZ(0);
                  //   will-change: transform;
                  // `;
                  // zoomInBtn.addEventListener('click', (e) => {
                  //   e.preventDefault();
                  //   e.stopPropagation();
                  //   requestAnimationFrame(() => {
                  //     fullscreenPanZoom.zoomIn();
                  //   });
                  // });
                  
                  // // 重置按钮
                  // const resetBtn = document.createElement('button');
                  // resetBtn.innerHTML = 'RESET';
                  // resetBtn.style.cssText = `
                  //   width: 30px;
                  //   height: 30px;
                  //   background: rgba(255, 255, 255, 0.9);
                  //   border: 1px solid #ccc;
                  //   border-radius: 4px;
                  //   cursor: pointer;
                  //   font-size: 8px;
                  //   font-weight: bold;
                  //   display: flex;
                  //   align-items: center;
                  //   justify-content: center;
                  // `;
                  // resetBtn.addEventListener('click', (e) => {
                  //   e.preventDefault();
                  //   e.stopPropagation();
                  //   requestAnimationFrame(() => {
                  //     fullscreenPanZoom.resetZoom();
                  //   });
                  // });
                  
                  // // 缩小按钮
                  // const zoomOutBtn = document.createElement('button');
                  // zoomOutBtn.innerHTML = '-';
                  // zoomOutBtn.style.cssText = `
                  //   width: 30px;
                  //   height: 30px;
                  //   background: rgba(255, 255, 255, 0.9);
                  //   border: 1px solid #ccc;
                  //   border-radius: 4px;
                  //   cursor: pointer;
                  //   font-size: 16px;
                  //   font-weight: bold;
                  //   display: flex;
                  //   align-items: center;
                  //   justify-content: center;
                  // `;
                  // zoomOutBtn.addEventListener('click', (e) => {
                  //   e.preventDefault();
                  //   e.stopPropagation();
                  //   requestAnimationFrame(() => {
                  //     fullscreenPanZoom.zoomOut();
                  //   });
                  // });
                  
                  // customControls.appendChild(zoomInBtn);
                  // customControls.appendChild(resetBtn);
                  // customControls.appendChild(zoomOutBtn);
                  // contentDiv.appendChild(customControls);
                } catch (error) {
                  // Error handling for fullscreen svg-pan-zoom initialization
                }
              }, 100);
            }
            
            // 组装容器结构：modal -> modalContent -> whiteContainer -> contentDiv
            whiteContainer.appendChild(contentDiv);
            modalContent.appendChild(whiteContainer);
            modal.appendChild(modalContent);
            document.body.appendChild(modal);
            
            // 关闭模态框的函数
            const closeModal = () => {
              // 清理 svg-pan-zoom 实例
              if ((modal as any)._panZoomInstance) {
                try {
                  (modal as any)._panZoomInstance.destroy();
                } catch (error) {
                  // Error handling for destroying fullscreen pan-zoom instance
                }
              }
              
              document.body.removeChild(modal);
            };
            
            // 点击模态框外部关闭
            modal.addEventListener('click', (e) => {
              if (e.target === modal) {
                closeModal();
              }
            });
            
            // ESC 键关闭
            const handleEsc = (e: KeyboardEvent) => {
              if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleEsc);
              }
            };
            document.addEventListener('keydown', handleEsc);
          });

          wrapper.appendChild(fullscreenBtn);
          
          // 添加悬停效果到包装器
          wrapper.addEventListener('mouseenter', () => {
            fullscreenBtn.style.opacity = '1';
          });
          
          wrapper.addEventListener('mouseleave', () => {
            fullscreenBtn.style.opacity = '0';
          });
        });

      } catch (error) {
        // Error handling for loading svg-pan-zoom
      }
    };

    const timer = setTimeout(() => {
      void initializePanZoom();
    }, 1000);

    return () => {
      clearTimeout(timer);
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      
      panZoomInstancesRef.current.forEach((instance, svgElement) => {
        try {
          instance.destroy();
          
          const wrapper = svgElement.parentElement;
          if (wrapper && (wrapper as any)._svgPanZoomEvents) {
            const events = (wrapper as any)._svgPanZoomEvents;
            wrapper.removeEventListener('wheel', events.handleWheel);
            wrapper.removeEventListener('mouseenter', events.handleMouseEnter);
            wrapper.removeEventListener('mouseleave', events.handleMouseLeave);
            delete (wrapper as any)._svgPanZoomEvents;
          }
        } catch (error) {
          // Error handling for destroying pan-zoom instance
        }
      });
      panZoomInstancesRef.current.clear();
      
      document.body.style.overflow = 'auto';
    };
  }, [enabled, containerRef, content]);
}