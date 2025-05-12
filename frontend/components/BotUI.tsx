'use client';

import { useState, useRef, useEffect } from 'react';
import Draggable from 'react-draggable';
import { FiMessageSquare, FiMaximize, FiMinimize } from 'react-icons/fi';

export default function BotUI() {
  const [open, setOpen] = useState(false);
  const [size, setSize] = useState({ width: 400, height: 300 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [panelPosition, setPanelPosition] = useState({ x: 0, y: 0 });
  const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  

  const panelRef = useRef<HTMLDivElement>(null);
  const botButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleResize = () => {
      if (!panelRef.current) return;
      const { innerWidth, innerHeight } = window;
      setSize((prev) => ({
        width: Math.min(prev.width, innerWidth),
        height: Math.min(prev.height, innerHeight),
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const togglePanel = () => {
    if (open) {
      setOpen(false);
      setIsFullscreen(false);
    } else {
      const rect = botButtonRef.current?.getBoundingClientRect();
      if (rect) {
        const panelW = size.width;
        const panelH = size.height;

        const x = Math.max(0, rect.left - panelW + 50);
        const y = Math.max(0, rect.top - panelH - 20);
        setPanelPosition({ x, y });
      }
      setOpen(true);
    }
  };

  const toggleFullscreen = () => {
    const padding = 20;
    const { innerWidth, innerHeight } = window;
    if (isFullscreen) {
      setSize({ width: 400, height: 300 });
    } else {
      setSize({
        width: innerWidth - padding * 2,
        height: innerHeight - padding * 2,
      });
      setPanelPosition({ x: padding, y: padding });
    }
    setIsFullscreen(!isFullscreen);
  };

  const onDrag = (e: any, data: any) => {
    const maxX = window.innerWidth - size.width;
    const maxY = window.innerHeight - size.height;
    const x = Math.min(Math.max(0, data.x), maxX);
    const y = Math.min(Math.max(0, data.y), maxY);
    setPanelPosition({ x, y });
  };

  const handleSendMessage = async () => {
    if (messageInput.trim() === '') return;

    setMessages((prevMessages) => [
      ...prevMessages,
      { text: messageInput, isUser: true },
    ]);
    setMessageInput('');
    setIsThinking(true);

    // Simulate AI response
     try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: messageInput,
          // policyKeys: policyKeys.length > 0 ? policyKeys : undefined,
        }),
      });
      const data = await res.json();
      setMessages((prevMessages) => [
      ...prevMessages,
      { text: data, isUser: false },
      ]);
    } catch {
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: '⚠️ Error getting response.', isUser: false },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessageInput(e.target.value);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isThinking) {
      handleSendMessage();
    }
  };

  return (
    <main className="min-h-screen bg-white text-black relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle,black_1px,transparent_1px)] bg-[size:20px_20px] opacity-10 pointer-events-none" />

      <button
        ref={botButtonRef}
        onClick={togglePanel}
        className="fixed bottom-6 right-6 z-50 bg-black text-white p-3 rounded-full shadow-md hover:scale-105 transition-transform"
      >
        <FiMessageSquare size={24} />
      </button>

      {open && (
        <Draggable
          handle=".handle"
          position={panelPosition}
          onDrag={onDrag}
          nodeRef={panelRef  as React.RefObject<HTMLElement>}
        >
          <div
            ref={panelRef}
            style={{
              width: size.width,
              height: size.height,
              maxWidth: '100vw',
              maxHeight: '100vh',
            }}
            className="fixed z-40 bg-white border border-black rounded-md shadow-lg overflow-hidden flex flex-col"
          >
            <div className="handle cursor-move bg-black text-white text-xs font-mono p-1">
              ⌘ Drag Me
            </div>

            <div className="absolute inset-0 bg-[linear-gradient(#000_1px,transparent_1px),linear-gradient(90deg,#000_1px,transparent_1px)] bg-[size:40px_40px] opacity-10 pointer-events-none" />

            <div className="flex flex-col w-full h-full">
              <div className="handle bg-black text-white px-4 py-2 text-sm flex justify-between items-center">
                <span className="font-mono">O𝑰 Assistant</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setOpen(false)}
                    className="bg-black text-white p-2 rounded-full"
                  >
                    ×
                  </button>
                  <button
                    onClick={toggleFullscreen}
                    className="bg-black text-white p-2 rounded-full"
                  >
                    {isFullscreen ? <FiMinimize size={20} /> : <FiMaximize size={20} />}
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-4 pt-3 pb-24 space-y-2">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`text-xs font-mono px-4 py-2 rounded-xl max-w-[80%] ${
                        message.isUser ? 'bg-black text-white' : 'bg-gray-200 text-black'
                      }`}
                    >
                      {message.text}
                    </div>
                  </div>
                ))}

                {isThinking && (
                  <div className="flex justify-start">
                    <div className="text-xs font-mono px-4 py-2 rounded-xl bg-gray-100 text-gray-500 animate-pulse">
                      Thinking...
                    </div>
                  </div>
                )}
              </div>

              <div className="absolute bottom-0 left-0 w-full bg-white border-t border-gray-200 px-4 py-3 flex justify-center items-center gap-2">
                <input
                  type="text"
                  placeholder="Type your message..."
                  value={messageInput}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyPress}
                  disabled={isThinking}
                  className="w-3/4 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isThinking}
                  className={`text-sm px-4 py-2 rounded-md ${
                    isThinking
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : 'bg-black text-white hover:bg-gray-800'
                  }`}
                >
                  Send
                </button>
              </div>
            </div>

            {!isFullscreen && (
              <div
                onMouseDown={(e) => {
                  e.preventDefault();
                  const startX = e.clientX;
                  const startY = e.clientY;
                  const startWidth = size.width;
                  const startHeight = size.height;

                  const doResize = (moveEvent: MouseEvent) => {
                    const newWidth = Math.min(
                      window.innerWidth,
                      Math.max(300, startWidth + (moveEvent.clientX - startX))
                    );
                    const newHeight = Math.min(
                      window.innerHeight,
                      Math.max(200, startHeight + (moveEvent.clientY - startY))
                    );
                    setSize({ width: newWidth, height: newHeight });
                  };

                  const stopResize = () => {
                    document.removeEventListener('mousemove', doResize);
                    document.removeEventListener('mouseup', stopResize);
                  };

                  document.addEventListener('mousemove', doResize);
                  document.addEventListener('mouseup', stopResize);
                }}
                className="absolute right-0 bottom-0 w-4 h-4 bg-black cursor-se-resize z-50"
              />
            )}
          </div>
        </Draggable>
      )}
    </main>
  );
}
